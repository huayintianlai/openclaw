# 小冠余额错误诊断报告

**时间**：2026-04-07 12:04
**问题**：小冠报错 "API provider returned a billing error"

## 根因分析

### 1. LLM-Hub 上游 API 额度问题（已恢复）

**历史错误**（2026-04-06）：
- `quan2go-gpt`：`limit exceeded, 额度用完了`（熔断器打开）
- `yunyi-gpt`：`没有可用token`

**当前状态**（2026-04-07 12:05）：
- ✅ LLM-Hub 健康检查通过
- ✅ 测试请求成功返回（gpt-5.4 模型）
- ✅ 上游 API 已恢复正常

### 2. 小冠会话状态问题（已修复）

**问题**：
- 会话状态为 `failed`
- 运行时间仅 1.5 秒就失败
- 配置正确但无法正常工作

**修复**：
- 会话状态已改为 `active`
- 配置确认：`model: gpt`, `authProfileOverride: custom:default`

## 技术架构确认

### LLM-Hub 配置
- **端口**：4000（OpenClaw 默认）、4105（Codex）、4106（KekeBaby）、4107（Claude Code）
- **上游**：
  - `quan2go-gpt`（优先级 1）
  - `yunyi-gpt`（优先级 2）
  - `yunyi-claude`（优先级 1）

### OpenClaw 配置
- **custom provider**：`http://127.0.0.1:4000`（指向 LLM-Hub）
- **小冠模型**：`gpt`（通过 LLM-Hub 路由到 gpt-5.4）

## 解决方案

1. ✅ LLM-Hub 上游 API 已自动恢复
2. ✅ 小冠会话状态已修复为 `active`
3. ✅ 配置验证通过

## 预防措施

### 监控建议
- 定期检查 LLM-Hub 日志：`tail -f /Users/xiaojiujiu2/Documents/coding/LLM-Hub/logs/gateway.log`
- 监控熔断器状态：访问 `http://localhost:8080`（LLM-Hub Dashboard）

### 备用方案
- 配置多个上游 API Key（已配置 GPT_KEY_A/B/C/D）
- 熔断器自动切换到备用上游

## 相关文件

- LLM-Hub 配置：`/Users/xiaojiujiu2/Documents/coding/LLM-Hub/config/gateway.yaml`
- 小冠会话配置：`/Volumes/KenDisk/Coding/openclaw-runtime/agents/xiaoguan/sessions/sessions.json`
- 会话日志：`/Volumes/KenDisk/Coding/openclaw-runtime/agents/xiaoguan/sessions/81fd0791-66e9-4fb0-b0c0-3f8c634cc535.jsonl`

---

**结论**：问题已解决，小冠现在应该可以正常回复消息了。
