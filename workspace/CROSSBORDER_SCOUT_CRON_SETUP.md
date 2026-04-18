# 跨境雷达周期执行配置

## 使用 CronCreate 创建每周一定时任务

根据 OpenClaw 官方文档，对于需要精确时间的周期任务（如"每周一 9:00"），应该使用 cron 而不是 heartbeat。

### 创建方法

在 xiaodong 的会话中执行以下命令：

```javascript
// 每周一上午 9:00 执行跨境风险扫描
await CronCreate({
  cron: "0 9 * * 1",  // 标准 cron 表达式：分 时 日 月 周（1=周一）
  prompt: "使用 sessions_spawn 调用 xiaodong_crossborder_scout，任务为'请执行近 30 天默认口径的跨境风险扫描'",
  recurring: true
});
```

### Cron 表达式说明

- `0 9 * * 1` = 每周一上午 9:00
- 格式：`分钟 小时 日 月 星期`
- 星期：0=周日, 1=周一, 2=周二, ..., 6=周六

### 为什么不用 heartbeat？

| 需求 | heartbeat | cron |
|------|-----------|------|
| 每周一 9:00 | ❌ 只能每 24h，需要 Agent 自己判断是否周一 | ✅ 精确指定周一 9:00 |
| 灵活性 | ❌ 一个 Agent 只能一个 heartbeat | ✅ 一个 Agent 可以多个 cron 任务 |
| 配置方式 | openclaw.json | CronCreate 工具 |

### 执行步骤

1. 通过飞书或 Telegram 与 xiaodong 对话
2. 发送消息：
   ```
   请创建一个 cron 定时任务：每周一上午 9:00 调用 xiaodong_crossborder_scout 执行跨境风险扫描
   ```
3. xiaodong 会使用 CronCreate 工具创建任务
4. 验证：发送 `/tasks` 查看已创建的定时任务

### 注意事项

- cron 任务只在当前 Claude 会话中有效
- 如果重启 OpenClaw 容器，需要重新创建
- 可以通过 CronList 查看所有任务
- 可以通过 CronDelete 删除任务

### 替代方案：系统级 crontab

如果需要持久化的定时任务（重启后仍然有效），可以在宿主机配置 crontab：

```bash
# 编辑 crontab
crontab -e

# 添加任务（每周一 9:00）
0 9 * * 1 docker exec openclaw-kentclaw curl -X POST http://localhost:18789/api/sessions/xiaodong/messages -H "Content-Type: application/json" -d '{"content":"使用 sessions_spawn 调用 xiaodong_crossborder_scout，任务为'\''请执行近 30 天默认口径的跨境风险扫描'\''"}'
```

但这种方式需要配置 Gateway API 认证，相对复杂。

---

**推荐方案：** 使用 CronCreate 工具，简单且符合 OpenClaw 设计理念。
