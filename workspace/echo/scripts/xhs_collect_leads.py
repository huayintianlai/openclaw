#!/usr/bin/env python3
"""
Echo 小红书意向客户采集脚本

双层过滤：
1. 时间过滤：只保留最近 N 天内的评论（默认 30 天）
2. 同行过滤：识别并排除广告/同行评论

用法：
  python3 scripts/xhs_collect_leads.py --keyword 法国公司注册 --days 30
"""

import json
import subprocess
import argparse
import time
from datetime import datetime, timedelta

# ============================================================
# 配置
# ============================================================

MCP_URL = "http://localhost:18060/mcp"

# 同行广告特征词（评论内容）
SPAM_CONTENT_KEYWORDS = [
    "独家", "货比三家", "线上线下合作", "均可办理",
    "欧美法仁", "一手资源", "私我", "加v", "加V",
    "威信", "wx", "WX", "➕微", "扫码", "报价单",
    "代办", "服务商推荐", "合作共赢", "佣金",
]

# 同行广告特征词（用户昵称）
SPAM_NICK_KEYWORDS = [
    "跨境注册", "欧洲注册", "本土注册", "VAT代",
    "欧注通", "跨途", "欧美公司", "OUBO", "跨境服务",
    "代办", "一手", "跨境飞猪", "金刚跨境",
]

# 意向客户特征词（至少命中一个才算意向）
INTENT_KEYWORDS = [
    "服务商", "推荐", "怎么", "办理", "咨询",
    "需要", "想", "多少钱", "费用", "哪家",
    "可以", "本土", "VAT", "流程", "注册",
    "入驻", "开店", "怎样", "求", "有没有",
    "我想", "我要", "多久", "资质",
]

# 需求类型分类
def classify_intent(content: str) -> str:
    if any(k in content for k in ["服务商", "推荐", "哪家", "哪里"]):
        return "求服务商"
    elif any(k in content for k in ["资质", "护照", "信息", "法人", "材料", "资料"]):
        return "资质问题"
    elif any(k in content for k in ["费用", "多少钱", "价格", "收费"]):
        return "开店咨询"
    elif any(k in content for k in ["VAT", "税", "免税"]):
        return "开店咨询"
    else:
        return "开店咨询"

# 优先级评估
def assess_priority(content: str, demand_type: str) -> str:
    high_signals = ["服务商", "推荐", "哪家", "私聊", "联系", "合作"]
    if demand_type == "求服务商" or any(k in content for k in high_signals):
        return "高"
    elif len(content) > 20:  # 评论内容较详细，说明认真
        return "中"
    else:
        return "低"

# ============================================================
# MCP 调用
# ============================================================

def call_mcp(tool_name: str, arguments: dict) -> dict:
    payload = json.dumps([
        {"jsonrpc": "2.0", "method": "initialize",
         "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "echo", "version": "1.0"}}, "id": 1},
        {"jsonrpc": "2.0", "method": "tools/call",
         "params": {"name": tool_name, "arguments": arguments}, "id": 2}
    ])
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", MCP_URL,
         "-H", "Content-Type: application/json", "-d", payload],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    if data[1].get("error"):
        raise Exception(data[1]["error"]["message"])
    text = data[1]["result"]["content"][0]["text"]
    return json.loads(text)

# ============================================================
# 过滤逻辑
# ============================================================

def is_spam(content: str, nickname: str) -> tuple[bool, str]:
    """返回 (是否同行, 原因)"""
    for kw in SPAM_CONTENT_KEYWORDS:
        if kw in content:
            return True, f"评论含同行词: {kw}"
    for kw in SPAM_NICK_KEYWORDS:
        if kw in nickname:
            return True, f"昵称含同行词: {kw}"
    return False, ""

def is_intent(content: str) -> bool:
    """是否有意向"""
    return any(kw in content for kw in INTENT_KEYWORDS)

def is_within_days(create_time_ms: int, days: int) -> bool:
    """评论时间是否在最近 N 天内"""
    cutoff = datetime.now() - timedelta(days=days)
    comment_time = datetime.fromtimestamp(create_time_ms / 1000)
    return comment_time >= cutoff

# ============================================================
# 主流程
# ============================================================

def collect_leads(keyword: str, days: int = 30, max_notes: int = 10) -> list[dict]:
    print(f"\n🔍 搜索关键词: {keyword}")
    print(f"📅 时间范围: 最近 {days} 天")
    print(f"📝 最多处理: {max_notes} 条笔记")
    print("-" * 50)

    # 搜索笔记
    search_result = call_mcp("search_feeds", {"keyword": keyword})
    feeds = search_result.get("feeds", [])
    print(f"共找到 {len(feeds)} 条笔记，取前 {max_notes} 条处理")

    all_leads = []
    skipped_time = 0
    skipped_spam = 0
    skipped_no_intent = 0
    skipped_author = 0

    for feed in feeds[:max_notes]:
        feed_id = feed["id"]
        xsec_token = feed["xsecToken"]
        title = feed["noteCard"]["displayTitle"]
        comment_count = feed["noteCard"]["interactInfo"]["commentCount"]

        if int(comment_count or 0) == 0:
            print(f"  ⏭️  跳过（无评论）: {title[:30]}")
            continue

        print(f"\n📖 {title[:35]}（{comment_count}条评论）")

        try:
            detail = call_mcp("get_feed_detail", {
                "feed_id": feed_id,
                "xsec_token": xsec_token,
                "load_all_comments": True
            })
            comments = detail["data"]["comments"]["list"]
        except Exception as e:
            print(f"  ❌ 获取失败: {e}")
            continue

        for c in comments:
            user_info = c.get("userInfo", {})
            nickname = user_info.get("nickname", "")
            content = c.get("content", "").strip()
            create_time = c.get("createTime", 0)
            is_author = "is_author" in c.get("showTags", [])

            # 排除作者
            if is_author:
                skipped_author += 1
                continue

            # 排除空评论
            if not content:
                continue

            # 层1：时间过滤
            if not is_within_days(create_time, days):
                skipped_time += 1
                continue

            # 层2：同行过滤
            spam, reason = is_spam(content, nickname)
            if spam:
                print(f"  🚫 同行: [{nickname}] {content[:40]} ({reason})")
                skipped_spam += 1
                continue

            # 意向判断
            if not is_intent(content):
                skipped_no_intent += 1
                continue

            # 通过！
            demand_type = classify_intent(content)
            priority = assess_priority(content, demand_type)
            print(f"  ✅ [{priority}][{demand_type}] [{nickname}] {content[:50]}")

            all_leads.append({
                "笔记ID": feed_id,
                "笔记链接": f"https://www.xiaohongshu.com/explore/{feed_id}",
                "笔记标题": title,
                "关键词": keyword,
                "评论用户": nickname,
                "评论原文": content,
                "需求类型": demand_type,
                "优先级": priority,
                "评论时间": create_time,
            })

        time.sleep(1)  # 避免频率限制

    print("\n" + "=" * 50)
    print(f"✅ 通过筛选: {len(all_leads)} 条")
    print(f"⏭️  时间过期: {skipped_time} 条")
    print(f"🚫 同行过滤: {skipped_spam} 条")
    print(f"❓ 无意向:   {skipped_no_intent} 条")
    print(f"📝 作者回复: {skipped_author} 条")

    return all_leads


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="小红书意向客户采集")
    parser.add_argument("--keyword", default="法国公司注册", help="搜索关键词")
    parser.add_argument("--days", type=int, default=30, help="时间范围（天）")
    parser.add_argument("--max-notes", type=int, default=10, help="最多处理笔记数")
    parser.add_argument("--dry-run", action="store_true", help="只打印不写入飞书")
    args = parser.parse_args()

    leads = collect_leads(args.keyword, args.days, args.max_notes)

    if leads and not args.dry_run:
        print(f"\n💾 准备写入飞书（{len(leads)} 条）...")
        # 写入逻辑由调用方（Echo）完成
        print(json.dumps(leads, ensure_ascii=False, indent=2))
    elif args.dry_run:
        print("\n[Dry Run] 不写入飞书，仅展示结果：")
        print(json.dumps(leads, ensure_ascii=False, indent=2))
