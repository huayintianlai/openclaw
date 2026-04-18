# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Xiaoguan Task Workflow

- 主链路：官方 `feishu_task_tasklist` + `feishu_task_task`
- 当前任务清单：`小冠清单`
- `tasklist_guid`: `c8851bed-0b84-41d3-905e-411ad58144f6`
- 常用动作：
  - 清单发现：`feishu_task_tasklist` `action=list`
  - 清单内任务：`feishu_task_tasklist` `action=tasks`
  - 创建任务：`feishu_task_task` `action=create`
  - 查询任务：`feishu_task_task` `action=get`
  - 更新任务：`feishu_task_task` `action=patch`
- 时间字段统一使用带时区的 ISO 8601 / RFC 3339，例如 `2026-03-24T18:00:00+08:00`
- 文档兜底使用 `feishu_fetch_doc` / `feishu_create_doc` / `feishu_update_doc`，不再作为默认任务系统

## Xiaoguan Bitable Tables

- 通用 app_token：`Z3DEboviLaJAlXsdUPvcItgrnZd`
- CRM 表：`tblTrN5hZM9w0Aj2`
- 意向表：`tblc2lDtItP7N7vp`
- 成交表：`tbl2SZmEq4LbQkBk`
- 群消息监听表 / **03.6_同行动态**（简称：同行动态表）：`tblhviIhGA7ToWxy`
  - 别名：同行动态、同行动态表、03.6_同行动态、群聊监听记录表
  - 用途：记录微信群监听到的同行动态，按结构化字段入库
  - 字段：消息内容、发言人、消息时间、店铺类型、业务类型、关键信息、来源群、处理状态

订单与客户结构化数据优先写 bitable；通用待办和跟进事项优先写 `小冠清单`。

## WeChat Runtime

- 本地 runtime 根目录：`/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime`
- CLI 入口：`/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/bin/wechat-ops`
- worker 入口：`/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/bin/xiaoguan-wechat-worker`
- 小冠工作区 wrapper：`/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/bin/wechat-ops`
- worker wrapper：`/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/bin/xiaoguan-wechat-worker`
- 验收脚本：`/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/scripts/acceptance.sh`
- 配置文件：`/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/config/wechat-ops.json`
- 状态文件：`/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/state/runtime-state.json`
- daemon 状态：`/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/state/daemon-state.json`
- worker 状态：`/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/state/worker-state.json`
- watcher 状态目录：`/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/state/watchers`
- jobs 队列：`/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/state/jobs`
- results 队列：`/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/state/results`
- 事件流：`/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/state/events.jsonl`
- 小冠可以直接 exec 这个 wrapper 做内部微信探测，不需要额外确认。
