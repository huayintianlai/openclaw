# 记忆系统测试 - 问题排查与修复指南

## 常见问题诊断树

---

## 问题 1: memory_store 工具调用失败

### 症状
- Agent 报错："memory_store tool not found"
- 或者工具调用后无响应
- 或者返回错误信息

### 排查步骤

#### 1.1 检查 openclaw.json 配置
```bash
# 检查 agent 的 tools.allow 列表
grep -A 20 '"id": "xiaodong"' /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/openclaw.json | grep -E "memory_store|memory_search|memory_list|memory_forget"
```

**预期结果：** 应该看到这些工具在 allow 列表中

**如果缺失：** 在 openclaw.json 的对应 agent 配置中添加：
```json
"tools": {
  "allow": [
    "memory_search",
    "memory_get",
    "memory_store",
    "memory_list",
    "memory_forget"
  ]
}
```

#### 1.2 检查 Mem0 插件状态
```bash
# 检查插件是否启用
grep -A 5 '"openclaw-mem0"' /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/openclaw.json
```

**预期结果：**
```json
"openclaw-mem0": {
  "enabled": true,
  ...
}
```

**如果 enabled: false：** 修改为 `"enabled": true`

#### 1.3 检查环境变量
```bash
# 进入容器检查
docker exec -it kentclaw-openclaw-1 env | grep -E "QDRANT|MEM0"
```

**预期结果：**
```
QDRANT_URL=https://qdrant.99uwen.com
QDRANT_API_KEY=b5f76dd48b706008495b983487aff77a27630e609290bf78550cd79a6384addb
MEM0_BASE_USER_ID=kentclaw
MEM0_QDRANT_COLLECTION=openclaw_mem0_prod
```

**如果缺失：** 检查 .env 文件并重启容器

#### 1.4 测试 Qdrant 连接
```bash
# 测试 Qdrant API
curl -H "api-key: b5f76dd48b706008495b983487aff77a27630e609290bf78550cd79a6384addb" \
  https://qdrant.99uwen.com/collections
```

**预期结果：** 返回 collection 列表

**如果失败：** 检查网络连接或 API key

---

## 问题 2: memory_search 找不到刚存储的记忆

### 症状
- memory_store 成功
- 但 memory_search 返回空结果或找不到

### 排查步骤

#### 2.1 检查 user_id 隔离
Mem0 使用 `agent_id` 作为 user_id 进行记忆隔离。

```bash
# 检查配置
grep -A 10 '"openclaw-mem0"' /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/openclaw.json | grep userId
```

**预期：** `"userId": "${MEM0_BASE_USER_ID}"`

#### 2.2 检查搜索阈值
```json
"searchThreshold": 0.5
```

**如果阈值过高：** 降低到 0.3 试试

#### 2.3 检查 embedding 模型
```bash
# 检查配置
grep -A 5 '"embedder"' /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/openclaw.json
```

**预期：**
```json
"embedder": {
  "provider": "openai",
  "config": {
    "model": "text-embedding-3-small"
  }
}
```

#### 2.4 手动验证 Qdrant 中的数据
```bash
# 查询 collection 中的点
curl -X POST "https://qdrant.99uwen.com/collections/openclaw_mem0_prod/points/scroll" \
  -H "api-key: b5f76dd48b706008495b983487aff77a27630e609290bf78550cd79a6384addb" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

---

## 问题 3: read 工具无法读取文件

### 症状
- 报错："file not found"
- 或者权限错误

### 排查步骤

#### 3.1 检查文件路径
容器内路径 vs 宿主机路径：
- 宿主机：`/Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/workspace/xiaodong/AGENTS.md`
- 容器内：`/Users/xiaojiujiu2/.openclaw/workspace/xiaodong/AGENTS.md`

**测试消息应该使用容器内路径**

#### 3.2 检查文件是否存在
```bash
# 在容器内检查
docker exec -it kentclaw-openclaw-1 ls -la /Users/xiaojiujiu2/.openclaw/workspace/xiaodong/
```

#### 3.3 检查 workspace 配置
```bash
grep -A 5 '"id": "xiaodong"' /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/openclaw.json | grep workspace
```

**预期：** `"workspace": "/Users/xiaojiujiu2/.openclaw/workspace/xiaodong"`

---

## 问题 4: 飞书机器人无响应

### 症状
- 发送消息后机器人不回复
- 或者显示"机器人离线"

### 排查步骤

#### 4.1 检查容器状态
```bash
docker ps | grep kentclaw
```

**预期：** 容器状态为 Up

#### 4.2 检查飞书配置
```bash
# 检查 app_id 和 app_secret
grep -E "FEISHU_XIAODONG_APP_ID|FEISHU_XIAODONG_APP_SECRET" /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/.env
```

#### 4.3 检查飞书 webhook
```bash
# 查看容器日志
docker logs kentclaw-openclaw-1 --tail 100 | grep -i feishu
```

**查找：**
- "Feishu webhook received"
- 错误信息

#### 4.4 检查用户权限
```json
"allowFrom": [
  "ou_dc95eabe8982323faf7e9f3701e61e22"
]
```

**确认你的飞书 user_id 在 allowFrom 列表中**

#### 4.5 测试飞书 API
```bash
# 获取 access_token
curl -X POST "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal" \
  -H "Content-Type: application/json" \
  -d '{
    "app_id": "cli_a904a148eab81bd8",
    "app_secret": "hiq9eHvKjmGlRLjjjxxeag45Jfpf4bTj"
  }'
```

---

## 问题 5: task 工具调用失败

### 症状
- `feishu_task_task` 或 `feishu_task_tasklist` 调用失败
- 报错：用户授权不足、scope 不足、任务工具不可用

### 排查步骤

#### 5.1 检查插件状态
```bash
grep -A 10 '"openclaw-lark"' /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/openclaw.json
```

**预期：** `"enabled": true`

#### 5.2 检查用户 token
```bash
# 检查 token 文件
docker exec -it kentclaw-openclaw-1 cat /Users/xiaojiujiu2/.openclaw/state/feishu-user-token.json
```

**预期：** 包含有效的 access_token 和 refresh_token

#### 5.3 检查环境变量
```bash
grep -E "FEISHU_XIAODONG_USER_ACCESS_TOKEN|FEISHU_XIAODONG_USER_REFRESH_TOKEN" /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/.env
```

#### 5.4 手动刷新 token
```bash
# 使用 refresh_token 获取新的 access_token
curl -X POST "https://open.feishu.cn/open-apis/authen/v1/refresh_access_token" \
  -H "Content-Type: application/json" \
  -d '{
    "grant_type": "refresh_token",
    "refresh_token": "ur-cxwhpx0fR38UlkcfZUvxHUgl4HmR4hWjX08amQE00xzm"
  }'
```

---

## 问题 6: sessions_spawn 调用失败

### 症状
- aduan 无法 spawn 子 agent
- 报错："agent not found" 或超时

### 排查步骤

#### 6.1 检查 subagents 配置
```bash
grep -A 10 '"id": "aduan"' /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/openclaw.json | grep -A 5 subagents
```

**预期：**
```json
"subagents": {
  "allowAgents": [
    "xiaodong",
    "xiaodong_crossborder_scout",
    "xiaoguan",
    "finance"
  ]
}
```

#### 6.2 检查目标 agent 是否存在
```bash
grep '"id": "xiaodong_crossborder_scout"' /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/openclaw.json
```

#### 6.3 检查并发限制
```json
"subagents": {
  "maxConcurrent": 8
}
```

---

## 问题 7: 图片处理失败

### 症状
- 发送图片后 agent 无法识别
- 或者报错

### 排查步骤

#### 7.1 检查模型支持
```bash
grep -A 20 '"id": "xiaodong"' /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/openclaw.json | grep -A 10 model
```

**预期：** 模型支持 image input
```json
"input": [
  "text",
  "image"
]
```

#### 7.2 检查图片大小
- 飞书限制：< 10MB
- 建议：< 5MB

#### 7.3 检查图片格式
支持的格式：
- JPG/JPEG
- PNG
- GIF
- WebP

---

## 快速修复命令

### 重启 OpenClaw 容器
```bash
cd /Users/xiaojiujiu2/Documents/openclaw-docker
docker-compose -f docker-compose.yml restart openclaw
```

### 查看实时日志
```bash
docker logs -f kentclaw-openclaw-1
```

### 清理并重启
```bash
cd /Users/xiaojiujiu2/Documents/openclaw-docker
docker-compose down
docker-compose up -d
```

### 重新加载配置（无需重启）
```bash
# 发送 SIGHUP 信号
docker exec kentclaw-openclaw-1 kill -HUP 1
```

---

## 性能优化建议

### 1. 记忆搜索优化
```json
"openclaw-mem0": {
  "config": {
    "topK": 5,  // 减少到 3 可以提速
    "searchThreshold": 0.5  // 提高到 0.6 可以提高精度
  }
}
```

### 2. 并发优化
```json
"defaults": {
  "maxConcurrent": 4,  // 根据服务器性能调整
  "subagents": {
    "maxConcurrent": 8
  }
}
```

### 3. 官方插件确认
```json
"openclaw-lark": {
  "enabled": true
}
```

---

## 测试后清理

### 清理测试记忆
```bash
# 在每个 agent 中执行
memory_list  # 获取所有记忆 ID
memory_forget <memory_id>  # 删除测试记忆
```

### 清理测试任务
```bash
# 在 xiaodong/xiaoguan 中执行
feishu_task_task  # action=list 获取任务列表
# 然后再用 action=patch 或飞书界面清理测试任务
```

### 清理测试文件
```bash
rm /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/workspace/test_*.md
rm /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/workspace/pre_test_check.sh
```

---

## 联系支持

如果以上方法都无法解决问题：

1. 收集日志：
```bash
docker logs kentclaw-openclaw-1 > openclaw_logs.txt
```

2. 导出配置：
```bash
cp /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/openclaw.json openclaw_config_backup.json
```

3. 记录问题详情：
   - 问题描述
   - 复现步骤
   - 错误信息
   - 环境信息

4. 提交 issue 或寻求帮助

---

## 测试成功标准

### 最低标准（必须通过）
- ✅ 至少 3 个 agent 的 memory_store 正常
- ✅ 至少 3 个 agent 的 memory_search 正常
- ✅ 所有 agent 的 read 工具正常
- ✅ 飞书机器人响应正常

### 理想标准（期望通过）
- ✅ 所有配置的 memory 工具正常
- ✅ 所有 task 工具正常
- ✅ 图片处理正常
- ✅ sessions_spawn 正常
- ✅ 记忆隔离正确
- ✅ 记忆持久化正常

---

测试愉快！🚀
