# 两个风险的最终方案

## 风险 1：scout heartbeat - 已移除 ✅
**决策：** 移除 scout 的 heartbeat
**理由：** 避免与 xiaodong 的 cron 调用冲突，统一由 xiaodong 管理

## 风险 2：sessions_send 目标会话
**当前代码：**
```javascript
await sessions_send({
  agent: "xiaodong",
  content: "..."
});
```

**问题：** 当 scout 被 xiaodong 通过 sessions_spawn 调用时，通知会发送到 xiaodong 的会话，xiaodong 会收到并转发给用户 ✅

**结论：** 当前实现正确，无需调整

---

## 最终配置状态

✅ xiaodong 有 sessions_spawn 权限
✅ xiaodong 有 subagents.allowAgents 配置
✅ scout 有 sessions_send 权限
✅ scout 的 heartbeat 已移除
✅ 飞书表格已配置完成

**下一步：通过飞书测试**
```
请使用 sessions_spawn 调用 xiaodong_crossborder_scout，任务为'测试调用'
```
