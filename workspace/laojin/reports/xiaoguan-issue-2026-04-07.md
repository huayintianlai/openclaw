# 小冠无法主动回消息问题诊断报告

**时间**：2026-04-07 11:27  
**报告人**：老金  
**问题**：小冠无法主动回复飞书消息

---

## 问题现象

- 小冠收到飞书消息后无法回复
- 会话状态显示 `status: "failed"`
- 最近两个会话都失败

## 根本原因

**模型配置问题**：会话尝试使用的模型都失败了

### 错误详情

1. **第一次尝试**：Moonshot (kimi-k2.5)
   - 错误：`401 Invalid Authentication`
   - 原因：API Key 配置错误或失效

2. **第二次尝试**：DeepSeek
   - 错误：`402 Insufficient Balance`
   - 原因：账户余额不足

### 会话信息

- 会话 ID：`81fd0791-66e9-4fb0-b0c0-3f8c634cc535`
- 最后更新：2026-04-07 11:10
- 发送者：张建东 (ou_dc95eabe8982323faf7e9f3701e61e22)
- 消息内容：关于欧洲 GPSR 法规的调研请求

## 正确配置

小冠应该使用的模型：
- **Provider**: `custom`
- **Model**: `gpt`
- **Backend**: LiteLLM (`http://127.0.0.1:4000`)
- **Context**: 1,050,000 tokens

## 解决方案

### 方案 1：修复会话配置（推荐）

需要 Kent 手动操作：

```bash
# 1. 检查 LiteLLM 是否运行
curl http://127.0.0.1:4000/health

# 2. 重启小冠的会话，强制使用 custom/gpt
openclaw agent xiaoguan reset-session

# 3. 或者直接编辑会话配置
# 编辑 /Volumes/KenDisk/Coding/openclaw-runtime/agents/xiaoguan/sessions/sessions.json
# 确保 authProfileOverride 设置为 "custom:default"
```

### 方案 2：修复 API Keys（备选）

如果需要保留 Moonshot/DeepSeek：

1. **Moonshot**：更新 API Key
   ```bash
   # 在 auth-profiles.json 中更新 MOONSHOT_API_KEY
   ```

2. **DeepSeek**：充值账户
   ```bash
   # 访问 https://platform.deepseek.com/ 充值
   ```

## 预防措施

1. **设置默认模型**：在 agent 配置中明确指定默认使用 `custom/gpt`
2. **监控余额**：定期检查 DeepSeek 等付费服务的余额
3. **API Key 管理**：定期验证 API Keys 的有效性

## 后续行动

- [ ] Kent 确认 LiteLLM 运行状态
- [ ] 重置小冠的会话配置
- [ ] 测试消息回复功能
- [ ] 考虑添加模型降级机制（custom/gpt → custom/claude）

---

**诊断工具**：
- 会话日志：`/Volumes/KenDisk/Coding/openclaw-runtime/agents/xiaoguan/sessions/*.jsonl`
- 模型配置：`/Volumes/KenDisk/Coding/openclaw-runtime/agents/xiaoguan/agent/models.json`
- 会话状态：`/Volumes/KenDisk/Coding/openclaw-runtime/agents/xiaoguan/sessions/sessions.json`
