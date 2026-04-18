# HEARTBEAT.md - 系统运维巡检

## 1. 记忆系统健康检查

每次心跳先执行 Mem0 探针测试：

1. **读探针**：`memory_search(query="Kent")`
   - 目标：验证搜索链路
   - 成功标准：工具执行成功（即使返回空结果）

2. **写探针**：`memory_store`
   - 内容：`[MEM0_HEALTHCHECK][YYYY-MM-DD] xiaodong heartbeat probe`
   - 参数：`longTerm=true`
   - metadata：`{healthcheck: true, source: "heartbeat", kind: "mem0_probe"}`
   - 目标：验证 LLM 提取 + embedding + 写入链路

3. **清理探针**：`memory_forget(memoryId)`
   - 使用 `memory_store` 返回的 `memoryId`
   - 目标：避免污染长期记忆

4. **失败处理**
   - 任一步骤失败 → 立即报告 `MEM0_ALERT: [具体错误]`
   - 停止后续检查，等待人工介入

---

## 2. xiaodong 任务健康检查

检查 xiaodong agent 的定时任务是否正常运行：

### 检查项

- **早报任务**：是否在 8:30-8:59 触发
- **跨境雷达**：xiaodong_crossborder_scout 是否按周执行
- **AI 侦察**：xiaodong_ai_scout 是否按 48 小时周期运行

### 检查方法

```bash
# 检查 xiaodong 的日志
tail -n 100 ~/.openclaw/logs/xiaodong.log | grep -E "早报|crossborder|ai_scout"

# 检查 cron 任务
crontab -l | grep xiaodong
```

### 异常报告

- 早报未按时触发 → `TASK_ALERT: xiaodong 早报未按时触发（上次：[时间]）`
- 雷达任务失败 → `TASK_ALERT: 跨境雷达执行失败（错误：[摘要]）`
- AI 侦察异常 → `TASK_ALERT: AI Scout 异常（错误：[摘要]）`

---

## 3. 飞书工具链健康检查

检查飞书 OAuth 授权状态：

```bash
# 检查授权状态
cat ~/.openclaw/feishu-auth-status.json
```

### 异常报告

- 授权失效 → `AUTH_ALERT: 飞书授权失效（user_id: [ID]）`
- Token 过期 → `AUTH_ALERT: 飞书 Token 过期（需重新授权）`

---

## 4. 代码项目运维检查

对所有我负责的代码项目进行健康检查：

### 检查项

- **进程状态**：关键服务是否存活
- **日志错误**：最近 24 小时是否有 ERROR/FATAL
- **性能指标**：CPU/内存/磁盘是否异常
- **依赖更新**：是否有安全漏洞需要修复

### 主动修复

发现问题后：
1. 评估影响范围
2. 直接修复（如果是明确的 bug）
3. 提交代码并测试
4. 报告修复结果

### 异常报告

- 进程挂掉 → `SERVICE_ALERT: [项目名] 进程异常（PID: [ID]）`
- 日志错误 → `LOG_ALERT: [项目名] 发现错误（[错误摘要]）`
- 性能异常 → `PERF_ALERT: [项目名] 性能异常（[指标]）`

---

## 5. 兜底规则

如果所有检查都通过，回复：`HEARTBEAT_OK`
