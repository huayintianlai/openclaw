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

## Shared WeChat Runtime

- 共享 runtime 根目录：`/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime`
- CLI 入口：`/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/wechat-ops-runtime/bin/wechat-ops`
- 当前 laojin watcher 通过这个 runtime 获取：
  - 健康检查
  - 当前会话识别
  - LLM 屏幕分析
  - 安全发送（目标会话校验）

## Mobile Runtime

laojin 现在优先通过共享 `mobile_*` 工具操作手机，不再从业务流程里直接拼 `adb`。

### 设备别名

- `xiaodong-main`：主力通用手机
- `xiaodong-backup`：备用通用手机
- `echo-xhs-1`：艾可主力小红书手机
- `echo-xhs-2`：艾可备用小红书手机

### 推荐调用

- 观察屏幕：`mobile_observe`
- 运行模板任务：`mobile_run_task`
- 单步语义动作：`mobile_act`
- 查看任务与锁：`mobile_status`
- 查看截图与 UI 树：`mobile_artifacts`

### 典型用法

```javascript
await mobile_run_task({
  device_selector: { alias: "xiaodong-main" },
  flow_id: "wechat_read_only",
  inputs: { chat_name: "客户A" },
  approval_policy: "auto"
});
```

如需探索型任务或中文输入兜底，runtime 会自动下沉到 AutoGLM；不要在业务提示词里直接引用序列号或 `phone_control.sh`。

## Feishu Official Lark Tools

### 工具清单

**官方文档工具：**
- `feishu_fetch_doc`：通过文档 ID 或 URL 直接读取飞书文档内容。
- `feishu_create_doc` / `feishu_update_doc`：创建和更新飞书文档。
- `feishu_doc_media` / `feishu_doc_comments`：处理文档媒体和评论。

**官方任务与日历工具：**
- `feishu_task_task`：任务本体，使用 `action=create|get|list|patch`。
- `feishu_task_tasklist`：任务清单，使用 `action=create|get|list|tasks|patch|delete|add_members|remove_members`。
- `feishu_task_comment`：任务评论，使用 `action=create|list|get`。
- `feishu_task_subtask`：子任务，使用 `action=create|list`。
- `feishu_calendar_calendar`：日历管理，使用 `action=list|get|primary`。
- `feishu_calendar_event`：日程管理，使用 `action=create|list|get|patch|delete|search|reply|instances|instance_view`。
- `feishu_calendar_event_attendee` / `feishu_calendar_freebusy`：参会人与忙闲查询。

### 权限边界

- 当前已切到官方 `openclaw-lark`。
- 不再使用旧的 scoped wiki/doc 工具名。
- 写入行为由官方飞书应用权限和工具白名单共同约束。

## Feishu Official Notes

- 飞书知识库 / Wiki 已停用，不要再把任务引导到旧的 wiki 节点结构。
- 旧的 `feishu-task-mcp`、`feishu-task-plugin`、scoped wiki/doc 工具已经下线。
- 如果任务、文档或历史消息工具报用户授权错误，优先走官方 `feishu_oauth` / 自动授权链路。

## 跨境雷达调用（xiaodong_crossborder_scout）

**重要：** 你负责调用跨境雷达，不是 aduan。

### 快速调用

当用户要求"跨境扫描"、"看看跨境风险"、"检查平台政策"时：

```typescript
// 直接调用，不要反问
await sessions_spawn({
  agent: "xiaodong_crossborder_scout",
  task: "请执行近 30 天默认口径的跨境风险扫描（主题：跨境服务商近期市场与风险信号；范围：法国/德国公司注册、欧盟 VAT、支付、物流、合规政策，以及 16 个重点平台的招商政策、卖家风险、经营门槛）"
});
```

### 详细指南

参考 `CROSSBORDER_SCOUT_GUIDE.md` 了解：
- 调用时机和方式
- 返回结果处理
- 后续动作建议
- 常见问题排查

### 关键原则

- ❌ 不要问用户"需要扫描哪些平台"
- ✅ 直接调用，默认口径以 scout 自身 TOOLS.md 为准
- ✅ 默认主轴：法国/德国公司注册、欧盟 VAT、支付、物流、合规政策
- ✅ 默认平台池：16 个重点平台的招商政策、卖家风险、经营门槛
- ✅ 泛行业资讯、无明确中国卖家影响的信息，不进入正式预警
- ✅ 等待结果，处理高风险通知
- ✅ 评估影响，决定后续动作

## Blogwatcher（行业资讯监控）

### 工具路径

- 二进制：`~/go/bin/blogwatcher`
- Skill：`skills/blogwatcher`

### 已追踪的 RSS 源

| 名称 | URL | 说明 |
|---|---|---|
| Readhub Daily | https://readhub.cn/daily | 科技/商业/资本市场日报 |

### 常用命令

- 扫描更新：`~/go/bin/blogwatcher scan`
- 查看未读：`~/go/bin/blogwatcher articles`
- 标记已读：`~/go/bin/blogwatcher read-all`
- 添加源：`~/go/bin/blogwatcher add "名称" https://url`
- 查看订阅列表：`~/go/bin/blogwatcher blogs`

### 使用时机

- 用户要求「看看今日资讯」、「有什么行业动态」时，主动执行 `scan` + `articles`
- 跨境雷达扫描前，可先拉取 Readhub 动态作为背景信息补充
