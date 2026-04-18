#!/usr/bin/env python3
"""
小红书意向客户采集脚本 v2（基于 xiaohongshu-mcp）

用法：
  python3 collect_leads.py --keyword 法国公司注册
  python3 collect_leads.py --keyword VAT --max-notes 5 --dry-run
"""

import json
import subprocess
import argparse
import time
import sys
from datetime import datetime, timezone, timedelta

# ============================================================
# 配置
# ============================================================

MCP_URL = "http://localhost:18060/mcp"

# 同行/广告过滤词（昵称）
SPAM_NICK = [
    "跨境注册", "欧洲注册", "本土注册", "VAT代",
    "欧注通", "跨途", "欧美公司", "OUBO", "跨境服务",
    "代办", "一手", "跨境飞猪", "金刚跨境",
]

# 同行/广告过滤词（评论内容）
SPAM_CONTENT = [
    "独家", "货比三家", "线上线下合作", "均可办理",
    "欧美法仁", "一手资源", "私我", "加v", "加V",
    "威信", "➕微", "扫码", "报价单",
    "代办", "服务商推荐", "合作共赢", "佣金",
]

# 意向识别词（至少命中一个才保留）
INTENT_KEYWORDS = [
    "服务商", "推荐", "怎么", "办理", "咨询",
    "需要", "想", "多少钱", "费用", "哪家",
    "可以", "本土", "VAT", "流程", "注册",
    "入驻", "开店", "怎样", "求", "有没有",
    "我想", "我要", "多久", "资质", "哪里",
]

# ============================================================
# MCP 调用
# ============================================================

def call_mcp(tool_name: str, arguments: dict):
    payload = json.dumps([
        {"jsonrpc": "2.0", "method": "initialize",
         "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "echo", "version": "1.0"}}, "id": 1},
        {"jsonrpc": "2.0", "method": "tools/call",
         "params": {"name": tool_name, "arguments": arguments}, "id": 2}
    ], ensure_ascii=False)
    for attempt in range(3):
        try:
            result = subprocess.run(
                ["curl", "-s", "-X", "POST", MCP_URL,
                 "-H", "Content-Type: application/json; charset=utf-8",
                 "-d", payload],
                capture_output=True, text=True, timeout=90
            )
            responses = json.loads(result.stdout)
            for r in responses:
                if r.get("id") == 2:
                    if "error" in r:
                        raise RuntimeError(f"MCP error: {r['error']}")
                    content = r["result"]["content"][0]["text"]
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return content
            raise RuntimeError("No response from MCP")
        except subprocess.TimeoutExpired:
            if attempt < 2:
                print(f"    ⏱️ 超时，第 {attempt+2} 次重试...")
                time.sleep(3)
            else:
                raise

# ============================================================
# 过滤与分类
# ============================================================

def is_spam(nickname: str, content: str) -> bool:
    for kw in SPAM_NICK:
        if kw in nickname:
            return True
    for kw in SPAM_CONTENT:
        if kw in content:
            return True
    return False

def has_intent(content: str) -> bool:
    return any(kw in content for kw in INTENT_KEYWORDS)

def classify_demand(content: str) -> str:
    if any(k in content for k in ["服务商", "推荐", "哪家", "哪里", "找"]):
        return "求服务商"
    elif any(k in content for k in ["资质", "护照", "法人", "材料", "资料"]):
        return "资质问题"
    elif any(k in content for k in ["费用", "多少钱", "价格", "VAT", "税", "开店", "入驻", "流程"]):
        return "开店咨询"
    else:
        return "开店咨询"

def assess_priority(content: str, demand_type: str) -> str:
    if demand_type == "求服务商" or any(k in content for k in ["联系", "私聊", "合作", "怎么联系"]):
        return "高"
    elif len(content) > 20:
        return "中"
    else:
        return "低"

def identify_persona(content: str) -> str:
    """判断评论者身份，决定回复人设"""
    if any(k in content for k in ["服务商", "推荐", "哪家", "找"]):
        return "明确找服务商"
    elif any(k in content for k in ["资质", "审核", "被拒", "卡"]):
        return "有经验但卡住"
    elif any(k in content for k in ["怎么", "怎样", "如何", "想开", "想注册"]):
        return "刚起步新卖家"
    elif any(k in content for k in ["坑", "骗", "差", "烂", "失败", "亏"]):
        return "吐槽平台"
    else:
        return "刚起步新卖家"

# ============================================================
# 主流程
# ============================================================

def is_within_days(create_time, days: int = 60) -> bool:
    """判断评论是否在 days 天内（create_time 为毫秒时间戳或空）"""
    if not create_time:
        return True  # 没有时间信息，不过滤
    try:
        ts = int(create_time) / 1000
        comment_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
        return comment_dt >= cutoff
    except Exception:
        return True


def collect(keyword: str, max_notes: int = 10, days: int = 60) -> list:
    print(f"\n🔍 搜索关键词：{keyword}")

    # Step 1: 搜索笔记
    search_result = call_mcp("search_feeds", {
        "keyword": keyword,
        "filters": {
            "sort_by": "最多评论",
            "publish_time": "半年内"
        }
    })

    feeds = search_result.get("feeds", [])[:max_notes]
    print(f"📄 获取笔记：{len(feeds)} 篇")

    leads = []
    skipped_spam = 0
    skipped_no_intent = 0
    skipped_author = 0

    for i, feed in enumerate(feeds):
        feed_id = feed.get("id")
        xsec_token = feed.get("xsecToken")
        note_card = feed.get("noteCard", {})
        title = note_card.get("displayTitle") or note_card.get("title", "")
        author_id = note_card.get("user", {}).get("userId", "")
        author_name = note_card.get("user", {}).get("nickname", "")

        print(f"\n  [{i+1}/{len(feeds)}] {title[:30] or feed_id}")

        # Step 2: 获取评论
        try:
            detail = call_mcp("get_feed_detail", {
                "feed_id": feed_id,
                "xsec_token": xsec_token,
                "load_all_comments": True,
                "limit": 50
            })
        except Exception as e:
            print(f"    ⚠️ 获取详情失败：{e}")
            time.sleep(1)
            continue

        comments = []
        if isinstance(detail, dict):
            data = detail.get("data", detail)
            comments_block = data.get("comments", {})
            if isinstance(comments_block, dict):
                comments = comments_block.get("list", [])
            elif isinstance(comments_block, list):
                comments = comments_block
        
        print(f"    💬 评论数：{len(comments)}")

        for comment in comments:
            user_info = comment.get("userInfo", {})
            user_id = user_info.get("userId", "") or comment.get("userId", "")
            nickname = user_info.get("nickname", "") or user_info.get("nickName", "") or comment.get("nickname", "")
            content = comment.get("content", "").strip()
            create_time = comment.get("createTime") or comment.get("time", "")

            if not content or len(content) < 5:
                continue

            # 时间过滤（60天内）
            if not is_within_days(create_time, days):
                continue

            # 跳过作者自己
            if user_id == author_id:
                skipped_author += 1
                continue

            # 同行过滤
            if is_spam(nickname, content):
                skipped_spam += 1
                continue

            # 意向过滤
            if not has_intent(content):
                skipped_no_intent += 1
                continue

            demand_type = classify_demand(content)
            priority = assess_priority(content, demand_type)
            persona = identify_persona(content)

            print(f"    ✅ [{priority}][{demand_type}] {nickname}：{content[:40]}")

            leads.append({
                "feed_id": feed_id,
                "xsec_token": xsec_token,
                "note_title": title,
                "note_url": f"https://www.xiaohongshu.com/explore/{feed_id}",
                "author_name": author_name,
                "keyword": keyword,
                "nickname": nickname,
                "content": content,
                "demand_type": demand_type,
                "priority": priority,
                "persona": persona,
                "create_time": create_time,
            })

        time.sleep(1.5)  # 避免限流

    print(f"\n{'='*50}")
    print(f"✅ 意向客户：{len(leads)} 条")
    print(f"🚫 同行过滤：{skipped_spam} 条")
    print(f"❓ 无意向：  {skipped_no_intent} 条")
    print(f"📝 作者回复：{skipped_author} 条")

    return leads


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="小红书意向客户采集 v2")
    parser.add_argument("--keyword", default="法国公司注册", help="搜索关键词")
    parser.add_argument("--max-notes", type=int, default=10, help="最多处理笔记数")
    parser.add_argument("--days", type=int, default=90, help="评论时间范围（天），默认90天")
    parser.add_argument("--dry-run", action="store_true", help="只打印不写入飞书")
    args = parser.parse_args()

    leads = collect(args.keyword, args.max_notes, args.days)

    if leads:
        print("\n📋 结果（JSON）：")
        print(json.dumps(leads, ensure_ascii=False, indent=2))
    else:
        print("\n未发现意向客户。")
        sys.exit(0)
