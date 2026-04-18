import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from wechat_ops.config import WeChatOpsConfig
from wechat_ops.runtime import (
    bounds_for_window,
    canonicalize_json,
    classify_nav_and_session_badges,
    contacts_match,
    detect_badge_components,
    detect_conversation_badges,
    detect_nav_chat_badge,
    detect_sidebar_badges,
    diff_group_messages,
    extract_ai_section,
    extract_group_messages_from_ocr_payload,
    extract_json_fragment,
    extract_unread_from_ocr_payload,
    first_window_target,
    group_messages_signature,
    infer_badge_count_from_image,
    moments_feed_signature,
    likely_contact_text,
    normalize_contact_name,
    normalize_group_messages,
    normalize_moments_items,
    normalize_unread_items,
    parse_hid_idle_time_seconds,
    parse_chat_time_like,
    parse_permissions_output,
    recommended_next_step_for_error,
    sidebar_conversation_candidates,
    sidebar_row_infos_from_ocr_payload,
    unread_signature,
    WeChatOpsRuntime,
)
from wechat_ops.worker import WeChatOpsWorker


UTC = timezone.utc
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    return json.loads((FIXTURES_DIR / name).read_text())


class StubRuntime(WeChatOpsRuntime):
    def __init__(self, config: WeChatOpsConfig) -> None:
        super().__init__(config)
        self.platform_payload = {
            "ok": True,
            "error_code": None,
            "phase": "health_check",
            "checked_at": "2026-03-26T00:00:00+00:00",
            "account_id": config.account_id,
            "permissions": {"healthy": True},
            "window": {"app": "微信", "window_id": 180, "title": "微信"},
            "peekaboo_bin": config.peekaboo_bin,
        }

    def _platform_health_check(self) -> dict:
        return dict(self.platform_payload)


class RuntimeHelpersTest(unittest.TestCase):
    def test_parse_permissions_output(self):
        payload = parse_permissions_output(
            "Source: Peekaboo Bridge\n"
            "Screen Recording (Required): Granted\n"
            "Accessibility (Required): Granted\n"
        )
        self.assertTrue(payload["healthy"])
        self.assertEqual(payload["source"], "Peekaboo Bridge")

    def test_first_window_target_prefers_titled_main_window(self):
        payload = {
            "data": {
                "windows": [
                    {"window_id": 111, "title": "", "index": 1, "isOnScreen": True, "isMinimized": False, "bounds": [[0, 0], [780, 969]]},
                    {"window_id": 173, "title": "微信", "index": 0, "isOnScreen": True, "isMinimized": False, "bounds": [[1140, 25], [780, 969]]},
                ]
            }
        }
        self.assertEqual(first_window_target(payload), ("微信", 173))

    def test_bounds_for_window(self):
        target = {
            "window_id": 173,
            "windows": [
                {"windowID": 173, "bounds": [[1140, 25], [780, 969]]},
            ],
        }
        self.assertEqual(bounds_for_window(target), (1140, 25, 780, 969))

    def test_extract_ai_section(self):
        text = "🤖 AI Analysis\n优质跨境服务群2(488)\n\n🔍 Element Summary\n..."
        self.assertEqual(extract_ai_section(text), "优质跨境服务群2(488)")

    def test_extract_json_fragment(self):
        payload = extract_json_fragment('prefix [{"name":"A","unread_count":2}] suffix')
        self.assertEqual(payload[0]["name"], "A")

    def test_normalize_contact_name_and_match(self):
        self.assertEqual(normalize_contact_name(" 优质跨境服务群2 (488) "), "优质跨境服务群2(488)")
        self.assertTrue(contacts_match("优质跨境服务群2(488)", "优质跨境服务群2 (488)"))
        self.assertFalse(contacts_match("KentZ", "KentZ-客户群"))
        self.assertFalse(likely_contact_text(".？"))

    def test_parse_hid_idle_time_seconds(self):
        text = '    | | |   "HIDIdleTime" = 21693971666'
        value = parse_hid_idle_time_seconds(text)
        self.assertIsNotNone(value)
        self.assertGreater(value, 21.0)

    def test_parse_chat_time_like(self):
        self.assertTrue(parse_chat_time_like("昨天 10:07"))
        self.assertTrue(parse_chat_time_like("星期二."))
        self.assertTrue(parse_chat_time_like("03/17"))
        self.assertTrue(parse_chat_time_like("昨大 23:41"))
        self.assertFalse(parse_chat_time_like("Eason Chen Sarl"))

    def test_normalize_unread_items(self):
        items = normalize_unread_items(
            [
                {"name": " B群 ", "unread_badge_count": "2", "has_unread_badge": True, "preview": " hi "},
                {"name": "A群", "has_unread_badge": True, "preview": ""},
            ]
        )
        self.assertEqual(items[0]["name"], "A群")
        self.assertEqual(items[1]["unread_count"], 2)
        self.assertTrue(items[0]["has_unread_badge"])
        self.assertEqual(items[1]["preview_text"], "hi")

    def test_unread_signature_stable(self):
        left = [{"name": "B群", "unread_badge_count": "2", "has_unread_badge": True, "preview": "hi"}]
        right = [{"preview_text": "hi", "unread_count": 2, "has_unread_badge": True, "name": "B群"}]
        self.assertEqual(unread_signature(left), unread_signature(right))

    def test_normalize_moments_items_and_signature(self):
        items = normalize_moments_items(
            [{"author": "A", "summary": "  hi ", "has_media": 1}, {"author": None}]
        )
        self.assertEqual(items[0]["summary"], "hi")
        self.assertIn("card_signature", items[0])
        self.assertNotEqual(moments_feed_signature(items), moments_feed_signature(list(reversed(items))))

    def test_diff_group_messages(self):
        previous = normalize_group_messages(
            [{"speaker": "A", "time": "12:00", "text": "old"}, {"speaker": "B", "time": "12:01", "text": "stay"}]
        )
        current = normalize_group_messages(
            [{"speaker": "B", "time": "12:01", "text": "stay"}, {"speaker": "C", "time": "12:02", "text": "new"}]
        )
        diff = diff_group_messages(previous, current)
        self.assertEqual(diff["added_messages"][0]["speaker"], "C")
        self.assertEqual(diff["removed_messages"][0]["speaker"], "A")
        self.assertTrue(diff["window_shift"])

    def test_recommended_next_step_mapping(self):
        self.assertEqual(recommended_next_step_for_error("human_active"), "retry_after_idle")
        self.assertEqual(recommended_next_step_for_error("new_incoming_message"), "reprepare_send")
        self.assertEqual(recommended_next_step_for_error("something_else"), "escalate_to_developer")

    def test_split_message_chunks_keeps_url_whole(self):
        from wechat_ops.runtime import split_message_chunks

        chunks = split_message_chunks(
            "哥们，刚做了个调研，感觉挺有意思的，分享给你瞅瞅 👉 https://gemini.google.com/share/44970cbabb51",
            24,
        )
        self.assertTrue(any(chunk.startswith("https://gemini.google.com/") for chunk in chunks))
        self.assertTrue(all(len(chunk) <= 60 for chunk in chunks))

    def test_extract_group_messages_from_ocr_payload(self):
        payload = load_fixture("group_chat_content_ocr.json")
        messages = extract_group_messages_from_ocr_payload(payload)
        self.assertEqual(messages[0]["speaker"], "美企 WayfairChoi")
        self.assertEqual(messages[0]["time"], "12:02")
        self.assertIn("新蛋Newegg", messages[0]["text"])

    def test_extract_group_messages_from_private_chat_does_not_treat_time_as_speaker(self):
        payload = load_fixture("private_chat_content_ocr.json")
        messages = extract_group_messages_from_ocr_payload(payload, cropped=True)
        self.assertEqual(messages, [])

    def test_extract_unread_from_ocr_payload(self):
        payload = {
            "lines": [
                {"text": "张三李四", "boundingBox": [0.15, 0.90, 0.08, 0.018]},
                {"text": "昨天 23:47", "boundingBox": [0.30, 0.90, 0.07, 0.01]},
                {"text": "最近整了个深度调研，发你看看", "boundingBox": [0.15, 0.88, 0.22, 0.014]},
                {"text": "2", "boundingBox": [0.03, 0.81, 0.03, 0.02]},
                {"text": "Jessie 耐思跨境", "boundingBox": [0.15, 0.83, 0.13, 0.014]},
                {"text": "03/17", "boundingBox": [0.33, 0.83, 0.04, 0.01]},
                {"text": "这个是过期了，注册时可以用…", "boundingBox": [0.15, 0.81, 0.22, 0.014]},
                {"text": "优质跨境服务群2", "boundingBox": [0.15, 0.48, 0.14, 0.018]},
                {"text": "23:42", "boundingBox": [0.33, 0.48, 0.04, 0.01]},
                {"text": "［3 条］安静：稀缺资源..", "boundingBox": [0.15, 0.46, 0.16, 0.014]},
            ]
        }
        unread = extract_unread_from_ocr_payload(payload)
        self.assertTrue(unread["available"])
        self.assertEqual(unread["items"][0]["name"], "Jessie 耐思跨境")
        self.assertEqual(unread["items"][0]["unread_count"], 2)
        self.assertEqual(group_messages_signature([]), "[]")

    def test_extract_unread_from_real_sidebar_layout(self):
        payload = load_fixture("unread_sidebar_selected_and_inline_time.json")
        unread = extract_unread_from_ocr_payload(payload)
        self.assertTrue(unread["available"])

    def test_sidebar_conversation_candidates_keep_preview_row(self):
        payload = {
            "lines": [
                {"text": "YYY服务商", "boundingBox": [0.421, 0.923, 0.20, 0.016]},
                {"text": "星期一.", "boundingBox": [0.826, 0.928, 0.09, 0.012]},
                {"text": "截图", "boundingBox": [0.427, 0.904, 0.06, 0.012]},
            ]
        }
        rows = sidebar_row_infos_from_ocr_payload(payload)
        conversations = sidebar_conversation_candidates(rows)
        self.assertEqual(conversations[0]["name"], "YYY服务商")
        self.assertEqual(conversations[0]["preview"], "截图")

    def test_sidebar_conversation_candidates_allow_selected_row_without_time(self):
        payload = {
            "lines": [
                {"text": "KentZ", "boundingBox": [0.427, 0.928, 0.20, 0.016]},
                {"text": "测试", "boundingBox": [0.427, 0.905, 0.10, 0.012]},
                {"text": "星期二.", "boundingBox": [0.826, 0.857, 0.09, 0.012]},
                {"text": "张三李四", "boundingBox": [0.421, 0.857, 0.20, 0.016]},
            ]
        }
        rows = sidebar_row_infos_from_ocr_payload(payload)
        conversations = sidebar_conversation_candidates(rows)
        self.assertEqual(conversations[0]["name"], "KentZ")
        self.assertEqual(conversations[0]["preview"], "测试")

    def test_sidebar_conversation_candidates_strip_inline_time_from_title(self):
        payload = load_fixture("unread_sidebar_selected_and_inline_time.json")
        rows = sidebar_row_infos_from_ocr_payload(payload)
        conversations = sidebar_conversation_candidates(rows)
        named = {item["name"]: item for item in conversations}
        self.assertEqual(named["AA汽车出口资源"]["time"], "昨天 23:52")
        self.assertEqual(named["AA汽车出口资源"]["preview"], "［999+条］专供清关手续合⋯这")
        self.assertEqual(named["KentZ"]["preview"], "测试")

    def test_replay_fixture_group_chat_kind(self):
        payload = load_fixture("group_chat_content_ocr.json")
        messages = normalize_group_messages(extract_group_messages_from_ocr_payload(payload))
        self.assertEqual(messages[0]["speaker"], "美企 WayfairChoi")

    def test_group_message_wrapped_short_line_stays_in_body(self):
        payload = {
            "lines": [
                {"text": "10:07", "boundingBox": [0.66, 0.84, 0.05, 0.01]},
                {"text": "美客多沃尔玛跨境本土", "boundingBox": [0.47, 0.80, 0.18, 0.016]},
                {"text": "1：新蛋三站点，PP迁移，已搬家，欢", "boundingBox": [0.48, 0.77, 0.30, 0.018]},
                {"text": "迎来询", "boundingBox": [0.48, 0.75, 0.08, 0.018]},
                {"text": "2：接沃尔玛经理店代入驻，3.5万SKU", "boundingBox": [0.48, 0.73, 0.30, 0.018]},
            ]
        }
        messages = extract_group_messages_from_ocr_payload(payload)
        self.assertEqual(messages[0]["speaker"], "美客多沃尔玛跨境本土")
        self.assertIn("迎来询", messages[0]["text"])

    def test_replay_fixture_private_chat_kind(self):
        payload = load_fixture("private_chat_content_ocr.json")
        messages = normalize_group_messages(extract_group_messages_from_ocr_payload(payload, cropped=True))
        self.assertEqual(messages, [])

    def test_detect_sidebar_badges(self):
        from PIL import Image, ImageDraw

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sidebar.png"
            image = Image.new("RGB", (356, 965), (245, 245, 245))
            draw = ImageDraw.Draw(image)
            draw.ellipse((64, 86, 79, 101), fill=(232, 74, 74))
            image.save(path)

            badges = detect_sidebar_badges(path)
            self.assertEqual(len(badges), 1)
            self.assertGreater(badges[0]["center_y"], 0.88)

    def test_detect_sidebar_badges_ignores_large_red_avatar_blocks(self):
        from PIL import Image, ImageDraw

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sidebar.png"
            image = Image.new("RGB", (356, 965), (245, 245, 245))
            draw = ImageDraw.Draw(image)
            draw.rectangle((100, 120, 140, 160), fill=(210, 70, 70))
            draw.ellipse((64, 86, 79, 101), fill=(232, 74, 74))
            image.save(path)

            badges = detect_sidebar_badges(path)
            self.assertEqual(len(badges), 1)
            self.assertLess(badges[0]["box_width"], 20)

    def test_detect_nav_chat_badge(self):
        badges = [
            {"center_x": 0.82, "center_y": 0.86},
            {"center_x": 0.30, "center_y": 0.50},
        ]
        badge = detect_nav_chat_badge(badges)
        self.assertEqual(badge["center_x"], 0.82)

    def test_detect_conversation_badges(self):
        badges = [
            {"center_x": 0.82, "center_y": 0.86},
            {"center_x": 0.22, "center_y": 0.92},
            {"center_x": 0.18, "center_y": 0.60},
        ]
        detected = detect_conversation_badges(badges)
        self.assertEqual(len(detected), 2)
        self.assertGreater(detected[0]["center_y"], detected[1]["center_y"])

    def test_classify_nav_and_session_badges_separates_app_and_session_badges(self):
        badges = [
            {"center_x": 0.82, "center_y": 0.86},
            {"center_x": 0.22, "center_y": 0.92},
        ]
        classified = classify_nav_and_session_badges(badges)
        self.assertEqual(classified["app_badge"]["center_x"], 0.82)
        self.assertEqual(len(classified["session_badges"]), 1)

    def test_infer_badge_count_from_image(self):
        from PIL import Image, ImageDraw, ImageFont

        font_path = "/System/Library/Fonts/SFNS.ttf"
        if not Path(font_path).exists():
            self.skipTest("SFNS.ttf not available")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "badge.png"
            image = Image.new("RGB", (80, 80), (255, 255, 255))
            draw = ImageDraw.Draw(image)
            draw.ellipse((10, 10, 70, 70), fill=(232, 74, 74))
            font = ImageFont.truetype(font_path, size=34)
            bbox = draw.textbbox((0, 0), "4", font=font)
            draw.text(
                ((80 - (bbox[2] - bbox[0])) / 2 - bbox[0], (80 - (bbox[3] - bbox[1])) / 2 - bbox[1]),
                "4",
                fill=(255, 255, 255),
                font=font,
            )
            image.save(path)
            self.assertEqual(infer_badge_count_from_image(path), 4)


class QueueAndWatcherTest(unittest.TestCase):
    def make_runtime(self):
        tmpdir = tempfile.TemporaryDirectory()
        config = WeChatOpsConfig.load(Path(tmpdir.name))
        runtime = StubRuntime(config)
        self.addCleanup(tmpdir.cleanup)
        return runtime

    def test_process_watcher_result_increments_cursor_and_enqueues_unread_job(self):
        runtime = self.make_runtime()
        payload = {
            "ok": True,
            "phase": "unread_snapshot",
            "current_view": "chat_detail",
            "current_contact": "KentZ",
            "view": "chat_detail",
            "available": True,
            "items": [{"name": "客户A", "unread_count": 2, "preview": "你好"}],
            "signature": unread_signature([{"name": "客户A", "unread_count": 2, "preview": "你好"}]),
            "recommended_next_step": None,
        }
        processed = runtime.process_watcher_result("unread", payload, enqueue_jobs=True)
        self.assertEqual(processed["state"]["cursor"], 1)
        self.assertEqual(len(processed["jobs"]), 1)
        self.assertEqual(processed["jobs"][0]["type"], "unread.snapshot.changed")

        same = runtime.process_watcher_result("unread", payload, enqueue_jobs=True)
        self.assertEqual(same["state"]["cursor"], 1)
        self.assertEqual(len(same["jobs"]), 0)

    def test_watcher_failure_threshold_emits_health_job(self):
        runtime = self.make_runtime()
        failure = {
            "ok": False,
            "error_code": "ocr_failed",
            "phase": "unread_snapshot",
            "current_view": "unknown_view",
            "current_contact": "__UNKNOWN__",
            "recommended_next_step": "run_health",
        }
        processed = None
        for _ in range(3):
            processed = runtime.process_watcher_result("unread", failure, enqueue_jobs=True)
        self.assertFalse(processed["state"]["healthy"])
        self.assertEqual(processed["state"]["consecutive_failures"], 3)
        self.assertEqual(processed["jobs"][0]["type"], "watcher.health.changed")

    def test_chat_visible_only_enqueues_when_added_messages_exist(self):
        runtime = self.make_runtime()
        first = {
            "ok": True,
            "phase": "chat_visible_snapshot",
            "current_view": "chat_detail",
            "current_contact": "优质跨境服务群2",
            "view": "chat_detail",
            "available": True,
            "messages": [{"speaker": "A", "time": "12:00", "text": "old"}],
            "signature": group_messages_signature([{"speaker": "A", "time": "12:00", "text": "old"}]),
            "recommended_next_step": None,
        }
        runtime.process_watcher_result("chat_visible", first, enqueue_jobs=False)
        second = {
            "ok": True,
            "phase": "chat_visible_snapshot",
            "current_view": "chat_detail",
            "current_contact": "优质跨境服务群2",
            "view": "chat_detail",
            "available": True,
            "messages": [
                {"speaker": "A", "time": "12:00", "text": "old"},
                {"speaker": "B", "time": "12:01", "text": "new"},
            ],
            "signature": group_messages_signature(
                [
                    {"speaker": "A", "time": "12:00", "text": "old"},
                    {"speaker": "B", "time": "12:01", "text": "new"},
                ]
            ),
            "recommended_next_step": None,
        }
        processed = runtime.process_watcher_result("chat_visible", second, enqueue_jobs=True)
        self.assertEqual(processed["jobs"][0]["payload"]["added_messages"][0]["speaker"], "B")

    def test_run_watch_cycle_returns_cursor_enriched_payload(self):
        runtime = self.make_runtime()
        runtime.session_current = lambda: {
            "ok": True,
            "view": "chat_list",
            "current_contact": "优质跨境服务群2",
            "window": {"app": "微信", "window_id": 180, "title": "微信"},
        }
        runtime._collect_unread_snapshot = lambda **_: {
            "ok": True,
            "phase": "unread_snapshot",
            "current_view": "chat_list",
            "current_contact": "优质跨境服务群2",
            "view": "chat_list",
            "available": True,
            "items": [{"name": "客户A", "unread_count": 1, "preview": "hi"}],
            "signature": unread_signature([{"name": "客户A", "unread_count": 1, "preview": "hi"}]),
            "recommended_next_step": None,
        }
        watch = runtime.run_watch_cycle("unread", enqueue_jobs=False)
        self.assertEqual(watch["payload"]["cursor"], 1)

    def test_daemon_cycle_snapshot_contains_new_runtime_sections(self):
        runtime = self.make_runtime()
        runtime.session_current = lambda: {
            "ok": True,
            "view": "chat_list",
            "current_contact": "优质跨境服务群2",
            "window": {"app": "微信", "window_id": 180, "title": "微信"},
        }
        runtime._collect_unread_snapshot = lambda **_: {
            "ok": True,
            "phase": "unread_snapshot",
            "current_view": "chat_list",
            "current_contact": "优质跨境服务群2",
            "view": "chat_list",
            "available": False,
            "items": [],
            "signature": "",
            "recommended_next_step": None,
        }
        runtime._collect_chat_visible_snapshot = lambda **_: {
            "ok": True,
            "phase": "chat_visible_snapshot",
            "current_view": "chat_detail",
            "current_contact": "优质跨境服务群2",
            "view": "chat_detail",
            "available": False,
            "messages": [],
            "signature": "",
            "recommended_next_step": None,
        }
        runtime._collect_moments_snapshot = lambda **_: {
            "ok": True,
            "phase": "moments_snapshot",
            "current_view": "chat_detail",
            "current_contact": "优质跨境服务群2",
            "view": "chat_detail",
            "available": False,
            "items": [],
            "feed_signature": "",
            "signature": "",
            "recommended_next_step": None,
        }
        snapshot = runtime.daemon_cycle(watches={"unread", "chat_visible", "moments"}, enqueue_jobs=False)
        self.assertIn("watchers", snapshot)
        self.assertIn("queues", snapshot)
        self.assertIn("jobs_enqueued", snapshot)

    def test_health_check_reports_watchers_and_queues(self):
        runtime = self.make_runtime()
        watcher_state = runtime.load_watcher_state("unread")
        watcher_state["healthy"] = False
        watcher_state["last_error_code"] = "ocr_failed"
        runtime.save_watcher_state("unread", watcher_state)
        runtime.save_daemon_state(
            {
                "pid": 123,
                "status": "running",
                "watches": ["unread"],
                "last_heartbeat_at": datetime.now(tz=UTC).isoformat(),
            }
        )
        runtime._write_json_file(
            runtime.config.worker_state_file,
            {
                "pid": 456,
                "status": "idle",
                "processed_jobs": 0,
                "last_heartbeat_at": datetime.now(tz=UTC).isoformat(),
            },
        )
        health = runtime.health_check()
        self.assertFalse(health["overall_healthy"])
        self.assertEqual(health["recommended_next_step"], "restart_daemon")
        self.assertIn("watchers", health)
        self.assertIn("queues", health)

    def test_daemon_status_not_healthy_when_explicitly_stopped(self):
        runtime = self.make_runtime()
        runtime.save_daemon_state(
            {
                "pid": 123,
                "status": "stopped",
                "watches": ["unread"],
                "last_heartbeat_at": datetime.now(tz=UTC).isoformat(),
            }
        )
        status = runtime.daemon_status()
        self.assertFalse(status["healthy"])
        self.assertEqual(status["status"], "stopped")

    def test_worker_status_not_healthy_when_explicitly_stopped(self):
        runtime = self.make_runtime()
        runtime._write_json_file(
            runtime.config.worker_state_file,
            {
                "pid": 456,
                "status": "stopped",
                "processed_jobs": 2,
                "last_heartbeat_at": datetime.now(tz=UTC).isoformat(),
            },
        )
        status = runtime.worker_status()
        self.assertFalse(status["healthy"])
        self.assertEqual(status["status"], "stopped")

    def test_worker_processes_job_and_writes_result(self):
        runtime = self.make_runtime()
        runtime.enqueue_job(
            job_type="unread.snapshot.changed",
            source="watcher:unread",
            cursor=1,
            signature="sig-1",
            payload={"items": [{"name": "客户A"}]},
        )
        worker = WeChatOpsWorker(runtime.config)
        rc = worker.run(once=True)
        self.assertEqual(rc, 0)
        result_files = list(runtime.config.results_pending_dir.glob("*.json"))
        self.assertEqual(len(result_files), 1)
        payload = json.loads(result_files[0].read_text())
        self.assertEqual(payload["type"], "unread.snapshot.changed")
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["payload"]["summary"]["unread_count"], 1)

    def test_worker_reclaims_stale_processing_job(self):
        runtime = self.make_runtime()
        created_at = datetime.now(tz=UTC).isoformat()
        stale_job = {
            "job_id": "stale-1",
            "type": "watcher.health.changed",
            "source": "watcher:unread",
            "created_at": created_at,
            "cursor": 1,
            "signature": "sig",
            "payload": {"watcher": "unread"},
            "retry_count": 0,
            "max_retries": 3,
            "claimed_at": (datetime.now(tz=UTC) - timedelta(seconds=120)).isoformat(),
        }
        runtime._write_json_file(runtime.config.jobs_processing_dir / "stale-1.json", stale_job)
        worker = WeChatOpsWorker(runtime.config)
        reclaimed = worker.reclaim_stale_processing()
        self.assertEqual(reclaimed, 1)
        self.assertTrue((runtime.config.jobs_pending_dir / "stale-1.json").exists())

    def test_cleanup_artifacts_removes_old_desktop_peekaboo_leaks_only(self):
        runtime = self.make_runtime()
        desktop_dir = runtime.config.root_dir / "fake-desktop"
        desktop_dir.mkdir(parents=True, exist_ok=True)
        runtime.config.desktop_dir = desktop_dir
        runtime.config.desktop_artifact_ttl_minutes = 15

        old_leak = desktop_dir / "peekaboo_see_old.png"
        old_leak.write_text("old")
        old_ts = (datetime.now(tz=UTC) - timedelta(minutes=30)).timestamp()
        os.utime(old_leak, (old_ts, old_ts))

        fresh_leak = desktop_dir / "peekaboo_see_fresh.png"
        fresh_leak.write_text("fresh")

        manual_file = desktop_dir / "截屏2026-03-28 13.00.00.png"
        manual_file.write_text("manual")
        os.utime(manual_file, (old_ts, old_ts))

        result = runtime.cleanup_artifacts()

        self.assertEqual(result["desktop_removed"], 1)
        self.assertFalse(old_leak.exists())
        self.assertTrue(fresh_leak.exists())
        self.assertTrue(manual_file.exists())


if __name__ == "__main__":
    unittest.main()
