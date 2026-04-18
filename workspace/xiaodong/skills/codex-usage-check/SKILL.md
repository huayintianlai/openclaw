---
name: codex-usage-check
---

# Codex Usage 余量查询（HTTP API 直连，不依赖浏览器插件）

## Description
直接调用 `https://deepl.micosoft.icu/api/` 的接口查询 Codex 余量/用量（无需 OpenClaw Browser Relay）。

## When to use
用户说“查余量 / 用量 / codexusage / 今日花了多少 / 额度还剩多少”等。

## Tools
- exec

## Inputs
- baseUrl: `https://deepl.micosoft.icu/api`
- cardKey: 授权码（只在运行时使用，不要回显到聊天里，不要写入长期记忆）

## Procedure
1) POST `/users/card-login` 获取 `user.token`
2) GET `/users/whoami` 获取：day_score_used、vip.day_score、vip.expire_at 等
3) （可选）POST `/chatgpt/chatlog` 获取最近 N 条使用记录（page/pageSize）
4) 结构化输出：今日已用、每日额度、剩余、到期日、最近使用（可选）

## Notes
- 认证头：后续请求使用 `x-auth-token: <token>`
- 若接口返回非 200 或 JSON parse 失败，直接回报 HTTP 状态码 + 响应体前 200 字符（脱敏）。
