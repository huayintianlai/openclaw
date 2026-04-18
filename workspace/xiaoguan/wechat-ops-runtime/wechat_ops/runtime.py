from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import uuid4

from .config import WeChatOpsConfig


UTC = timezone.utc
KNOWN_WATCHERS = ("unread", "chat_visible", "moments")
WATCHER_PHASES = {
    "unread": "unread_snapshot",
    "chat_visible": "chat_visible_snapshot",
    "moments": "moments_snapshot",
}
WATCHER_CHANGE_JOB_TYPES = {
    "unread": "unread.snapshot.changed",
    "chat_visible": "chat.visible.delta",
    "moments": "moments.cards.unseen",
}


def now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def parse_iso(value: str | None) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def parse_permissions_output(text: str) -> Dict[str, Any]:
    source = ""
    screen = False
    accessibility = False
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("Source:"):
            source = line.split(":", 1)[1].strip()
        elif line.startswith("Screen Recording"):
            screen = "Granted" in line
        elif line.startswith("Accessibility"):
            accessibility = "Granted" in line
    return {
        "source": source,
        "screen_recording": screen,
        "accessibility": accessibility,
        "healthy": screen and accessibility,
    }


def first_window_target(payload: Dict[str, Any]) -> Optional[Tuple[str, int]]:
    windows = payload.get("data", {}).get("windows", [])
    candidates: List[Dict[str, Any]] = []

    def area(bounds: Any) -> int:
        try:
            return int(bounds[1][0] or 0) * int(bounds[1][1] or 0)
        except Exception:
            return 0

    for window in windows:
        if not isinstance(window, dict):
            continue
        window_id = int(window.get("window_id") or window.get("windowID") or 0)
        if window.get("isMinimized"):
            continue
        if not window.get("isOnScreen", True):
            continue
        if window_id <= 0:
            continue
        bounds = window.get("bounds", [[0, 0], [0, 0]])
        try:
            win_x = int(bounds[0][0] or 0)
            win_y = int(bounds[0][1] or 0)
            win_w = int(bounds[1][0] or 0)
            win_h = int(bounds[1][1] or 0)
        except Exception:
            win_x = win_y = win_w = win_h = 0
        # 排除菜单栏/overlay：高度小于 100px，或 y=0 且高度小于 50px
        if win_h < 100:
            continue
        # 排除宽高比异常的窗口（如超宽菜单栏，宽度>高度*8）
        if win_h > 0 and win_w > win_h * 8:
            continue
        window["_resolved_window_id"] = window_id
        window["_area"] = area(bounds)
        candidates.append(window)
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (
            0 if item.get("title") else 1,
            -item.get("_area", 0),
            0 if item.get("isMainWindow") else 1,
            item.get("index", 99),
        )
    )
    best = candidates[0]
    return best.get("title", ""), int(best["_resolved_window_id"])


def bounds_for_window(target: Dict[str, Any]) -> Optional[Tuple[int, int, int, int]]:
    target_id = int(target.get("window_id") or 0)
    for window in target.get("windows", []):
        try:
            window_id = int(window.get("window_id") or window.get("windowID") or 0)
        except Exception:
            window_id = 0
        if window_id != target_id:
            continue
        bounds = window.get("bounds", [[0, 0], [0, 0]])
        try:
            win_x = int(bounds[0][0] or 0)
            win_y = int(bounds[0][1] or 0)
            win_w = int(bounds[1][0] or 0)
            win_h = int(bounds[1][1] or 0)
        except Exception:
            return None
        if win_w <= 0 or win_h <= 0:
            return None
        return win_x, win_y, win_w, win_h
    return None


def extract_ai_section(text: str) -> str:
    match = re.search(
        r"(?:🤖\s*)?AI Analysis\s*\n(?P<body>.*?)(?:\n(?:🔍\s*)?Element Summary|\Z)",
        text,
        re.DOTALL,
    )
    if not match:
        return ""
    body = match.group("body").strip()
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    return lines[0] if lines else ""


def extract_json_fragment(text: str) -> Optional[Any]:
    decoder = json.JSONDecoder()
    for index, char in enumerate(text):
        if char not in "[{":
            continue
        try:
            value, _ = decoder.raw_decode(text[index:])
            return value
        except json.JSONDecodeError:
            continue
    return None


def canonicalize_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def parse_hid_idle_time_seconds(text: str) -> Optional[float]:
    match = re.search(r'"HIDIdleTime"\s*=\s*(\d+)', text)
    if not match:
        return None
    nanos = int(match.group(1))
    return nanos / 1_000_000_000


def normalize_contact_name(value: str) -> str:
    value = (value or "").strip()
    value = re.sub(r"\s+", "", value)
    value = value.replace("（", "(").replace("）", ")")
    return value.casefold()


def contacts_match(expected: str, actual: str) -> bool:
    expected_norm = normalize_contact_name(expected)
    actual_norm = normalize_contact_name(actual)
    if not expected_norm or not actual_norm:
        return False
    if actual_norm in {"__unknown__", "__none__"}:
        return False
    # 精确匹配
    if expected_norm == actual_norm:
        return True
    if not likely_group_contact_name(expected) and likely_group_contact_name(actual):
        return False
    # 非群聊场景坚持严格匹配，避免把个人联系人误匹配到群聊或相似名称。
    if not likely_group_contact_name(expected) and not likely_group_contact_name(actual):
        return False
    # 部分匹配：群名可能被 OCR 截断或带省略号
    # 去掉省略号后取前16字符做前缀匹配
    actual_clean = actual_norm.rstrip(".").rstrip("⋯").rstrip("…")
    expected_clean = expected_norm.rstrip(".").rstrip("⋯").rstrip("…")
    prefix_len = min(len(expected_clean), len(actual_clean), 16)
    if prefix_len >= 4 and expected_clean[:prefix_len] == actual_clean[:prefix_len]:
        return True
    # actual 包含 expected 核心（去掉括号内成员数）
    expected_core = re.sub(r"[（(]\d+[）)]", "", expected_clean).strip()
    actual_core = re.sub(r"[（(]\d+[）)]", "", actual_clean).strip()
    if expected_core and actual_core and (expected_core in actual_core or actual_core in expected_core):
        return True
    return False


def ensure_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [json_safe(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def message_signature(text: str) -> str:
    return normalize_contact_name(text or "")


def split_message_chunks(text: str, max_chars: int) -> List[str]:
    url_pattern = re.compile(r"https?://\S+")
    chunks: List[str] = []
    last_index = 0
    for match in url_pattern.finditer(text):
        prefix = text[last_index : match.start()]
        if prefix:
            chunks.extend(_split_plaintext_chunks(prefix, max_chars))
        chunks.append(match.group(0))
        last_index = match.end()
    tail = text[last_index:]
    if tail:
        chunks.extend(_split_plaintext_chunks(tail, max_chars))
    return [chunk for chunk in chunks if chunk]


def _split_plaintext_chunks(text: str, max_chars: int) -> List[str]:
    parts: List[str] = []
    for paragraph in text.splitlines(keepends=True):
        working = paragraph
        while len(working) > max_chars:
            window = working[:max_chars]
            split_at = max(
                window.rfind(sep) for sep in ("。", "！", "？", "，", ",", "；", ";", " ")
            )
            if split_at <= 0:
                split_at = max_chars
            else:
                split_at += 1
            parts.append(working[:split_at])
            working = working[split_at:]
        if working:
            parts.append(working)
    return parts


def parse_time_like(text: str) -> bool:
    return bool(re.fullmatch(r"[0-2]?\d[:：][0-5]\d", text.strip()))


def parse_chat_time_like(text: str) -> bool:
    cleaned = normalize_sidebar_time_text(text).strip("•·.。")
    if re.fullmatch(r"昨.\s*\d{1,2}:\d{2}", cleaned):
        return True
    return parse_time_like(cleaned) or parse_sidebar_time_like(cleaned)


def normalize_sidebar_time_text(text: str) -> str:
    cleaned = text.strip()
    cleaned = cleaned.replace("：", ":")
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"昨天\s*(\d{1,2}:\d{2})", r"昨天 \1", cleaned)
    return cleaned


def split_sidebar_text_and_time(text: str) -> Tuple[str, Optional[str]]:
    cleaned = normalize_sidebar_time_text(text)
    patterns = (
        r"^(.*?)[•·.\s]*(昨天 ?\d{1,2}:\d{2})$",
        r"^(.*?)[•·.\s]*(\d{2}/\d{2})$",
        r"^(.*?)[•·.\s]*(星期[一二三四五六日天])$",
        r"^(.*?)[•·.\s]*(今天)$",
        r"^(.*?)[•·.\s]*(刚刚)$",
    )
    for pattern in patterns:
        match = re.match(pattern, cleaned)
        if not match:
            continue
        left = match.group(1).strip().strip("•·.。")
        time_text = match.group(2).strip()
        return left, time_text
    return cleaned, None


def parse_sidebar_time_like(text: str) -> bool:
    cleaned = normalize_sidebar_time_text(text).strip("•·.。")
    if parse_time_like(cleaned):
        return True
    if re.fullmatch(r"\d{2}/\d{2}", cleaned):
        return True
    if re.fullmatch(r"昨天 ?\d{1,2}:\d{2}", cleaned):
        return True
    return cleaned in {
        "昨天",
        "今天",
        "刚刚",
        "星期一",
        "星期二",
        "星期三",
        "星期四",
        "星期五",
        "星期六",
        "星期日",
        "星期天",
    }


def likely_contact_text(text: str) -> bool:
    cleaned = text.strip()
    if not cleaned:
        return False
    if cleaned in {"搜索", "微信"}:
        return False
    if parse_time_like(cleaned):
        return False
    if not re.search(r"[A-Za-z0-9\u4e00-\u9fff]", cleaned):
        return False
    return len(cleaned) > 1


def line_text(line: Dict[str, Any]) -> str:
    return ensure_text(line.get("text")).strip()


def line_box(line: Dict[str, Any]) -> List[float]:
    box = line.get("boundingBox") or [0.0, 0.0, 0.0, 0.0]
    return [float(v) for v in box]


def image_is_blank(path: Path) -> bool:
    try:
        from PIL import Image
    except Exception:
        return False

    if not path.exists():
        return True

    img = Image.open(path)
    pixels = list(img.resize((20, 20)).getdata())
    vals = [sum(pixel[:3]) / 3 for pixel in pixels]
    return max(vals) <= 3


def crop_image(path: Path, output: Path, *, x0: float, y0: float, x1: float, y1: float) -> Path:
    from PIL import Image

    img = Image.open(path)
    width, height = img.size
    cropped = img.crop(
        (
            int(width * x0),
            int(height * y0),
            int(width * x1),
            int(height * y1),
        )
    )
    cropped.save(output)
    return output


def crop_image(path: Path, output: Path, *, x0: float, y0: float, x1: float, y1: float) -> Path:
    from PIL import Image

    img = Image.open(path)
    width, height = img.size
    left = int(width * x0)
    top = int(height * y0)
    right = int(width * x1)
    bottom = int(height * y1)
    cropped = img.crop((left, top, right, bottom))
    cropped.save(output)
    return output


def parse_unread_count(text: str) -> Optional[int]:
    cleaned = text.strip()
    if "999+" in cleaned:
        return 999
    match = re.search(r"(\d+)\+?", cleaned)
    if not match:
        return None
    return int(match.group(1))


def sidebar_title_from_row_info(row_info: Dict[str, Any]) -> Optional[str]:
    for text in row_info["texts"]:
        cleaned = normalize_sidebar_time_text(text)
        cleaned, inline_time = split_sidebar_text_and_time(cleaned)
        if not cleaned or cleaned in {"Q 搜索", "搜索"}:
            continue
        if inline_time or parse_sidebar_time_like(cleaned):
            continue
        if re.fullmatch(r"\d+\+?", cleaned):
            continue
        if cleaned.startswith(("［", "[", "（", "(")):
            continue
        if likely_contact_text(cleaned):
            return cleaned
    return None


def sidebar_preview_from_row_info(row_info: Dict[str, Any]) -> str:
    if row_info.get("time_text"):
        return ""
    text = str(row_info.get("content_text") or "").strip()
    if not text or text in {"Q 搜索", "搜索"}:
        return ""
    return text


def sidebar_row_infos_from_ocr_payload(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw_lines = payload.get("lines") or []
    lines = [
        line
        for line in raw_lines
        if isinstance(line, dict)
        and line_text(line)
        and line_box(line)[0] < 0.95
        and line_box(line)[1] < 0.97
        and line_box(line)[1] > 0.04
    ]
    lines.sort(key=lambda line: (-line_box(line)[1], line_box(line)[0]))

    rows: List[List[Dict[str, Any]]] = []
    row_ys: List[float] = []
    for line in lines:
        y = line_box(line)[1]
        if rows and abs(row_ys[-1] - y) <= 0.015:
            rows[-1].append(line)
        else:
            rows.append([line])
            row_ys.append(y)

    row_infos: List[Dict[str, Any]] = []
    for index, row in enumerate(rows):
        badge_count = None
        time_text = None
        content_parts: List[str] = []
        xs: List[float] = []
        for line in sorted(row, key=lambda item: line_box(item)[0]):
            text = line_text(line)
            x, _, _, _ = line_box(line)
            xs.append(x)
            cleaned = normalize_sidebar_time_text(text)
            if x < 0.20 and re.fullmatch(r"\d+\+?", cleaned):
                badge_count = badge_count or parse_unread_count(cleaned)
                continue
            if re.fullmatch(r"\d+\+?", cleaned):
                badge_count = badge_count or parse_unread_count(cleaned)
                continue
            if parse_sidebar_time_like(cleaned) and x >= 0.60:
                time_text = cleaned
                continue
            left, inline_time = split_sidebar_text_and_time(cleaned)
            if inline_time:
                if left:
                    content_parts.append(left)
                time_text = inline_time
                continue
            content_parts.append(cleaned)
        content_text = " ".join(part for part in content_parts if part).strip()
        row_infos.append(
            {
                "texts": [line_text(line) for line in row],
                "badge_count": badge_count,
                "time_text": time_text,
                "content_text": content_text,
                "y": row_ys[index],
                "x_min": min(xs) if xs else 0.0,
                "line_count": len(row),
            }
        )
    return row_infos


def sidebar_conversation_candidates(row_infos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    conversations: List[Dict[str, Any]] = []
    for index, current in enumerate(row_infos):
        title = sidebar_title_from_row_info(current) or current["content_text"]
        time_text = current["time_text"]
        next_preview = (
            sidebar_preview_from_row_info(row_infos[index + 1])
            if index + 1 < len(row_infos)
            else ""
        )
        next_gap = (
            current["y"] - row_infos[index + 1]["y"]
            if index + 1 < len(row_infos)
            else 999.0
        )
        if (
            not title
            or title in {"Q 搜索", "搜索"}
            or title.startswith(("［", "[", "（", "("))
            or not likely_contact_text(title)
            or not (
                time_text
                or current["badge_count"] is not None
                or (next_preview and 0 < next_gap <= 0.04)
            )
        ):
            continue

        unread_count = current["badge_count"]
        preview = ""
        for candidate in row_infos[index + 1 : min(index + 4, len(row_infos))]:
            if current["y"] - candidate["y"] > 0.09:
                break
            candidate_title = sidebar_title_from_row_info(candidate)
            if candidate.get("time_text") and candidate_title:
                break
            if unread_count is None and candidate["badge_count"] is not None:
                unread_count = candidate["badge_count"]
            if not preview:
                preview = sidebar_preview_from_row_info(candidate)
        conversations.append(
            {
                "name": title,
                "unread_count": unread_count,
                "preview": preview,
                "time": time_text,
                "y": current["y"],
                "row_index": index,
            }
        )
    return conversations


def detect_badge_components(image_path: Path) -> List[Dict[str, Any]]:
    try:
        from PIL import Image
    except Exception:
        return []

    if not image_path.exists():
        return []

    img = Image.open(image_path).convert("RGB")
    width, height = img.size
    red_mask = [[False] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            r, g, b = img.getpixel((x, y))
            red_mask[y][x] = (
                r > 175 and g < 150 and b < 150 and (r - g) > 35 and (r - b) > 35
            )

    components: List[Dict[str, Any]] = []
    seen = [[False] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            if seen[y][x] or not red_mask[y][x]:
                continue
            stack = [(x, y)]
            seen[y][x] = True
            points: List[Tuple[int, int]] = []
            while stack:
                cx, cy = stack.pop()
                points.append((cx, cy))
                for nx, ny in (
                    (cx + 1, cy),
                    (cx - 1, cy),
                    (cx, cy + 1),
                    (cx, cy - 1),
                ):
                    if (
                        0 <= nx < width
                        and 0 <= ny < height
                        and red_mask[ny][nx]
                        and not seen[ny][nx]
                    ):
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            if len(points) < 18:
                continue
            xs = [point[0] for point in points]
            ys = [point[1] for point in points]
            left = min(xs)
            top = min(ys)
            right = max(xs)
            bottom = max(ys)
            box_width = right - left + 1
            box_height = bottom - top + 1
            area = box_width * box_height
            aspect = box_width / max(box_height, 1)
            fill_ratio = len(points) / max(area, 1)
            center_x = (left + right) / 2 / width
            center_y = 1.0 - ((top + bottom) / 2 / height)
            if not (7 <= box_width <= 32 and 7 <= box_height <= 24):
                continue
            if not (0.55 <= aspect <= 2.4):
                continue
            if fill_ratio < 0.22:
                continue
            components.append(
                {
                    "left": left,
                    "top": top,
                    "right": right,
                    "bottom": bottom,
                    "center_x": center_x,
                    "center_y": center_y,
                    "pixel_count": len(points),
                    "box_width": box_width,
                    "box_height": box_height,
                    "fill_ratio": fill_ratio,
                }
            )
    components.sort(key=lambda item: (-item["center_y"], item["center_x"]))
    return components


def detect_sidebar_badges(image_path: Path) -> List[Dict[str, Any]]:
    return detect_badge_components(image_path)


def classify_sidebar_badges(
    badges: List[Dict[str, Any]],
    *,
    image_width: Optional[int] = None,
) -> Dict[str, Any]:
    return classify_nav_and_session_badges(badges)


def detect_nav_chat_badge(badges: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    candidates = [
        badge
        for badge in badges
        if 0.55 <= badge["center_x"] <= 0.95
        and 0.74 <= badge["center_y"] <= 0.94
    ]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda item: (
            abs(item["center_y"] - 0.865),
            abs(item["center_x"] - 0.80),
        ),
    )


def detect_conversation_badges(badges: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates = [
        badge
        for badge in badges
        if 0.10 <= badge["center_x"] <= 0.34
    ]
    candidates.sort(key=lambda item: (-item["center_y"], item["center_x"]))
    return candidates


def classify_nav_and_session_badges(
    badges: List[Dict[str, Any]],
    *,
    image_width: Optional[int] = None,
) -> Dict[str, Any]:
    app_badge = detect_nav_chat_badge(badges)
    session_badges = detect_conversation_badges(badges)
    return {
        "app_badge": app_badge,
        "session_badges": session_badges,
        "image_width": image_width,
    }


def infer_badge_count_from_image(image_path: Path) -> Optional[int]:
    try:
        from PIL import Image, ImageChops, ImageDraw, ImageFont
    except Exception:
        return None

    if not image_path.exists():
        return None

    img = Image.open(image_path).convert("RGB")
    red_points: List[Tuple[int, int]] = []
    mask = Image.new("L", img.size, 0)
    for y in range(img.height):
        for x in range(img.width):
            r, g, b = img.getpixel((x, y))
            lum = (r + g + b) / 3
            is_red = r > 160 and g < 170 and b < 170 and (r - g) > 20 and (r - b) > 20
            if is_red:
                red_points.append((x, y))
            is_digit = lum > 175 and not is_red
            mask.putpixel((x, y), 255 if is_digit else 0)

    if not red_points:
        return None

    xs = [point[0] for point in red_points]
    ys = [point[1] for point in red_points]
    box = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
    mask = mask.crop(box).resize((64, 64))
    font_path = "/System/Library/Fonts/SFNS.ttf"
    if not Path(font_path).exists():
        return None

    scores: List[Tuple[str, int]] = []
    for digit in "123456789":
        best_score = 10**18
        for size in range(22, 46):
            tmpl = Image.new("L", (64, 64), 0)
            draw = ImageDraw.Draw(tmpl)
            font = ImageFont.truetype(font_path, size=size)
            bbox = draw.textbbox((0, 0), digit, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text(
                ((64 - tw) / 2 - bbox[0], (64 - th) / 2 - bbox[1]),
                digit,
                fill=255,
                font=font,
            )
            diff = ImageChops.difference(mask, tmpl)
            score = sum(diff.getdata())
            if score < best_score:
                best_score = score
        scores.append((digit, best_score))
    scores.sort(key=lambda item: item[1])
    if len(scores) < 2:
        return None
    best_digit, best_score = scores[0]
    second_score = scores[1][1]
    if best_score > 320000:
        return None
    if second_score - best_score < 5000:
        return None
    return int(best_digit)


def normalize_unread_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        if not name:
            continue
        unread_count = item.get("unread_count")
        if unread_count in ("", "__NONE__", "__UNKNOWN__"):
            unread_count = None
        if isinstance(unread_count, str) and unread_count.isdigit():
            unread_count = int(unread_count)
        if isinstance(unread_count, (int, float)):
            unread_count = int(unread_count)
        else:
            unread_count = None
        unread_badge_count = item.get("unread_badge_count", unread_count)
        if unread_badge_count in ("", "__NONE__", "__UNKNOWN__"):
            unread_badge_count = None
        if isinstance(unread_badge_count, str) and unread_badge_count.isdigit():
            unread_badge_count = int(unread_badge_count)
        if isinstance(unread_badge_count, (int, float)):
            unread_badge_count = int(unread_badge_count)
        else:
            unread_badge_count = None
        preview = str(item.get("preview_text") or item.get("preview") or "").strip()
        has_unread_badge = bool(item.get("has_unread_badge"))
        if unread_badge_count is not None:
            has_unread_badge = True
        normalized.append(
            {
                "name": name,
                "unread_count": unread_badge_count if unread_badge_count is not None else unread_count,
                "unread_badge_count": unread_badge_count,
                "has_unread_badge": has_unread_badge,
                "preview": preview,
                "preview_text": preview,
                "time": str(item.get("time") or "").strip(),
            }
        )
    normalized.sort(
        key=lambda entry: (
            0 if entry["has_unread_badge"] else 1,
            normalize_contact_name(entry["name"]),
            -(entry["unread_count"] or 0),
            entry["preview"],
        )
    )
    return normalized


def unread_signature(items: List[Dict[str, Any]]) -> str:
    return canonicalize_json(normalize_unread_items(items))


def likely_group_contact_name(name: str) -> bool:
    cleaned = normalize_contact_name(name)
    if not cleaned or cleaned == "__UNKNOWN__":
        return False
    if "群" in cleaned or "讨论组" in cleaned:
        return True
    return bool(re.search(r"[（(]\d{2,5}[)）]$", cleaned))


def classify_chat_kind(
    *,
    current_contact: str,
    visible_messages: List[Dict[str, Any]],
) -> str:
    if visible_messages:
        return "group_chat"
    if likely_group_contact_name(current_contact):
        return "group_chat"
    if current_contact and current_contact != "__UNKNOWN__":
        return "private_chat"
    return "unknown_chat"


def session_payload_signature(payload: Dict[str, Any]) -> str:
    return canonicalize_json(
        {
            "ok": payload.get("ok", False),
            "view": payload.get("view", payload.get("current_view", "unknown_view")),
            "current_contact": payload.get("current_contact", "__UNKNOWN__"),
            "last_incoming_message": payload.get("last_incoming_message", "__NONE__"),
            "chat_kind": payload.get("chat_kind", "unknown_chat"),
        }
    )


def unread_payload_signature(payload: Dict[str, Any]) -> str:
    summary = payload.get("summary", {}) if isinstance(payload.get("summary"), dict) else {}
    return canonicalize_json(
        {
            "ok": payload.get("ok", False),
            "available": payload.get("available", False),
            "app_has_unread_badge": payload.get("app_has_unread_badge", False),
            "app_unread_badge_count": payload.get("app_unread_badge_count"),
            "visible_unread_session_count": summary.get("visible_unread_session_count"),
            "signature": payload.get("signature", ""),
        }
    )


def chat_visible_payload_signature(payload: Dict[str, Any]) -> str:
    return canonicalize_json(
        {
            "ok": payload.get("ok", False),
            "available": payload.get("available", False),
            "current_contact": payload.get("current_contact", "__UNKNOWN__"),
            "chat_kind": payload.get("chat_kind", "unknown_chat"),
            "signature": payload.get("signature", ""),
        }
    )


def extract_unread_from_ocr_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    row_infos = sidebar_row_infos_from_ocr_payload(payload)
    entries = [
        {
            "name": candidate["name"],
            "unread_count": candidate["unread_count"],
            "unread_badge_count": candidate["unread_count"],
            "has_unread_badge": candidate["unread_count"] is not None,
            "preview": candidate["preview"],
            "preview_text": candidate["preview"],
            "time": candidate["time"],
        }
        for candidate in sidebar_conversation_candidates(row_infos)
        if candidate["unread_count"] is not None
    ]
    normalized = normalize_unread_items(entries)
    available = any(
        sidebar_title_from_row_info(row_info) and row_info.get("time_text")
        for row_info in row_infos
    )
    return {
        "available": available,
        "items": normalized,
        "signature": unread_signature(normalized),
    }


def group_message_speaker_candidate(line: Dict[str, Any], *, cropped: bool = False) -> bool:
    text = line_text(line)
    if not likely_contact_text(text):
        return False
    if parse_chat_time_like(text):
        return False
    if re.match(r"^\d+[：:]", text.strip()):
        return False
    if text.strip().endswith(("、", "，", "。", "！", "？", "：", ":", "；", ";")):
        return False
    if re.search(r"\d{1,2}[:：]\d{2}", text):
        return False
    if re.match(r"^(昨.|昨天|今天|星期[一二三四五六日天])", text.strip()):
        return False
    if not re.search(r"[A-Za-z\u4e00-\u9fff]", text):
        return False
    x, _, w, _ = line_box(line)
    if cropped:
        if x > 0.45:
            return False
        if w >= 0.38:
            return False
    else:
        if x < 0.42 or x > 0.72:
            return False
        if w >= 0.24:
            return False
    return len(text) <= 22


def extract_group_messages_from_ocr_payload(payload: Dict[str, Any], *, cropped: bool = False) -> List[Dict[str, Any]]:
    raw_lines = payload.get("lines") or []
    lines = [
        line
        for line in raw_lines
        if isinstance(line, dict)
        and line_text(line)
        and line_box(line)[1] <= 0.92
        and (line_box(line)[0] >= 0.42 if not cropped else True)
    ]
    lines.sort(key=lambda item: (-line_box(item)[1], line_box(item)[0]))

    messages: List[Dict[str, Any]] = []
    current_time: Optional[str] = None
    i = 0
    while i < len(lines):
        current = lines[i]
        text = line_text(current)
        if parse_chat_time_like(text):
            current_time = normalize_sidebar_time_text(text).strip("•·.。")
            i += 1
            continue
        if not group_message_speaker_candidate(current, cropped=cropped):
            i += 1
            continue

        speaker = text
        speaker_x = line_box(current)[0]
        body_parts: List[str] = []
        i += 1
        while i < len(lines):
            nxt = lines[i]
            nxt_text = line_text(nxt)
            if parse_chat_time_like(nxt_text):
                break
            if group_message_speaker_candidate(nxt, cropped=cropped):
                if body_parts and len(nxt_text.strip()) <= 4:
                    nxt_x = line_box(nxt)[0]
                    if abs(nxt_x - speaker_x) <= 0.12:
                        body_parts.append(nxt_text)
                        i += 1
                        continue
                break
            nxt_x = line_box(nxt)[0]
            if abs(nxt_x - speaker_x) > 0.16:
                i += 1
                continue
            if re.search(r"[A-Za-z\u4e00-\u9fff]", nxt_text) and len(nxt_text.strip()) > 1:
                body_parts.append(nxt_text)
            i += 1

        if body_parts:
            messages.append(
                {
                    "speaker": speaker,
                    "time": current_time,
                    "text": " ".join(body_parts).strip(),
                }
            )
    return messages


def normalize_group_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for item in messages:
        if not isinstance(item, dict):
            continue
        speaker = ensure_text(item.get("speaker")).strip()
        text = ensure_text(item.get("text")).strip()
        time_text = ensure_text(item.get("time")).strip() or None
        if not speaker or not text:
            continue
        normalized.append({"speaker": speaker, "time": time_text, "text": text})
    return normalized


def group_message_key(message: Dict[str, Any]) -> str:
    return canonicalize_json(
        {
            "speaker": ensure_text(message.get("speaker")).strip(),
            "time": ensure_text(message.get("time")).strip() or None,
            "text": ensure_text(message.get("text")).strip(),
        }
    )


def group_messages_signature(messages: List[Dict[str, Any]]) -> str:
    return canonicalize_json(normalize_group_messages(messages))


def diff_group_messages(
    previous: List[Dict[str, Any]],
    current: List[Dict[str, Any]],
) -> Dict[str, Any]:
    prev_items = normalize_group_messages(previous)
    curr_items = normalize_group_messages(current)
    prev_counts = Counter(group_message_key(item) for item in prev_items)
    curr_counts = Counter(group_message_key(item) for item in curr_items)

    running_prev = prev_counts.copy()
    added: List[Dict[str, Any]] = []
    for item in curr_items:
        key = group_message_key(item)
        if running_prev.get(key, 0) > 0:
            running_prev[key] -= 1
        else:
            added.append(item)

    running_curr = curr_counts.copy()
    removed: List[Dict[str, Any]] = []
    for item in prev_items:
        key = group_message_key(item)
        if running_curr.get(key, 0) > 0:
            running_curr[key] -= 1
        else:
            removed.append(item)

    return {
        "added_messages": added,
        "removed_messages": removed,
        "window_shift": bool(removed),
    }


def moments_card_signature(item: Dict[str, Any]) -> str:
    return canonicalize_json(
        {
            "author": ensure_text(item.get("author")).strip(),
            "summary": ensure_text(item.get("summary")).strip(),
            "has_media": bool(item.get("has_media")),
        }
    )


def normalize_moments_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        author = ensure_text(item.get("author")).strip()
        summary = ensure_text(item.get("summary")).strip()
        has_media = bool(item.get("has_media"))
        normalized.append(
            {
                "author": author,
                "summary": summary,
                "has_media": has_media,
                "card_signature": moments_card_signature(
                    {"author": author, "summary": summary, "has_media": has_media}
                ),
            }
        )
    return normalized


def moments_feed_signature(items: List[Dict[str, Any]]) -> str:
    normalized = normalize_moments_items(items)
    return canonicalize_json([item["card_signature"] for item in normalized])


def recommended_next_step_for_error(error_code: Optional[str]) -> str:
    mapping = {
        "human_active": "retry_after_idle",
        "operation_busy": "retry_after_idle",
        "target_mismatch": "run_session_current",
        "view_unknown": "run_health",
        "unknown_view": "run_health",
        "ocr_failed": "run_health",
        "timeout": "run_health",
        "window_not_found": "run_health",
        "permission_denied": "run_health",
        "new_incoming_message": "reprepare_send",
        "watcher_unhealthy": "restart_daemon",
        "daemon_stale": "restart_daemon",
        "worker_stale": "start_worker",
    }
    return mapping.get(error_code or "", "escalate_to_developer")


@dataclass
class CommandResult:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0
    error_code: Optional[str] = None


class WeChatOpsRuntime:
    def __init__(self, config: Optional[WeChatOpsConfig] = None) -> None:
        self.config = config or WeChatOpsConfig.load()
        self.config.ensure_dirs()
        self._env_cache = self._load_env_file(self.config.env_file)

    def _load_env_file(self, path: str) -> Dict[str, str]:
        result: Dict[str, str] = {}
        env_path = Path(path)
        if not env_path.exists():
            return result
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip().strip("'").strip('"')
        return result

    def _command_env(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        env = os.environ.copy()
        env.update(self._env_cache)
        if extra:
            env.update(extra)
        return env

    def _run(
        self,
        args: Iterable[str],
        *,
        timeout: Optional[int] = None,
        extra_env: Optional[Dict[str, str]] = None,
    ) -> CommandResult:
        timeout_value = timeout or self.config.timeout_seconds
        process = subprocess.Popen(
            list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=self._command_env(extra_env),
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout_value)
        except subprocess.TimeoutExpired as exc:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except Exception:
                process.kill()
            stdout, stderr = process.communicate()
            return CommandResult(
                ok=False,
                stdout=ensure_text(stdout or exc.stdout),
                stderr=ensure_text(stderr or exc.stderr),
                returncode=124,
                error_code="timeout",
            )
        returncode = process.returncode
        return CommandResult(
            ok=returncode == 0,
            stdout=ensure_text(stdout),
            stderr=ensure_text(stderr),
            returncode=returncode,
            error_code=None if returncode == 0 else "command_failed",
        )

    def _peek(self, *args: str, extra_env: Optional[Dict[str, str]] = None) -> CommandResult:
        return self._run((self.config.peekaboo_bin, *args), extra_env=extra_env)

    def _read_json_file(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return default

    def _write_json_file(self, path: Path, payload: Any) -> None:
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(json_safe(payload), ensure_ascii=False, indent=2))
        tmp_path.replace(path)

    def _top_level_health_failure(
        self,
        error_code: str,
        *,
        phase: str,
        current_view: str = "unknown_view",
        current_contact: str = "__UNKNOWN__",
        **extra: Any,
    ) -> Dict[str, Any]:
        payload = {
            "ok": False,
            "error_code": error_code,
            "phase": phase,
            "current_view": current_view,
            "current_contact": current_contact,
            "recommended_next_step": recommended_next_step_for_error(error_code),
        }
        payload.update(json_safe(extra))
        return payload

    def _watcher_failure(
        self,
        watcher: str,
        error_code: str,
        *,
        current_view: str = "unknown_view",
        current_contact: str = "__UNKNOWN__",
        available: bool = False,
        **extra: Any,
    ) -> Dict[str, Any]:
        payload = self._top_level_health_failure(
            error_code,
            phase=WATCHER_PHASES[watcher],
            current_view=current_view,
            current_contact=current_contact,
            available=available,
            **extra,
        )
        payload["watcher"] = watcher
        return payload

    def _success_payload(
        self,
        *,
        phase: str,
        current_view: str,
        current_contact: str,
        recommended_next_step: Optional[str] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        payload = {
            "ok": True,
            "phase": phase,
            "current_view": current_view,
            "current_contact": current_contact,
            "recommended_next_step": recommended_next_step,
        }
        payload.update(json_safe(extra))
        return payload

    def _stable_observation_delay_seconds(self) -> float:
        return max(self.config.observation_delay_ms, 0) / 1000

    def _stable_observation_count(self) -> int:
        return max(1, int(self.config.observation_attempts))

    def _collect_stable_payload(
        self,
        sample_fn,
        *,
        signature_fn,
        attempts: Optional[int] = None,
        delay_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        attempts = attempts or self._stable_observation_count()
        delay_seconds = (
            self._stable_observation_delay_seconds()
            if delay_seconds is None
            else max(0.0, delay_seconds)
        )
        samples: List[Dict[str, Any]] = []
        counts: Dict[str, int] = {}
        latest_index: Dict[str, int] = {}
        payloads_by_signature: Dict[str, Dict[str, Any]] = {}

        for index in range(attempts):
            payload = json_safe(sample_fn())
            samples.append(payload)
            signature = signature_fn(payload)
            counts[signature] = counts.get(signature, 0) + 1
            latest_index[signature] = index
            payloads_by_signature[signature] = payload
            if index < attempts - 1 and delay_seconds > 0:
                time.sleep(delay_seconds)

        winner_signature = max(
            counts,
            key=lambda key: (counts[key], latest_index[key]),
        )
        winner = dict(payloads_by_signature[winner_signature])
        winner["stability"] = {
            "sample_attempts": attempts,
            "winning_observations": counts[winner_signature],
            "stable": counts[winner_signature] >= min(2, attempts),
        }
        return winner

    def _platform_health_check(self) -> Dict[str, Any]:
        permissions_result = self._peek("permissions")
        permissions = parse_permissions_output(permissions_result.stdout)
        window = self.discover_window_target() if permissions["healthy"] else None
        error_code = None
        if not permissions["healthy"]:
            error_code = "permission_denied"
        elif window is None:
            error_code = "window_not_found"
        return {
            "ok": error_code is None,
            "error_code": error_code,
            "phase": "health_check",
            "checked_at": now_iso(),
            "account_id": self.config.account_id,
            "permissions": permissions,
            "window": window,
            "peekaboo_bin": self.config.peekaboo_bin,
        }

    def list_windows(self, app: str) -> List[Dict[str, Any]]:
        result = self._peek(
            "list",
            "windows",
            "--app",
            app,
            "--include-details",
            "ids,bounds",
            "--json",
        )
        if not result.ok:
            return []
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []
        return payload.get("data", {}).get("windows", [])

    def discover_window_target(self) -> Optional[Dict[str, Any]]:
        for app in self.config.app_candidates:
            result = self._peek(
                "list",
                "windows",
                "--app",
                app,
                "--include-details",
                "ids,bounds",
                "--json",
            )
            if not result.ok:
                continue
            try:
                payload = json.loads(result.stdout)
            except json.JSONDecodeError:
                continue
            selected = first_window_target(payload)
            if selected:
                title, window_id = selected
                return {
                    "app": app,
                    "window_id": window_id,
                    "title": title,
                    "windows": payload.get("data", {}).get("windows", []),
                }
        return None

    def probe_window(self, target: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        target = target or self.discover_window_target()
        if not target:
            return self._top_level_health_failure(
                "window_not_found",
                phase="window_discovery",
            )
        try:
            screen_capture = self._run(
                ("screencapture", "-x", "-l", str(target["window_id"]), str(self.config.probe_path)),
                timeout=5,
            )
        except Exception:
            screen_capture = type("_R", (), {"ok": False})()
        if screen_capture.ok and self.config.probe_path.exists() and not image_is_blank(self.config.probe_path):
            return {
                "ok": True,
                "target": target,
                "path": str(self.config.probe_path),
                "capture_source": "screencapture",
            }
        result = self._peek(
            "image",
            "--app",
            target["app"],
            "--window-id",
            str(target["window_id"]),
            "--path",
            str(self.config.probe_path),
        )
        if not result.ok:
            return self._top_level_health_failure(
                result.error_code or "probe_failed",
                phase="window_discovery",
                stderr=result.stderr.strip(),
                window=target,
            )
        if image_is_blank(self.config.probe_path):
            return self._top_level_health_failure(
                "probe_blank_image",
                phase="window_discovery",
                window=target,
            )
        return {
            "ok": True,
            "target": target,
            "path": str(self.config.probe_path),
            "capture_source": "peekaboo",
        }

    def _openai_env(self) -> Dict[str, str]:
        key = (
            os.environ.get("OPENAI_API_KEY")
            or self._env_cache.get("OPENAI_API_KEY")
            or self._env_cache.get("MEM0_OPENAI_API_KEY")
        )
        return {"OPENAI_API_KEY": key} if key else {}

    def run_vision_ocr(self, image_path: Path) -> Dict[str, Any]:
        result = self._run((str(self.config.vision_ocr_script), str(image_path)), timeout=15)
        if not result.ok:
            return self._top_level_health_failure(
                result.error_code or "ocr_failed",
                phase="window_discovery",
                stderr=result.stderr,
            )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            return self._top_level_health_failure(
                "ocr_failed",
                phase="window_discovery",
                stderr=result.stdout,
            )
        return {"ok": True, "payload": payload}

    def analyze_view(
        self,
        prompt: str,
        target: Optional[Dict[str, Any]] = None,
        *,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        target = target or self.discover_window_target()
        if not target:
            return self._top_level_health_failure(
                "window_not_found",
                phase="window_discovery",
            )
        timeout_value = timeout_seconds or self.config.timeout_seconds
        args = [
            "see",
            "--app",
            target["app"],
            "--window-id",
            str(target["window_id"]),
            "--path",
            str(self.config.see_path),
            "--timeout-seconds",
            str(timeout_value),
            "--analyze",
            prompt,
        ]
        result = self._run(
            (self.config.peekaboo_bin, *args),
            timeout=timeout_value,
            extra_env=self._openai_env(),
        )
        if not result.ok:
            return self._top_level_health_failure(
                result.error_code or "ocr_failed",
                phase="view_detection",
                stderr=result.stderr.strip(),
                window=target,
            )
        return {
            "ok": True,
            "target": target,
            "raw": result.stdout,
            "answer": extract_ai_section(result.stdout),
            "path": str(self.config.see_path),
        }

    def detect_view(self, target: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        prompt = (
            "请只输出以下枚举之一：chat_list, chat_detail, moments_feed, "
            "moments_detail, unknown_view。不要解释。"
        )
        result = self.analyze_view(
            prompt,
            target=target,
            timeout_seconds=self.config.unread_timeout_seconds,
        )
        if not result.get("ok"):
            return result
        answer = (result["answer"] or "unknown_view").strip()
        if answer not in {
            "chat_list",
            "chat_detail",
            "moments_feed",
            "moments_detail",
            "unknown_view",
        }:
            answer = "unknown_view"
        result["view"] = answer
        return result

    def identify_current_contact(self, target: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        prompt = "请只输出当前微信聊天窗口顶部显示的联系人或群名称；若无法识别只输出__UNKNOWN__。"
        result = self.analyze_view(prompt, target=target)
        if result.get("ok"):
            result["contact"] = result["answer"] or "__UNKNOWN__"
        return result

    def read_last_incoming_message(self, target: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        prompt = "请只输出当前微信聊天中对方最后一条消息的纯文本；若看不清或没有输出__NONE__。"
        result = self.analyze_view(prompt, target=target)
        if result.get("ok"):
            result["message"] = result["answer"] or "__NONE__"
        return result

    def fallback_session_from_ocr(self, target: Dict[str, Any]) -> Dict[str, Any]:
        probe = self.probe_window(target)
        if not probe.get("ok"):
            return {
                "ok": True,
                "view": "unknown_view",
                "current_contact": "__UNKNOWN__",
                "last_incoming_message": "__NONE__",
                "chat_kind": "unknown_chat",
                "fallback_source": "probe_failed",
            }
        ocr = self.run_vision_ocr(self.config.probe_path)
        if not ocr.get("ok"):
            return {
                "ok": True,
                "view": "unknown_view",
                "current_contact": "__UNKNOWN__",
                "last_incoming_message": "__NONE__",
                "chat_kind": "unknown_chat",
                "fallback_source": "vision_ocr_failed",
            }

        lines = ocr["payload"].get("lines", [])
        left_lines = [
            line
            for line in lines
            if float((line.get("boundingBox") or [0, 0, 0, 0])[0]) < 0.42
        ]
        right_lines = [
            line
            for line in lines
            if float((line.get("boundingBox") or [0, 0, 0, 0])[0]) >= 0.42
        ]
        top_lines = [
            line
            for line in lines
            if 0.38 <= float((line.get("boundingBox") or [0, 0, 0, 0])[0]) <= 0.85
            and float((line.get("boundingBox") or [0, 0, 0, 0])[1]) >= 0.88
            and float((line.get("boundingBox") or [0, 0, 0, 0])[2]) >= 0.08
            and likely_contact_text(ensure_text(line.get("text")))
        ]
        top_lines.sort(
            key=lambda line: (
                -float(line.get("confidence", 0.0)),
                -len(ensure_text(line.get("text"))),
            )
        )
        contact = ensure_text(top_lines[0].get("text")).strip() if top_lines else "__UNKNOWN__"
        visible_messages = extract_group_messages_from_ocr_payload(ocr["payload"])
        if visible_messages:
            last_message = visible_messages[-1].get("text", "__NONE__")
        else:
            message_candidates = [
                ensure_text(line.get("text")).strip()
                for line in right_lines
                if float((line.get("boundingBox") or [0, 0, 0, 0])[1]) < 0.60
                and not parse_time_like(ensure_text(line.get("text")))
            ]
            message_candidates = [line for line in message_candidates if line]
            last_message = message_candidates[-1] if message_candidates else "__NONE__"

        if contact != "__UNKNOWN__" and (visible_messages or len(right_lines) >= 4):
            view = "chat_detail"
        elif len(left_lines) >= 4:
            view = "chat_list"
        else:
            view = "unknown_view"
        chat_kind = (
            classify_chat_kind(current_contact=contact, visible_messages=visible_messages)
            if view == "chat_detail"
            else "unknown_chat"
        )
        return {
            "ok": True,
            "view": view,
            "current_contact": contact,
            "last_incoming_message": last_message,
            "chat_kind": chat_kind,
            "fallback_source": "vision_ocr",
            "ocr_text": ocr["payload"].get("fullText", ""),
        }

    def _read_badge_count(
        self,
        source: Path,
        badge: Dict[str, Any],
        *,
        index: int,
        prefix: str,
    ) -> Optional[int]:
        try:
            from PIL import Image, ImageOps
        except Exception:
            return None

        if not source.exists():
            return None

        img = Image.open(source)
        width, height = img.size
        margin = 8
        left = max(0, int(badge["left"]) - margin)
        top = max(0, int(badge["top"]) - margin)
        right = min(width, int(badge["right"]) + margin + 1)
        bottom = min(height, int(badge["bottom"]) + margin + 1)
        crop = img.crop((left, top, right, bottom)).convert("RGB")
        variant_paths: List[Path] = []

        original = crop.resize((max((right - left) * 10, 64), max((bottom - top) * 10, 64)))
        original_path = self.config.temp_dir / f"{prefix}-badge-{index}.png"
        original.save(original_path)
        variant_paths.append(original_path)

        bw = Image.new("L", original.size, 255)
        for y in range(original.height):
            for x in range(original.width):
                r, g, b = original.getpixel((x, y))
                lum = (r + g + b) / 3
                if lum > 205 and abs(r - g) < 40 and abs(r - b) < 40:
                    bw.putpixel((x, y), 0)
                elif r > 160 and g < 170 and b < 170:
                    bw.putpixel((x, y), 255)
                else:
                    bw.putpixel((x, y), 255)
        bw = ImageOps.autocontrast(bw)
        bw_path = self.config.temp_dir / f"{prefix}-badge-{index}-bw.png"
        bw.save(bw_path)
        variant_paths.append(bw_path)

        inv_path = self.config.temp_dir / f"{prefix}-badge-{index}-inv.png"
        ImageOps.invert(bw).save(inv_path)
        variant_paths.append(inv_path)

        for path in variant_paths:
            ocr = self.run_vision_ocr(path)
            if not ocr.get("ok"):
                continue
            full_text = str(ocr["payload"].get("fullText") or "").strip()
            count = parse_unread_count(full_text)
            if count is not None:
                return count
        return infer_badge_count_from_image(original_path)

    def _build_unread_summary(
        self,
        *,
        items: List[Dict[str, Any]],
        app_has_unread_badge: bool,
        app_unread_badge_count: Optional[int],
        visible_session_count: int,
    ) -> Dict[str, Any]:
        numeric_counts = [
            int(item["unread_badge_count"])
            for item in items
            if item.get("unread_badge_count") is not None
        ]
        return {
            "app_has_unread_badge": app_has_unread_badge,
            "app_unread_badge_count": app_unread_badge_count,
            "visible_session_count": visible_session_count,
            "visible_unread_session_count": len(items),
            "visible_unread_sessions_with_numeric_badge": len(numeric_counts),
            "visible_unread_message_badge_total": sum(numeric_counts),
            "visible_unread_names": [item.get("name") for item in items],
        }

    def _merge_badge_unread_items(
        self,
        *,
        conversations: List[Dict[str, Any]],
        extracted_items: List[Dict[str, Any]],
        app_badge: Optional[Dict[str, Any]],
        session_badges: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        merged: Dict[str, Dict[str, Any]] = {}
        for item in extracted_items:
            key = normalize_contact_name(item["name"])
            merged[key] = {
                "name": item["name"],
                "preview": item.get("preview", ""),
                "preview_text": item.get("preview_text") or item.get("preview", ""),
                "time": item.get("time", ""),
                "has_unread_badge": bool(item.get("has_unread_badge")),
                "unread_badge_count": item.get("unread_badge_count", item.get("unread_count")),
                "unread_count": item.get("unread_count"),
            }

        app_has_unread_badge = app_badge is not None
        app_unread_badge_count = (
            self._read_badge_count(
                self.config.navrail_path,
                app_badge,
                index=9000,
                prefix="app",
            )
            if app_badge
            else None
        )

        for index, badge in enumerate(session_badges):
            matched = min(
                conversations,
                key=lambda candidate: abs(candidate["y"] - badge["center_y"]),
                default=None,
            )
            if not matched:
                continue
            if abs(matched["y"] - badge["center_y"]) > 0.045:
                continue
            count = self._read_badge_count(
                self.config.sidebar_path,
                badge,
                index=index,
                prefix="session",
            )
            key = normalize_contact_name(matched["name"])
            current = merged.get(key)
            if current:
                current["has_unread_badge"] = True
                if count is not None:
                    existing = current.get("unread_badge_count")
                    current["unread_badge_count"] = max(existing or 0, count)
                    current["unread_count"] = current["unread_badge_count"]
                if not current.get("preview_text"):
                    current["preview"] = matched.get("preview", "")
                    current["preview_text"] = matched.get("preview", "")
                if not current.get("time"):
                    current["time"] = matched.get("time", "")
            else:
                merged[key] = {
                    "name": matched["name"],
                    "has_unread_badge": True,
                    "unread_badge_count": count,
                    "unread_count": count,
                    "preview": matched.get("preview", ""),
                    "preview_text": matched.get("preview", ""),
                    "time": matched.get("time", ""),
                }
        normalized = normalize_unread_items(
            [item for item in merged.values() if item.get("has_unread_badge")]
        )
        return {
            "items": normalized,
            "app_has_unread_badge": app_has_unread_badge,
            "app_unread_badge_count": app_unread_badge_count,
            "summary": self._build_unread_summary(
                items=normalized,
                app_has_unread_badge=app_has_unread_badge,
                app_unread_badge_count=app_unread_badge_count,
                visible_session_count=len(conversations),
            ),
        }

    def fallback_unread_from_ocr(self, target: Dict[str, Any]) -> Dict[str, Any]:
        probe = self.probe_window(target)
        if not probe.get("ok"):
            return {
                "ok": False,
                "available": False,
                "items": [],
                "signature": unread_signature([]),
                "view": "unknown_view",
            }
        crop_image(
            self.config.probe_path,
            self.config.navrail_path,
            x0=0.00,
            y0=0.00,
            x1=0.095,
            y1=1.00,
        )
        crop_image(
            self.config.probe_path,
            self.config.sidebar_path,
            x0=0.095,
            y0=0.05,
            x1=0.42,
            y1=0.98,
        )
        ocr = self.run_vision_ocr(self.config.sidebar_path)
        if not ocr.get("ok"):
            return {
                "ok": False,
                "available": False,
                "items": [],
                "signature": unread_signature([]),
                "view": "unknown_view",
            }
        extracted = extract_unread_from_ocr_payload(ocr["payload"])
        row_infos = sidebar_row_infos_from_ocr_payload(ocr["payload"])
        conversations = sidebar_conversation_candidates(row_infos)
        nav_badges = detect_badge_components(self.config.navrail_path)
        app_badge = detect_nav_chat_badge(nav_badges)
        session_badges = detect_conversation_badges(detect_badge_components(self.config.sidebar_path))
        merged = self._merge_badge_unread_items(
            conversations=conversations,
            extracted_items=extracted["items"],
            app_badge=app_badge,
            session_badges=session_badges,
        )
        return {
            "ok": True,
            "available": extracted["available"],
            "app_has_unread_badge": merged["app_has_unread_badge"],
            "app_unread_badge_count": merged["app_unread_badge_count"],
            "items": merged["items"],
            "summary": merged["summary"],
            "signature": unread_signature(merged["items"]),
            "view": "chat_list" if extracted["available"] else "unknown_view",
            "fallback_source": "vision_ocr",
            "ocr_text": ocr["payload"].get("fullText", ""),
            "artifact_path": str(self.config.sidebar_path),
        }

    def user_idle_seconds(self) -> Optional[float]:
        result = self._run(("ioreg", "-c", "IOHIDSystem"))
        if not result.ok:
            return None
        return parse_hid_idle_time_seconds(result.stdout)

    def user_activity_state(self) -> Dict[str, Any]:
        idle_seconds = self.user_idle_seconds()
        return {
            "ok": idle_seconds is not None,
            "idle_seconds": idle_seconds,
            "min_idle_seconds": self.config.min_user_idle_seconds,
            "human_active": idle_seconds is not None
            and idle_seconds < self.config.min_user_idle_seconds,
        }

    def cleanup_artifacts(self) -> Dict[str, Any]:
        removed = 0
        artifact_cutoff = datetime.now(tz=UTC) - timedelta(hours=self.config.artifact_ttl_hours)
        for path in self.config.failure_dir.glob("*.png"):
            modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
            if modified < artifact_cutoff:
                path.unlink(missing_ok=True)
                removed += 1

        failures = sorted(
            self.config.failure_dir.glob("*.png"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        for path in failures[self.config.keep_failed_samples :]:
            path.unlink(missing_ok=True)
            removed += 1

        tx_cutoff = datetime.now(tz=UTC) - timedelta(hours=self.config.tx_ttl_hours)
        for path in self.config.tx_dir.glob("*.json"):
            modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
            if modified < tx_cutoff:
                path.unlink(missing_ok=True)
                removed += 1

        queue_cutoff = datetime.now(tz=UTC) - timedelta(hours=self.config.queue_retention_hours)
        for base in (
            self.config.jobs_done_dir,
            self.config.results_consumed_dir,
            self.config.results_failed_dir,
        ):
            for path in base.glob("*.json"):
                modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
                if modified < queue_cutoff:
                    path.unlink(missing_ok=True)
                    removed += 1

        seen_cards = self.load_moments_seen()
        if self.save_moments_seen(self.cleanup_seen_cards(seen_cards)):
            removed += 0

        desktop_removed = self.cleanup_desktop_leaks()
        removed += desktop_removed

        return {
            "removed": removed,
            "ttl_hours": self.config.artifact_ttl_hours,
            "desktop_removed": desktop_removed,
            "desktop_ttl_minutes": self.config.desktop_artifact_ttl_minutes,
            "queue_retention_hours": self.config.queue_retention_hours,
        }

    def cleanup_desktop_leaks(self) -> int:
        desktop_dir = self.config.desktop_dir
        if self.config.desktop_artifact_ttl_minutes <= 0 or not desktop_dir.exists():
            return 0
        cutoff = datetime.now(tz=UTC) - timedelta(
            minutes=self.config.desktop_artifact_ttl_minutes
        )
        removed = 0
        for path in sorted(desktop_dir.glob("peekaboo_see_*.png")):
            if not path.is_file():
                continue
            try:
                modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
            except FileNotFoundError:
                continue
            if modified >= cutoff:
                continue
            path.unlink(missing_ok=True)
            removed += 1
        return removed

    def cleanup_temp_files(self) -> None:
        self.config.probe_path.unlink(missing_ok=True)
        self.config.see_path.unlink(missing_ok=True)

    def record_failure_sample(self, label: str) -> Optional[str]:
        if not self.config.see_path.exists():
            return None
        timestamp = int(time.time())
        target = self.config.failure_dir / f"{label}-{timestamp}.png"
        shutil.copy2(self.config.see_path, target)
        self.cleanup_artifacts()
        return str(target)

    def append_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        event = {"type": event_type, "ts": now_iso(), "payload": payload}
        with self.config.events_file.open("a") as handle:
            handle.write(json.dumps(json_safe(event), ensure_ascii=False) + "\n")

    def load_state(self) -> Dict[str, Any]:
        return self._read_json_file(self.config.state_file, {})

    def save_state(self, state: Dict[str, Any]) -> None:
        self._write_json_file(self.config.state_file, state)

    def load_daemon_state(self) -> Dict[str, Any]:
        return self._read_json_file(self.config.daemon_state_file, {})

    def save_daemon_state(self, payload: Dict[str, Any]) -> None:
        self._write_json_file(self.config.daemon_state_file, payload)

    def touch_daemon_state(
        self,
        *,
        watches: Iterable[str],
        pid: Optional[int] = None,
        status: str = "running",
    ) -> Dict[str, Any]:
        payload = {
            "pid": pid or os.getpid(),
            "status": status,
            "watches": sorted(set(watches)),
            "last_heartbeat_at": now_iso(),
            "updated_at": now_iso(),
        }
        self.save_daemon_state(payload)
        return payload

    def load_worker_state(self) -> Dict[str, Any]:
        return self._read_json_file(self.config.worker_state_file, {})

    def worker_status(self) -> Dict[str, Any]:
        state = self.load_worker_state()
        last_heartbeat = parse_iso(state.get("last_heartbeat_at"))
        stale_after = max(self.config.processing_lease_seconds * 2, self.config.poll_interval_seconds * 4)
        status = state.get("status", "stopped")
        healthy = bool(
            status in {"running", "idle"}
            and last_heartbeat
            and (datetime.now(tz=UTC) - last_heartbeat).total_seconds() <= stale_after
        )
        return {
            "healthy": healthy,
            "status": status,
            "pid": state.get("pid"),
            "last_heartbeat_at": state.get("last_heartbeat_at"),
            "current_job_id": state.get("current_job_id"),
            "processed_jobs": state.get("processed_jobs", 0),
        }

    def daemon_status(self) -> Dict[str, Any]:
        state = self.load_daemon_state()
        last_heartbeat = parse_iso(state.get("last_heartbeat_at"))
        stale_after = max(self.config.processing_lease_seconds, self.config.poll_interval_seconds * 3)
        status = state.get("status", "stopped")
        healthy = bool(
            status == "running"
            and last_heartbeat
            and (datetime.now(tz=UTC) - last_heartbeat).total_seconds() <= stale_after
        )
        return {
            "healthy": healthy,
            "status": status,
            "pid": state.get("pid"),
            "watches": state.get("watches", []),
            "last_heartbeat_at": state.get("last_heartbeat_at"),
        }

    def queue_status(self) -> Dict[str, Any]:
        def count_files(path: Path) -> int:
            return len(list(path.glob("*.json")))

        stale_processing = 0
        now = datetime.now(tz=UTC)
        for path in self.config.jobs_processing_dir.glob("*.json"):
            job = self._read_json_file(path, {})
            claimed_at = parse_iso(job.get("claimed_at"))
            if claimed_at and (now - claimed_at).total_seconds() > self.config.processing_lease_seconds:
                stale_processing += 1
        return {
            "jobs": {
                "pending": count_files(self.config.jobs_pending_dir),
                "processing": count_files(self.config.jobs_processing_dir),
                "done": count_files(self.config.jobs_done_dir),
                "stale_processing": stale_processing,
            },
            "results": {
                "pending": count_files(self.config.results_pending_dir),
                "consumed": count_files(self.config.results_consumed_dir),
                "failed": count_files(self.config.results_failed_dir),
            },
        }

    def default_watcher_state(self, watcher: str) -> Dict[str, Any]:
        return {
            "watcher": watcher,
            "enabled": True,
            "healthy": True,
            "available": False,
            "phase": WATCHER_PHASES[watcher],
            "last_checked_at": None,
            "last_success_at": None,
            "last_error_at": None,
            "last_error_code": None,
            "consecutive_failures": 0,
            "cursor": 0,
            "signature": "",
            "recommended_next_step": None,
            "payload": {},
        }

    def load_watcher_state(self, watcher: str) -> Dict[str, Any]:
        payload = self._read_json_file(
            self.config.watcher_state_path(watcher),
            self.default_watcher_state(watcher),
        )
        state = self.default_watcher_state(watcher)
        state.update(payload if isinstance(payload, dict) else {})
        state["watcher"] = watcher
        return state

    def save_watcher_state(self, watcher: str, state: Dict[str, Any]) -> None:
        self._write_json_file(self.config.watcher_state_path(watcher), state)

    def load_all_watcher_states(self) -> Dict[str, Any]:
        return {watcher: self.load_watcher_state(watcher) for watcher in KNOWN_WATCHERS}

    def load_moments_seen(self) -> Dict[str, str]:
        payload = self._read_json_file(self.config.moments_seen_file, {})
        return payload if isinstance(payload, dict) else {}

    def cleanup_seen_cards(self, payload: Dict[str, str]) -> Dict[str, str]:
        cutoff = datetime.now(tz=UTC) - timedelta(hours=self.config.moments_seen_ttl_hours)
        result: Dict[str, str] = {}
        for signature, ts in payload.items():
            parsed = parse_iso(ts)
            if parsed and parsed >= cutoff:
                result[signature] = ts
        return result

    def save_moments_seen(self, payload: Dict[str, str]) -> bool:
        cleaned = self.cleanup_seen_cards(payload)
        self._write_json_file(self.config.moments_seen_file, cleaned)
        return True

    def mark_moments_seen(self, signatures: Iterable[str]) -> None:
        payload = self.load_moments_seen()
        timestamp = now_iso()
        for signature in signatures:
            payload[signature] = timestamp
        self.save_moments_seen(payload)

    def enqueue_job(
        self,
        *,
        job_type: str,
        source: str,
        cursor: int,
        signature: str,
        payload: Dict[str, Any],
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        job = {
            "job_id": uuid4().hex,
            "type": job_type,
            "source": source,
            "created_at": now_iso(),
            "cursor": cursor,
            "signature": signature,
            "payload": json_safe(payload),
            "retry_count": 0,
            "max_retries": max_retries,
        }
        path = self.config.jobs_pending_dir / f"{job['job_id']}.json"
        self._write_json_file(path, job)
        self.append_event("job_enqueued", {"job_id": job["job_id"], "type": job_type, "source": source})
        return job

    def health_check(self) -> Dict[str, Any]:
        runtime = self._platform_health_check()
        watchers = self.load_all_watcher_states()
        daemon = self.daemon_status()
        worker = self.worker_status()
        queues = self.queue_status()
        watcher_unhealthy = any(not state.get("healthy", True) for state in watchers.values())
        overall_healthy = (
            bool(runtime.get("ok"))
            and daemon.get("healthy", False)
            and worker.get("healthy", False)
            and not watcher_unhealthy
        )
        recommended_next_step = None
        if not overall_healthy:
            recommended_next_step = recommended_next_step_for_error(
                runtime.get("error_code")
                or ("watcher_unhealthy" if watcher_unhealthy else None)
                or ("worker_stale" if not worker.get("healthy", False) else None)
                or ("daemon_stale" if not daemon.get("healthy", False) else None)
            )
        result = {
            "ok": runtime.get("ok", False),
            "overall_healthy": overall_healthy,
            "error_code": runtime.get("error_code"),
            "phase": "health_check",
            "current_view": "unknown_view",
            "current_contact": "__UNKNOWN__",
            "recommended_next_step": recommended_next_step,
            "checked_at": runtime.get("checked_at"),
            "account_id": runtime.get("account_id"),
            "permissions": runtime.get("permissions"),
            "window": runtime.get("window"),
            "peekaboo_bin": runtime.get("peekaboo_bin"),
            "runtime": runtime,
            "daemon": daemon,
            "worker": worker,
            "watchers": watchers,
            "queues": queues,
        }
        return result

    def _session_current_from_target(self, target: Dict[str, Any]) -> Dict[str, Any]:
        fallback = self.fallback_session_from_ocr(target)
        fallback_view = fallback.get("view", "unknown_view")
        fallback_contact = fallback.get("current_contact", "__UNKNOWN__")
        fallback_message = fallback.get("last_incoming_message", "__NONE__")
        if fallback.get("ok") and (
            fallback_view != "unknown_view"
            or fallback_contact != "__UNKNOWN__"
            or fallback_message != "__NONE__"
        ):
            return self._success_payload(
                phase="view_detection",
                current_view=fallback_view,
                current_contact=fallback_contact,
                checked_at=now_iso(),
                account_id=self.config.account_id,
                window=target,
                view=fallback_view,
                last_incoming_message=fallback_message,
                chat_kind=fallback.get("chat_kind", "unknown_chat"),
                artifacts={
                    "probe_path": str(self.config.probe_path),
                    "see_path": str(self.config.see_path),
                },
                fallback_source=fallback.get("fallback_source"),
            )

        view_result = self.detect_view(target=target)
        if not view_result.get("ok"):
            return self._success_payload(
                phase="view_detection",
                current_view=fallback.get("view", "unknown_view"),
                current_contact=fallback.get("current_contact", "__UNKNOWN__"),
                checked_at=now_iso(),
                account_id=self.config.account_id,
                window=target,
                view=fallback.get("view", "unknown_view"),
                last_incoming_message=fallback.get("last_incoming_message", "__NONE__"),
                chat_kind=fallback.get("chat_kind", "unknown_chat"),
                artifacts={
                    "probe_path": str(self.config.probe_path),
                    "see_path": str(self.config.see_path),
                },
                fallback_source=fallback.get("fallback_source"),
            )

        view_name = view_result.get("view", "unknown_view")
        contact_result = (
            self.identify_current_contact(target=target)
            if view_name == "chat_detail"
            else {"contact": "__UNKNOWN__"}
        )
        message_result = (
            self.read_last_incoming_message(target=target)
            if view_name == "chat_detail"
            else {"message": "__NONE__"}
        )
        state = self._success_payload(
            phase="view_detection",
            current_view=view_name,
            current_contact=contact_result.get("contact", "__UNKNOWN__"),
            checked_at=now_iso(),
            account_id=self.config.account_id,
            window=target,
            view=view_name,
            last_incoming_message=message_result.get("message", "__NONE__"),
            chat_kind="group_chat" if likely_group_contact_name(contact_result.get("contact", "__UNKNOWN__")) else "private_chat" if contact_result.get("contact", "__UNKNOWN__") != "__UNKNOWN__" else "unknown_chat",
            artifacts={
                "probe_path": str(self.config.probe_path),
                "see_path": str(self.config.see_path),
            },
        )
        if view_name == "unknown_view" or state["current_contact"] == "__UNKNOWN__":
            fallback = self.fallback_session_from_ocr(target)
            if fallback.get("view") != "unknown_view":
                state["view"] = fallback.get("view", state["view"])
                state["current_view"] = state["view"]
            if state["current_contact"] == "__UNKNOWN__" and fallback.get("current_contact"):
                state["current_contact"] = fallback.get("current_contact", state["current_contact"])
            if state["last_incoming_message"] == "__NONE__" and fallback.get("last_incoming_message"):
                state["last_incoming_message"] = fallback.get(
                    "last_incoming_message",
                    state["last_incoming_message"],
                )
            if fallback.get("chat_kind"):
                state["chat_kind"] = fallback.get("chat_kind", state.get("chat_kind", "unknown_chat"))
            state["fallback_source"] = fallback.get("fallback_source")
        return state

    def session_current(self) -> Dict[str, Any]:
        runtime = self._platform_health_check()
        if not runtime.get("ok"):
            return self._top_level_health_failure(
                runtime.get("error_code", "window_not_found"),
                phase="health_check",
                checked_at=runtime.get("checked_at"),
                account_id=runtime.get("account_id"),
                permissions=runtime.get("permissions"),
                window=runtime.get("window"),
                peekaboo_bin=runtime.get("peekaboo_bin"),
            )
        return self._collect_stable_payload(
            lambda: self._session_current_from_target(runtime["window"]),
            signature_fn=session_payload_signature,
        )

    def _collect_unread_snapshot(
        self,
        *,
        target: Optional[Dict[str, Any]],
        current_view: Optional[str],
        current_contact: str,
    ) -> Dict[str, Any]:
        if not target:
            return self._watcher_failure(
                "unread",
                "window_not_found",
                current_view=current_view or "unknown_view",
                current_contact=current_contact,
            )

        ocr_result = self._collect_stable_payload(
            lambda: self.fallback_unread_from_ocr(target),
            signature_fn=unread_payload_signature,
        )
        if ocr_result.get("ok"):
            return self._success_payload(
                phase=WATCHER_PHASES["unread"],
                current_view=ocr_result.get("view", current_view or "unknown_view"),
                current_contact=current_contact,
                view=ocr_result.get("view", current_view or "unknown_view"),
                available=ocr_result.get("available", False),
                app_has_unread_badge=ocr_result.get("app_has_unread_badge", False),
                app_unread_badge_count=ocr_result.get("app_unread_badge_count"),
                items=ocr_result.get("items", []),
                summary=ocr_result.get("summary", {}),
                signature=ocr_result.get("signature", unread_signature([])),
                fallback_source=ocr_result.get("fallback_source"),
                stability=ocr_result.get("stability"),
            )

        result = self.analyze_view(
            (
                "请读取当前微信界面，并只输出一个 JSON 对象。"
                "格式必须是 {\"view\":\"chat_list|chat_detail|moments_feed|moments_detail|unknown_view\","
                "\"available\":true|false,"
                "\"items\":[{\"name\":\"会话名\",\"unread_count\":数字或null,\"preview\":\"摘要\"}] }。"
                "规则：如果左侧会话栏可见，就读取所有带未读红点或未读数字的会话；"
                "即使当前停留在聊天详情页，只要左侧会话栏可见，也要识别；"
                "如果左侧会话栏不可见，available=false 且 items=[]。"
            ),
            target=target,
            timeout_seconds=self.config.unread_timeout_seconds,
        )
        if not result.get("ok"):
            return self._watcher_failure(
                "unread",
                result.get("error_code", "ocr_failed"),
                current_view=current_view or "unknown_view",
                current_contact=current_contact,
                stderr=result.get("stderr", ""),
            )

        parsed = extract_json_fragment(result["raw"])
        parsed = parsed if isinstance(parsed, dict) else {}
        items = normalize_unread_items(parsed.get("items", []))
        view = parsed.get("view") if parsed.get("view") in {
            "chat_list",
            "chat_detail",
            "moments_feed",
            "moments_detail",
            "unknown_view",
        } else (current_view or "unknown_view")
        available = bool(parsed.get("available")) if parsed else view in {"chat_list", "chat_detail"}
        return self._success_payload(
            phase=WATCHER_PHASES["unread"],
            current_view=view,
            current_contact=current_contact,
            view=view,
            available=available,
            items=items,
            signature=unread_signature(items),
        )

    def _collect_chat_visible_snapshot(
        self,
        *,
        target: Optional[Dict[str, Any]],
        session: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        current_view = (session or {}).get("view", "unknown_view")
        current_contact = (session or {}).get("current_contact", "__UNKNOWN__")
        if not target:
            return self._watcher_failure(
                "chat_visible",
                "window_not_found",
                current_view=current_view,
                current_contact=current_contact,
            )

        if current_view != "chat_detail":
            return self._success_payload(
                phase=WATCHER_PHASES["chat_visible"],
                current_view=current_view,
                current_contact=current_contact,
                view=current_view,
                available=False,
                messages=[],
                signature="",
            )

        def sample_once() -> Dict[str, Any]:
            probe = self.probe_window(target)
            if not probe.get("ok"):
                return self._watcher_failure(
                    "chat_visible",
                    probe.get("error_code", "window_not_found"),
                    current_view=current_view,
                    current_contact=current_contact,
                    stderr=probe.get("stderr", ""),
                )

            crop_image(
                self.config.probe_path,
                self.config.content_path,
                x0=0.40,
                y0=0.08,
                x1=0.98,
                y1=0.98,
            )
            ocr = self.run_vision_ocr(self.config.content_path)
            if not ocr.get("ok"):
                return self._watcher_failure(
                    "chat_visible",
                    ocr.get("error_code", "ocr_failed"),
                    current_view=current_view,
                    current_contact=current_contact,
                    stderr=ocr.get("stderr", ""),
                )

            messages = normalize_group_messages(
                extract_group_messages_from_ocr_payload(ocr["payload"], cropped=True)
            )
            chat_kind = classify_chat_kind(
                current_contact=current_contact,
                visible_messages=messages,
            )
            available = bool(messages) and chat_kind == "group_chat"
            return self._success_payload(
                phase=WATCHER_PHASES["chat_visible"],
                current_view=current_view,
                current_contact=current_contact,
                view=current_view,
                chat_kind=chat_kind,
                available=available,
                messages=messages if available else [],
                signature=group_messages_signature(messages) if available else "",
                artifact_path=str(self.config.content_path),
                ocr_text=ocr["payload"].get("fullText", ""),
            )

        sampled = self._collect_stable_payload(
            sample_once,
            signature_fn=chat_visible_payload_signature,
        )
        if not sampled.get("ok"):
            return sampled
        return sampled

    def _collect_moments_snapshot(
        self,
        *,
        target: Optional[Dict[str, Any]],
        session: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        current_view = (session or {}).get("view", "unknown_view")
        current_contact = (session or {}).get("current_contact", "__UNKNOWN__")
        if not target:
            return self._watcher_failure(
                "moments",
                "window_not_found",
                current_view=current_view,
                current_contact=current_contact,
            )
        if current_view != "moments_feed":
            return self._success_payload(
                phase=WATCHER_PHASES["moments"],
                current_view=current_view,
                current_contact=current_contact,
                view=current_view,
                available=False,
                items=[],
                feed_signature="",
                signature="",
            )

        result = self.analyze_view(
            (
                "请读取当前朋友圈页面里可见的内容卡片，只输出 JSON 数组。"
                "每项格式为 {\"author\":\"作者\",\"summary\":\"内容摘要\",\"has_media\":true/false}。"
                "如果当前不是朋友圈或没有可见内容，输出 []。"
            ),
            target=target,
        )
        if not result.get("ok"):
            return self._watcher_failure(
                "moments",
                result.get("error_code", "ocr_failed"),
                current_view=current_view,
                current_contact=current_contact,
                stderr=result.get("stderr", ""),
            )
        parsed = extract_json_fragment(result["raw"])
        items = normalize_moments_items(parsed if isinstance(parsed, list) else [])
        seen = self.load_moments_seen()
        enriched = []
        for item in items:
            enriched.append({**item, "seen": item["card_signature"] in seen})
        feed_signature = moments_feed_signature(enriched)
        return self._success_payload(
            phase=WATCHER_PHASES["moments"],
            current_view=current_view,
            current_contact=current_contact,
            view=current_view,
            available=bool(enriched),
            items=enriched,
            feed_signature=feed_signature,
            signature=feed_signature,
        )

    def unread_list(self) -> Dict[str, Any]:
        session = self.session_current()
        if not session.get("ok"):
            return session
        state = self.load_watcher_state("unread")
        payload = self._collect_unread_snapshot(
            target=session.get("window"),
            current_view=session.get("view"),
            current_contact=session.get("current_contact", "__UNKNOWN__"),
        )
        if not payload.get("ok"):
            return payload
        changed = bool(payload.get("available")) and payload.get("signature") != state.get("signature")
        payload["cursor"] = state.get("cursor", 0) + (1 if changed else 0)
        payload["recommended_next_step"] = None
        return payload

    def read_visible_messages(self, target: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        session = self.session_current()
        if not session.get("ok"):
            return session
        target = target or session.get("window")
        state = self.load_watcher_state("chat_visible")
        payload = self._collect_chat_visible_snapshot(target=target, session=session)
        if not payload.get("ok"):
            return payload
        changed = bool(payload.get("available")) and payload.get("signature") != state.get("signature")
        payload["snapshot_signature"] = payload.get("signature", "")
        payload["snapshot_cursor"] = state.get("cursor", 0) + (1 if changed else 0)
        return payload

    def moments_scan(self, target: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        session = self.session_current()
        if not session.get("ok"):
            return session
        target = target or session.get("window")
        state = self.load_watcher_state("moments")
        payload = self._collect_moments_snapshot(target=target, session=session)
        if not payload.get("ok"):
            return payload
        changed = bool(payload.get("available")) and payload.get("signature") != state.get("signature")
        payload["cursor"] = state.get("cursor", 0) + (1 if changed else 0)
        return payload

    def capture_conversation_baseline(self, target: Dict[str, Any]) -> Dict[str, Any]:
        session = self._session_current_from_target(target)
        if not session.get("ok"):
            return session
        return {
            "ok": True,
            "view": session.get("view"),
            "current_contact": session.get("current_contact", "__UNKNOWN__"),
            "last_incoming_message": session.get("last_incoming_message", "__NONE__"),
            "last_incoming_signature": message_signature(
                session.get("last_incoming_message", "__NONE__")
            ),
            "captured_at": now_iso(),
        }

    def focus_window(self, target: Dict[str, Any]) -> CommandResult:
        return self._peek(
            "window",
            "focus",
            "--app",
            target["app"],
            "--window-id",
            str(target["window_id"]),
        )

    def _window_relative_point(
        self,
        target: Dict[str, Any],
        *,
        rel_x: float,
        rel_y: float,
    ) -> Optional[Tuple[int, int]]:
        bounds = bounds_for_window(target)
        if not bounds:
            return None
        win_x, win_y, win_w, win_h = bounds
        return (
            win_x + int(win_w * rel_x),
            win_y + int(win_h * rel_y),
        )

    def focus_chat_search(self, target: Dict[str, Any]) -> CommandResult:
        point = self._window_relative_point(target, rel_x=0.16, rel_y=0.035)
        if not point:
            return CommandResult(ok=False, error_code="window_not_found")
        x, y = point
        # 不带 --window-id，避免 peekaboo 把 click 发到错误的 AX 窗口
        result = self._peek(
            "click",
            "--app",
            target["app"],
            "--coords",
            f"{x},{y}",
        )
        if not result.ok:
            return result
        time.sleep(0.2)
        return result

    def clear_chat_search(self, target: Dict[str, Any], *, attempts: int = 24) -> None:
        for _ in range(max(1, attempts)):
            self._peek("press", "delete", "--app", target["app"])
        time.sleep(0.1)

    def open_chat(self, name: str) -> Dict[str, Any]:
        runtime = self._platform_health_check()
        if not runtime.get("ok"):
            return self._top_level_health_failure(
                runtime.get("error_code", "window_not_found"),
                phase="prepare_send",
                checked_at=runtime.get("checked_at"),
                window=runtime.get("window"),
            )
        target = runtime["window"]
        self.focus_window(target)
        time.sleep(0.6)
        # 先 Escape 2 次清除弹窗
        for _esc in range(2):
            self._peek("press", "escape", "--app", target["app"])
            time.sleep(0.2)
        # 检测是否卡在「搜一搜」聚合页：若导航栏有「搜一搜」字样，需点击侧边栏「聊天」tab 退出
        _probe_pre = self.probe_window(target)
        if _probe_pre.get("ok"):
            _ocr_pre = self.run_vision_ocr(self.config.probe_path)
            if _ocr_pre.get("ok"):
                _in_souyisou = any(
                    "搜一搜" in ensure_text(l.get("text", ""))
                    and l.get("boundingBox", [0, 0])[1] > 0.90
                    for l in _ocr_pre["payload"].get("lines", [])
                )
                if _in_souyisou:
                    import sys as _sys_sou
                    _sys_sou.stderr.write("[open_chat] detected 搜一搜 mode, clicking × to clear search\n")
                    # 找到搜索栏中的 × 按钮并点击，退出搜一搜模式
                    _x_line = None
                    for _l in _ocr_pre["payload"].get("lines", []):
                        if ensure_text(_l.get("text", "")).strip() == "×":
                            _x_line = _l
                            break
                    if _x_line:
                        _xbb = _x_line.get("boundingBox", [])
                        if len(_xbb) >= 2:
                            _bounds = bounds_for_window(target)
                            if _bounds:
                                _wx, _wy, _ww, _wh = _bounds
                                _cx = int(_wx + (_xbb[0] + (_xbb[2] if len(_xbb) >= 3 else 0) / 2) * _ww)
                                _cy = int(_wy + (_xbb[1] + (_xbb[3] if len(_xbb) >= 4 else 0) / 2) * _wh)
                                _sys_sou.stderr.write(f"[open_chat] clicking × at ({_cx},{_cy})\n")
                                self._peek("click", "--app", target["app"], "--coords", f"{_cx},{_cy}")
                    else:
                        _sys_sou.stderr.write("[open_chat] × not found, pressing Escape\n")
                        self._peek("press", "escape", "--app", target["app"])
                    time.sleep(0.8)
        # 点击搜索框
        search_focus = self.focus_chat_search(target)
        if not search_focus.ok:
            return self._top_level_health_failure(
                "send_failed",
                phase="prepare_send",
                stderr=search_focus.stderr.strip(),
            )
        self.clear_chat_search(target, attempts=40)
        # 搜索词去掉括号内人数后缀，避免微信搜索无结果
        search_name = re.sub(r"[（(]\d+[）)]", "", name).strip()
        type_result = self._peek("type", search_name, "--app", target["app"])
        if not type_result.ok:
            return self._top_level_health_failure(
                "send_failed",
                phase="prepare_send",
                stderr=type_result.stderr.strip(),
            )
        time.sleep(1.0)
        # 截图 OCR 找搜索结果里目标群名的坐标，再点击
        # 若 OCR 显示仍在「搜一搜」模式，点击 × 清除并重新搜索一次
        click_ok = False
        _probe_post = self.probe_window(target)
        if _probe_post.get("ok"):
            _ocr_post = self.run_vision_ocr(self.config.probe_path)
            if _ocr_post.get("ok"):
                _still_sou = any(
                    "搜一搜" in ensure_text(l.get("text", ""))
                    and l.get("boundingBox", [0, 0])[1] > 0.90
                    for l in _ocr_post["payload"].get("lines", [])
                )
                if _still_sou:
                    import sys as _sys_post
                    _sys_post.stderr.write("[open_chat] still in 搜一搜 after typing, clicking × and retrying\n")
                    _x2 = next((l for l in _ocr_post["payload"].get("lines", [])
                                if ensure_text(l.get("text", "")).strip() == "×"), None)
                    if _x2:
                        _xbb2 = _x2.get("boundingBox", [])
                        _b2 = bounds_for_window(target)
                        if _b2 and len(_xbb2) >= 4:
                            _wx2, _wy2, _ww2, _wh2 = _b2
                            _cx2 = int(_wx2 + (_xbb2[0] + _xbb2[2] / 2) * _ww2)
                            _cy2 = int(_wy2 + (_xbb2[1] + _xbb2[3] / 2) * _wh2)
                            self._peek("click", "--app", target["app"], "--coords", f"{_cx2},{_cy2}")
                    else:
                        self._peek("press", "escape", "--app", target["app"])
                    time.sleep(0.6)
                    # 重新获得搜索框焦点并输入
                    self.focus_chat_search(target)
                    self.clear_chat_search(target, attempts=40)
                    self._peek("type", search_name, "--app", target["app"])
                    time.sleep(1.2)
        probe2 = self.probe_window(target)
        if probe2.get("ok"):
            ocr2 = self.run_vision_ocr(self.config.probe_path)
            if ocr2.get("ok"):
                bounds = bounds_for_window(target)
                if bounds:
                    win_x, win_y, win_w, win_h = bounds
                    import sys as _sys_b
                    _sys_b.stderr.write(f"[open_chat] window bounds: x={win_x} y={win_y} w={win_w} h={win_h} (window_id={target.get('window_id')})\n")
                    name_norm = normalize_contact_name(name)
                    best_line = None
                    best_score = 0
                    for line in ocr2["payload"].get("lines", []):
                        text = ensure_text(line.get("text", ""))
                        text_norm = normalize_contact_name(text)
                        bb = line.get("boundingBox", [])
                        if len(bb) < 2:
                            continue
                        # 只考虑左侧列表区域（x < 0.42）
                        if bb[0] > 0.42:
                            continue
                        # 跳过搜索框和顶部标题区域（y>0.92）以及底部无效区域（y<0.06）
                        # 群名搜索结果可能出现在 y≈0.87，所以阈值要足够高
                        if bb[1] < 0.06 or bb[1] > 0.92:
                            continue
                        # 跳过「搜一搜」入口行，避免误点搜索聚合页
                        if "搜一搜" in text:
                            continue
                        # 先计算匹配分数
                        score = 0
                        name_core = re.sub(r"[（(]\d+[）)]", "", name_norm).strip()
                        text_core = re.sub(r"[（(]\d+[）)]", "", text_norm).strip()
                        if name_norm == text_norm:
                            score = 100
                        elif name_core and text_core and (name_core in text_core or text_core in name_core):
                            score = 80
                        elif name_core and text_core and len(name_core) >= 4 and name_core[:6] in text_core:
                            score = 60
                        # 跳过消息预览副标题行（y>0.70 且 height<0.020），
                        # 但若该行本身就是匹配目标（score>=60）则保留，
                        # 避免把搜索结果列表靠下位置的群名标题误过滤掉
                        bb_h = bb[3] if len(bb) >= 4 else 1.0
                        if score < 60 and bb[1] > 0.70 and bb_h < 0.020:
                            continue
                        if score > best_score:
                            best_score = score
                            best_line = line
                    import sys as _sys
                    for _dl in ocr2["payload"].get("lines", []):
                        _sys.stderr.write(f"[open_chat] OCR line: text={_dl.get('text','').__repr__()} bb={_dl.get('boundingBox',[])}\n")
                    _sys.stderr.write(f"[open_chat] best_score={best_score} best_line={best_line}\n")
                    if best_line and best_score >= 60:
                        bb = best_line.get("boundingBox", [])
                        cx = win_x + int(win_w * (bb[0] + 0.08))
                        cy = win_y + int(win_h * bb[1])
                        _sys.stderr.write(f"[open_chat] clicking ({cx},{cy})\n")
                        self._peek("click", "--coords", f"{cx},{cy}", "--app", target["app"])
                        time.sleep(1.0)
                        # 重新发现窗口：点击后可能弹出新窗口
                        new_target = self.discover_window_target()
                        if new_target and new_target.get("window_id") != target.get("window_id"):
                            _sys.stderr.write(f"[open_chat] new window detected: {new_target.get('window_id')}\n")
                            target = new_target
                        click_ok = True
        if not click_ok:
            # fallback: 按两次方向键+回车
            # 搜索结果第一行是「搜一搜」聚合入口，第二行才是目标联系人/群
            self._peek("press", "down", "--app", target["app"])
            time.sleep(0.4)
            self._peek("press", "down", "--app", target["app"])
            time.sleep(0.4)
            press_result = self._peek("press", "return", "--app", target["app"])
            if not press_result.ok:
                return self._top_level_health_failure(
                    "send_failed",
                    phase="prepare_send",
                    stderr=press_result.stderr.strip(),
                )
        # 等待 view 切换到 chat_detail，最多重试 6 次（每次 0.8s）
        # 始终用 window 180（完整微信内容窗口）来截图检测
        session = None
        opened_contact = "__UNKNOWN__"
        for _attempt in range(6):
            time.sleep(0.8)
            import sys as _sys2
            session = self._session_current_from_target(target)
            opened_contact = session.get("current_contact", "__UNKNOWN__")
            view_now = session.get("view", "unknown_view")
            _sys2.stderr.write(f"[open_chat] attempt {_attempt}: view={view_now} contact={opened_contact}\n")
            if view_now == "chat_detail" and opened_contact not in ("__UNKNOWN__", "__NONE__"):
                break
        if not contacts_match(name, opened_contact):
            return self._top_level_health_failure(
                "target_mismatch",
                phase="prepare_send",
                current_view=session.get("view", "unknown_view"),
                current_contact=opened_contact,
                expected_contact=name,
                opened_contact=opened_contact,
                window=target,
            )
        return {
            "ok": True,
            "opened": name,
            "opened_contact": opened_contact,
            "window": target,
            "phase": "prepare_send",
            "current_view": session.get("view", "unknown_view"),
            "current_contact": opened_contact,
        }

    def _tx_path(self, tx_id: str) -> Path:
        return self.config.tx_dir / f"{tx_id}.json"

    def save_tx(self, tx: Dict[str, Any]) -> None:
        tx["updated_at"] = now_iso()
        self._write_json_file(self._tx_path(tx["tx_id"]), tx)

    def load_tx(self, tx_id: str) -> Dict[str, Any]:
        path = self._tx_path(tx_id)
        if not path.exists():
            return self._top_level_health_failure("tx_not_found", phase="prepare_send", tx_id=tx_id)
        return self._read_json_file(path, {})

    def freeze_tx(self, tx: Dict[str, Any], error_code: str, **extra: Any) -> Dict[str, Any]:
        tx["ok"] = False
        tx["status"] = "frozen"
        tx["error_code"] = error_code
        tx["current_view"] = extra.pop("current_view", tx.get("current_view", "unknown_view"))
        tx["current_contact"] = extra.pop(
            "current_contact",
            tx.get("current_contact", "__UNKNOWN__"),
        )
        tx["recommended_next_step"] = recommended_next_step_for_error(error_code)
        tx["artifact_path"] = str(self.config.see_path)
        tx.update(json_safe(extra))
        self.save_tx(tx)
        return tx

    def abort_send(self, tx_id: str, reason: str = "aborted") -> Dict[str, Any]:
        tx = self.load_tx(tx_id)
        if tx.get("error_code") == "tx_not_found":
            return tx
        tx["ok"] = False
        tx["status"] = "aborted"
        tx["error_code"] = reason
        tx["recommended_next_step"] = recommended_next_step_for_error(reason)
        self.save_tx(tx)
        return tx

    def prepare_send(self, name: str, text: str) -> Dict[str, Any]:
        runtime = self._platform_health_check()
        if not runtime.get("ok"):
            return self._top_level_health_failure(
                runtime.get("error_code", "window_not_found"),
                phase="prepare_send",
                checked_at=runtime.get("checked_at"),
                window=runtime.get("window"),
            )
        target = runtime["window"]
        opened = self.open_chat(name)
        if not opened.get("ok"):
            return opened
        baseline = self.capture_conversation_baseline(target)
        if not baseline.get("ok"):
            return baseline
        tx = {
            "ok": True,
            "tx_id": uuid4().hex,
            "status": "prepared",
            "phase": "capture_conversation_baseline",
            "expected_contact": name,
            "opened_contact": opened.get("opened_contact", "__UNKNOWN__"),
            "window": target,
            "current_view": baseline.get("view", "unknown_view"),
            "current_contact": baseline.get("current_contact", "__UNKNOWN__"),
            "recommended_next_step": None,
            "message_text": text,
            "chunks": split_message_chunks(text, self.config.send_chunk_max_chars),
            "baseline": baseline,
            "baseline_incoming_message": baseline.get("last_incoming_message"),
            "baseline_signature": baseline.get("last_incoming_signature"),
            "current_incoming_message": baseline.get("last_incoming_message"),
            "current_signature": baseline.get("last_incoming_signature"),
            "draft_text": "",
            "verified_chunks": [],
            "created_at": now_iso(),
        }
        self.save_tx(tx)
        return tx

    def verify_current_chat_target(self, expected_name: str, target: Dict[str, Any]) -> Dict[str, Any]:
        session = self._session_current_from_target(target)
        opened_contact = session.get("current_contact", "__UNKNOWN__")
        if not contacts_match(expected_name, opened_contact):
            return self._top_level_health_failure(
                "target_mismatch",
                phase="verify_send",
                current_view=session.get("view", "unknown_view"),
                current_contact=opened_contact,
                expected_contact=expected_name,
                opened_contact=opened_contact,
                window=target,
            )
        return {
            "ok": True,
            "expected_contact": expected_name,
            "opened_contact": opened_contact,
            "window": target,
            "session": session,
        }

    def wait_for_chat_target(
        self,
        expected_name: str,
        target: Dict[str, Any],
        *,
        attempts: Optional[int] = None,
        delay_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        attempts = attempts or self.config.stable_chat_attempts
        delay_seconds = (
            delay_seconds
            if delay_seconds is not None
            else self.config.stable_chat_delay_ms / 1000
        )
        last_result = self._top_level_health_failure(
            "target_mismatch",
            phase="verify_send",
            expected_contact=expected_name,
            opened_contact="__UNKNOWN__",
            window=target,
        )
        consecutive_matches = 0
        for _ in range(attempts):
            last_result = self.verify_current_chat_target(expected_name, target)
            if last_result.get("ok"):
                consecutive_matches += 1
                if consecutive_matches >= attempts:
                    return last_result
            else:
                consecutive_matches = 0
            time.sleep(delay_seconds)
        if last_result.get("ok"):
            return self._top_level_health_failure(
                "unstable_view",
                phase="verify_send",
                current_view=last_result.get("session", {}).get("view", "unknown_view"),
                current_contact=last_result.get("opened_contact", "__UNKNOWN__"),
                expected_contact=expected_name,
                opened_contact=last_result.get("opened_contact"),
                window=target,
            )
        return last_result

    def inspect_compose_state(self, target: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        prompt = (
            "请只输出一个 JSON 对象，格式必须是："
            "{\"view\":\"chat_list|chat_detail|moments_feed|moments_detail|unknown_view\","
            "\"current_contact\":\"联系人或__UNKNOWN__\","
            "\"input_focused\":true|false,"
            "\"search_focused\":true|false,"
            "\"draft_text\":\"输入框当前文本，没有则空字符串\","
            "\"last_incoming_message\":\"对方最后一条消息，没有则__NONE__\"}。"
            "不要输出解释。"
        )
        result = self.analyze_view(prompt, target=target)
        if not result.get("ok"):
            return result
        parsed = extract_json_fragment(result["raw"])
        parsed = parsed if isinstance(parsed, dict) else {}
        view = parsed.get("view", "unknown_view")
        current_contact = parsed.get("current_contact", "__UNKNOWN__")
        return self._success_payload(
            phase="view_detection",
            current_view=view,
            current_contact=current_contact,
            view=view,
            input_focused=bool(parsed.get("input_focused")),
            search_focused=bool(parsed.get("search_focused")),
            draft_text=ensure_text(parsed.get("draft_text", "")).strip(),
            last_incoming_message=ensure_text(parsed.get("last_incoming_message", "__NONE__")).strip(),
        )

    def verify_send(self, tx_id: str) -> Dict[str, Any]:
        tx = self.load_tx(tx_id)
        if tx.get("error_code") == "tx_not_found":
            return tx
        tx["phase"] = "verify_send"
        target = tx["window"]
        activity = self.user_activity_state()
        if activity.get("human_active"):
            return self.freeze_tx(
                tx,
                "human_active",
                idle_seconds=activity.get("idle_seconds"),
                min_idle_seconds=activity.get("min_idle_seconds"),
            )

        verified = self.wait_for_chat_target(tx["expected_contact"], target)
        if not verified.get("ok"):
            return self.freeze_tx(
                tx,
                verified.get("error_code", "target_mismatch"),
                current_view=verified.get("current_view", "unknown_view"),
                current_contact=verified.get("current_contact", "__UNKNOWN__"),
                expected_contact=verified.get("expected_contact"),
                opened_contact=verified.get("opened_contact"),
            )

        compose = self.inspect_compose_state(target)
        if not compose.get("ok"):
            return self.freeze_tx(
                tx,
                compose.get("error_code", "ocr_failed"),
                stderr=compose.get("stderr", ""),
            )
        tx["current_view"] = compose.get("view", "unknown_view")
        tx["current_contact"] = compose.get("current_contact", "__UNKNOWN__")
        if compose.get("view") != "chat_detail":
            return self.freeze_tx(tx, "view_unknown", current_view=compose.get("view"))
        if compose.get("search_focused"):
            return self.freeze_tx(
                tx,
                "search_mode_active",
                current_view=compose.get("view"),
                current_contact=compose.get("current_contact"),
                compose_state=compose,
            )

        latest_signature = message_signature(compose.get("last_incoming_message", "__NONE__"))
        baseline_signature = tx.get("baseline_signature")
        tx["current_incoming_message"] = compose.get("last_incoming_message")
        tx["current_signature"] = latest_signature
        if latest_signature != baseline_signature:
            return self.freeze_tx(
                tx,
                "new_incoming_message",
                baseline_incoming_message=tx.get("baseline_incoming_message"),
                current_incoming_message=compose.get("last_incoming_message"),
                current_view=compose.get("view"),
                current_contact=compose.get("current_contact"),
            )

        tx["status"] = "verified"
        tx["compose_state"] = json_safe(compose)
        self.save_tx(tx)
        return tx

    def stage_message_chunks(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        target = tx["window"]
        tx["phase"] = "stage_message"
        self.focus_window(target)
        time.sleep(0.3)
        self._peek(
            "click",
            "--app",
            target["app"],
            "--window-id",
            str(target["window_id"]),
            "--coords",
            f"{self.config.input_x},{self.config.input_y}",
        )
        time.sleep(0.2)

        draft_text = ""
        for chunk in tx.get("chunks", []):
            compose = self.inspect_compose_state(target)
            if not compose.get("ok"):
                return self.freeze_tx(
                    tx,
                    compose.get("error_code", "ocr_failed"),
                    stderr=compose.get("stderr", ""),
                )
            tx["current_view"] = compose.get("view", "unknown_view")
            tx["current_contact"] = compose.get("current_contact", "__UNKNOWN__")
            if compose.get("search_focused") or compose.get("view") != "chat_detail":
                return self.freeze_tx(
                    tx,
                    "input_focus_lost",
                    current_view=compose.get("view"),
                    current_contact=compose.get("current_contact"),
                    compose_state=compose,
                )
            type_result = self._peek("type", chunk, "--app", target["app"])
            if not type_result.ok:
                return self.freeze_tx(tx, "send_failed", stderr=type_result.stderr)
            time.sleep(self.config.send_chunk_delay_ms / 1000)
            draft_text += chunk
            compose_after = self.inspect_compose_state(target)
            if not compose_after.get("ok"):
                return self.freeze_tx(
                    tx,
                    compose_after.get("error_code", "ocr_failed"),
                    stderr=compose_after.get("stderr", ""),
                )
            tx["current_view"] = compose_after.get("view", "unknown_view")
            tx["current_contact"] = compose_after.get("current_contact", "__UNKNOWN__")
            observed = compose_after.get("draft_text", "")
            if compose_after.get("search_focused") or compose_after.get("view") != "chat_detail":
                return self.freeze_tx(
                    tx,
                    "search_mode_active",
                    current_view=compose_after.get("view"),
                    current_contact=compose_after.get("current_contact"),
                    compose_state=compose_after,
                )
            if draft_text and observed and draft_text.strip() not in observed:
                return self.freeze_tx(
                    tx,
                    "draft_mismatch",
                    expected_draft=draft_text,
                    observed_draft=observed,
                )
            tx["verified_chunks"] = tx.get("verified_chunks", []) + [chunk]
            tx["draft_text"] = draft_text
            self.save_tx(tx)
        return tx

    def commit_send(self, tx_id: str) -> Dict[str, Any]:
        tx = self.load_tx(tx_id)
        if tx.get("error_code") == "tx_not_found":
            return tx
        tx = self.verify_send(tx_id)
        if not tx.get("ok"):
            return tx
        tx = self.stage_message_chunks(tx)
        if not tx.get("ok"):
            return tx

        tx["phase"] = "commit_send"
        target = tx["window"]
        compose = self.inspect_compose_state(target)
        if not compose.get("ok"):
            return self.freeze_tx(
                tx,
                compose.get("error_code", "ocr_failed"),
                stderr=compose.get("stderr", ""),
            )
        latest_signature = message_signature(compose.get("last_incoming_message", "__NONE__"))
        baseline_signature = tx.get("baseline_signature")
        tx["current_incoming_message"] = compose.get("last_incoming_message")
        tx["current_signature"] = latest_signature
        tx["current_view"] = compose.get("view", "unknown_view")
        tx["current_contact"] = compose.get("current_contact", "__UNKNOWN__")
        if latest_signature != baseline_signature:
            return self.freeze_tx(
                tx,
                "new_incoming_message",
                baseline_incoming_message=tx.get("baseline_incoming_message"),
                current_incoming_message=compose.get("last_incoming_message"),
                current_view=compose.get("view"),
                current_contact=compose.get("current_contact"),
            )
        press_result = self._peek("press", "return", "--app", target["app"])
        if not press_result.ok:
            return self.freeze_tx(tx, "send_failed", stderr=press_result.stderr)
        time.sleep(0.4)
        compose_after_send = self.inspect_compose_state(target)
        if not compose_after_send.get("ok"):
            return self.freeze_tx(
                tx,
                compose_after_send.get("error_code", "verify_sent_failed"),
                stderr=compose_after_send.get("stderr", ""),
            )
        tx["current_view"] = compose_after_send.get("view", "unknown_view")
        tx["current_contact"] = compose_after_send.get("current_contact", "__UNKNOWN__")
        if compose_after_send.get("search_focused") or compose_after_send.get("view") != "chat_detail":
            return self.freeze_tx(
                tx,
                "verify_sent_failed",
                current_view=compose_after_send.get("view"),
                current_contact=compose_after_send.get("current_contact"),
                compose_state=compose_after_send,
            )
        observed_after_send = compose_after_send.get("draft_text", "")
        if observed_after_send.strip():
            return self.freeze_tx(
                tx,
                "draft_not_cleared",
                expected_cleared_text=tx.get("draft_text"),
                observed_draft=observed_after_send,
            )
        tx["phase"] = "verify_sent"
        tx["status"] = "sent"
        tx["ok"] = True
        tx["compose_state"] = json_safe(compose_after_send)
        self.save_tx(tx)
        return tx

    def inspect_target(self) -> Dict[str, Any]:
        return self.session_current()

    def inspect_input(self) -> Dict[str, Any]:
        runtime = self._platform_health_check()
        target = runtime.get("window")
        return self.inspect_compose_state(target=target) if target else runtime

    def inspect_search(self) -> Dict[str, Any]:
        payload = self.inspect_input()
        if payload.get("ok"):
            return {
                "ok": True,
                "phase": payload.get("phase"),
                "search_focused": payload.get("search_focused", False),
                "view": payload.get("view"),
                "current_view": payload.get("view"),
                "current_contact": payload.get("current_contact"),
                "recommended_next_step": payload.get("recommended_next_step"),
            }
        return payload

    def inspect_last_incoming(self) -> Dict[str, Any]:
        runtime = self._platform_health_check()
        target = runtime.get("window")
        return self.read_last_incoming_message(target=target) if target else runtime

    def send_text(self, text: str, name: Optional[str] = None) -> Dict[str, Any]:
        if not name:
            return self._top_level_health_failure(
                "target_mismatch",
                phase="prepare_send",
                expected_contact=None,
                opened_contact="__UNKNOWN__",
            )
        prepared = self.prepare_send(name, text)
        if not prepared.get("ok"):
            return prepared
        committed = self.commit_send(prepared["tx_id"])
        if committed.get("ok"):
            return {
                "ok": True,
                "tx_id": committed["tx_id"],
                "phase": committed.get("phase"),
                "sent": text,
                "target_contact": name,
                "window": committed.get("window"),
                "current_view": committed.get("current_view"),
                "current_contact": committed.get("current_contact"),
                "recommended_next_step": None,
            }
        return committed

    def _build_health_change_job(
        self,
        watcher: str,
        *,
        previous_state: Dict[str, Any],
        current_state: Dict[str, Any],
        status: str,
    ) -> Dict[str, Any]:
        return self.enqueue_job(
            job_type="watcher.health.changed",
            source=f"watcher:{watcher}",
            cursor=current_state.get("cursor", previous_state.get("cursor", 0)),
            signature=current_state.get("signature", previous_state.get("signature", "")),
            payload={
                "watcher": watcher,
                "status": status,
                "previous_healthy": previous_state.get("healthy", True),
                "current_healthy": current_state.get("healthy", True),
                "state": current_state,
            },
        )

    def _build_change_job(
        self,
        watcher: str,
        *,
        previous_state: Dict[str, Any],
        payload: Dict[str, Any],
        cursor: int,
    ) -> Optional[Dict[str, Any]]:
        job_type = WATCHER_CHANGE_JOB_TYPES[watcher]
        signature = payload.get("signature", "")
        if watcher == "unread":
            return self.enqueue_job(
                job_type=job_type,
                source="watcher:unread",
                cursor=cursor,
                signature=signature,
                payload={
                    "watcher": watcher,
                    "view": payload.get("view"),
                    "items": payload.get("items", []),
                    "app_has_unread_badge": payload.get("app_has_unread_badge", False),
                    "app_unread_badge_count": payload.get("app_unread_badge_count"),
                    "summary": payload.get("summary", {}),
                    "available": payload.get("available", False),
                },
            )
        if watcher == "chat_visible":
            previous_messages = (
                previous_state.get("payload", {}).get("messages", [])
                if isinstance(previous_state.get("payload"), dict)
                else []
            )
            diff = diff_group_messages(previous_messages, payload.get("messages", []))
            if not diff["added_messages"]:
                return None
            return self.enqueue_job(
                job_type=job_type,
                source="watcher:chat_visible",
                cursor=cursor,
                signature=signature,
                payload={
                    "watcher": watcher,
                    "view": payload.get("view"),
                    "current_contact": payload.get("current_contact"),
                    "messages": payload.get("messages", []),
                    **diff,
                },
            )
        unseen_items = [item for item in payload.get("items", []) if not item.get("seen")]
        if not unseen_items:
            return None
        job = self.enqueue_job(
            job_type=job_type,
            source="watcher:moments",
            cursor=cursor,
            signature=signature,
            payload={
                "watcher": watcher,
                "view": payload.get("view"),
                "items": unseen_items,
            },
        )
        self.mark_moments_seen(item["card_signature"] for item in unseen_items)
        return job

    def process_watcher_result(
        self,
        watcher: str,
        payload: Dict[str, Any],
        *,
        enqueue_jobs: bool,
    ) -> Dict[str, Any]:
        previous_state = self.load_watcher_state(watcher)
        state = dict(previous_state)
        now = now_iso()
        state["watcher"] = watcher
        state["enabled"] = True
        state["phase"] = payload.get("phase", WATCHER_PHASES[watcher])
        state["last_checked_at"] = now
        jobs: List[Dict[str, Any]] = []

        if not payload.get("ok"):
            state["available"] = False
            state["last_error_at"] = now
            state["last_error_code"] = payload.get("error_code")
            state["recommended_next_step"] = payload.get("recommended_next_step")
            state["consecutive_failures"] = int(previous_state.get("consecutive_failures", 0)) + 1
            state["healthy"] = state["consecutive_failures"] < self.config.watcher_failure_threshold
            if enqueue_jobs and previous_state.get("healthy", True) and not state["healthy"]:
                jobs.append(
                    self._build_health_change_job(
                        watcher,
                        previous_state=previous_state,
                        current_state=state,
                        status="degraded",
                    )
                )
            self.save_watcher_state(watcher, state)
            return {"state": state, "payload": payload, "jobs": jobs}

        available = bool(payload.get("available", False))
        state["available"] = available
        state["healthy"] = True
        state["consecutive_failures"] = 0
        state["last_error_code"] = None
        state["recommended_next_step"] = payload.get("recommended_next_step")
        state["payload"] = json_safe(payload)
        if available:
            state["last_success_at"] = now
        signature = payload.get("signature", "")
        changed = available and signature != previous_state.get("signature", "")
        if changed:
            state["cursor"] = int(previous_state.get("cursor", 0)) + 1
            state["signature"] = signature
        if enqueue_jobs and not previous_state.get("healthy", True):
            jobs.append(
                self._build_health_change_job(
                    watcher,
                    previous_state=previous_state,
                    current_state=state,
                    status="recovered",
                )
            )
        if enqueue_jobs and changed:
            job = self._build_change_job(
                watcher,
                previous_state=previous_state,
                payload=payload,
                cursor=state["cursor"],
            )
            if job:
                jobs.append(job)
        self.save_watcher_state(watcher, state)
        return {"state": state, "payload": payload, "jobs": jobs}

    def snapshot(self, watches: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        requested = set(watches or {"session", *KNOWN_WATCHERS})
        health = self.health_check()
        runtime = health.get("runtime", {})
        session = self.session_current() if "session" in requested and runtime.get("ok") else None
        current_view = (session or {}).get("view", "unknown_view")
        current_contact = (session or {}).get("current_contact", "__UNKNOWN__")
        target = runtime.get("window")
        snapshot = {
            "checked_at": now_iso(),
            "health": health,
            "session": session,
            "daemon": health.get("daemon"),
            "worker": health.get("worker"),
            "watchers": health.get("watchers"),
            "queues": health.get("queues"),
        }
        if "unread" in requested:
            snapshot["unread"] = (
                self._collect_unread_snapshot(
                    target=target,
                    current_view=current_view,
                    current_contact=current_contact,
                )
                if runtime.get("ok")
                else self._watcher_failure("unread", runtime.get("error_code", "window_not_found"))
            )
        if "chat_visible" in requested:
            snapshot["chat_visible"] = (
                self._collect_chat_visible_snapshot(target=target, session=session)
                if runtime.get("ok")
                else self._watcher_failure(
                    "chat_visible",
                    runtime.get("error_code", "window_not_found"),
                )
            )
        if "moments" in requested:
            snapshot["moments"] = (
                self._collect_moments_snapshot(target=target, session=session)
                if runtime.get("ok")
                else self._watcher_failure("moments", runtime.get("error_code", "window_not_found"))
            )
        return snapshot

    def daemon_cycle(
        self,
        *,
        watches: Iterable[str],
        enqueue_jobs: bool = True,
    ) -> Dict[str, Any]:
        requested = set(watches) & set(KNOWN_WATCHERS)
        runtime = self._platform_health_check()
        session = self.session_current() if runtime.get("ok") else None
        self.touch_daemon_state(watches=requested, status="running")

        snapshot: Dict[str, Any] = {
            "checked_at": now_iso(),
            "session": session,
            "jobs_enqueued": [],
        }
        watcher_states: Dict[str, Any] = {}
        for watcher in requested:
            if watcher == "unread":
                payload = (
                    self._collect_unread_snapshot(
                        target=runtime.get("window"),
                        current_view=(session or {}).get("view", "unknown_view"),
                        current_contact=(session or {}).get("current_contact", "__UNKNOWN__"),
                    )
                    if runtime.get("ok")
                    else self._watcher_failure(
                        "unread",
                        runtime.get("error_code", "window_not_found"),
                    )
                )
            elif watcher == "chat_visible":
                payload = (
                    self._collect_chat_visible_snapshot(
                        target=runtime.get("window"),
                        session=session,
                    )
                    if runtime.get("ok")
                    else self._watcher_failure(
                        "chat_visible",
                        runtime.get("error_code", "window_not_found"),
                    )
                )
            else:
                payload = (
                    self._collect_moments_snapshot(
                        target=runtime.get("window"),
                        session=session,
                    )
                    if runtime.get("ok")
                    else self._watcher_failure(
                        "moments",
                        runtime.get("error_code", "window_not_found"),
                    )
                )
            processed = self.process_watcher_result(watcher, payload, enqueue_jobs=enqueue_jobs)
            snapshot[watcher] = payload
            watcher_states[watcher] = processed["state"]
            snapshot["jobs_enqueued"].extend(job["job_id"] for job in processed["jobs"])

        snapshot["watchers"] = self.load_all_watcher_states()
        snapshot["queues"] = self.queue_status()
        snapshot["daemon"] = self.daemon_status()
        snapshot["worker"] = self.worker_status()
        snapshot["health"] = self.health_check()
        self.save_state(snapshot)
        return snapshot

    def run_watch_cycle(
        self,
        watcher: str,
        *,
        enqueue_jobs: bool = False,
    ) -> Dict[str, Any]:
        runtime = self._platform_health_check()
        session = self.session_current() if runtime.get("ok") else None
        if watcher == "unread":
            payload = (
                self._collect_unread_snapshot(
                    target=runtime.get("window"),
                    current_view=(session or {}).get("view", "unknown_view"),
                    current_contact=(session or {}).get("current_contact", "__UNKNOWN__"),
                )
                if runtime.get("ok")
                else self._watcher_failure(
                    "unread",
                    runtime.get("error_code", "window_not_found"),
                )
            )
        elif watcher == "chat_visible":
            payload = (
                self._collect_chat_visible_snapshot(
                    target=runtime.get("window"),
                    session=session,
                )
                if runtime.get("ok")
                else self._watcher_failure(
                    "chat_visible",
                    runtime.get("error_code", "window_not_found"),
                )
            )
        elif watcher == "moments":
            payload = (
                self._collect_moments_snapshot(
                    target=runtime.get("window"),
                    session=session,
                )
                if runtime.get("ok")
                else self._watcher_failure(
                    "moments",
                    runtime.get("error_code", "window_not_found"),
                )
            )
        else:
            raise ValueError(f"unsupported watcher: {watcher}")
        processed = self.process_watcher_result(watcher, payload, enqueue_jobs=enqueue_jobs)
        state = processed["state"]
        enriched = dict(payload)
        if watcher == "unread":
            enriched["cursor"] = state.get("cursor", 0)
        elif watcher == "chat_visible":
            enriched["snapshot_signature"] = payload.get("signature", "")
            enriched["snapshot_cursor"] = state.get("cursor", 0)
        elif watcher == "moments":
            enriched["cursor"] = state.get("cursor", 0)
        return {
            "payload": enriched,
            "watcher_state": state,
            "jobs": processed["jobs"],
            "session": session,
        }

    def acquire_lock(self) -> None:
        self.config.state_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.config.lock_dir.mkdir()
        except FileExistsError:
            pid_path = self.config.lock_dir / "pid"
            if pid_path.exists():
                existing_pid = pid_path.read_text().strip()
                if existing_pid.isdigit():
                    try:
                        os.kill(int(existing_pid), 0)
                    except OSError:
                        shutil.rmtree(self.config.lock_dir, ignore_errors=True)
                        self.config.lock_dir.mkdir()
                    else:
                        raise RuntimeError(f"daemon already running with pid {existing_pid}")
        (self.config.lock_dir / "pid").write_text(str(os.getpid()))

    def release_lock(self) -> None:
        payload = self.load_daemon_state()
        if payload:
            payload["status"] = "stopped"
            payload["updated_at"] = now_iso()
            self.save_daemon_state(payload)
        shutil.rmtree(self.config.lock_dir, ignore_errors=True)
