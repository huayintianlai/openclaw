# 记忆系统测试指南 - 实际操作步骤

## 前置准备

1. 确保 OpenClaw 系统正在运行
2. 确保各个 agent 的飞书/Telegram 机器人已启动
3. 准备好测试用的图片文件（可选）

## 测试执行方式

你需要通过以下渠道与各个 agent 对话：

### 飞书渠道
- **xiaodong**: 飞书私聊 "小东" 机器人
- **xiaoguan**: 飞书私聊 "小冠" 机器人
- **finance**: 飞书私聊 "Finance Bot" 机器人
- **aduan**: 飞书私聊 "ceo_aduan" 机器人
- **echo**: 飞书私聊 "艾可" 机器人

### Telegram 渠道（备选）
- **xiaodong**: Telegram 私聊对应 bot
- **xiaoguan**: Telegram 私聊对应 bot
- **finance**: Telegram 私聊对应 bot

---

## 测试 1: xiaodong（小东）

### 发送消息：
```
你好小东，我要测试你的记忆系统。

第一步：请使用 memory_store 工具存储这条记忆：
"小红书投放策略：CPA 目标控制在 50 元以内，ROI >= 2.0，优先投放美妆和时尚类目"

第二步：使用 memory_search 工具搜索"小红书 CPA"

第三步：使用 memory_list 工具列出你的所有记忆

第四步：使用 read 工具读取 /Users/xiaojiujiu2/.openclaw/workspace/xiaodong/AGENTS.md

第五步：总结测试结果，告诉我哪些功能正常，哪些有问题。
```

### 预期行为：
- ✅ 应该调用 memory_store 工具
- ✅ 应该调用 memory_search 工具并找到刚存储的内容
- ✅ 应该调用 memory_list 工具
- ✅ 应该调用 read 工具并返回文件内容
- ✅ 应该给出清晰的测试总结

### 记录结果：
在 test_execution_log.md 中记录实际结果

---

## 测试 2: xiaodong_crossborder_scout（跨境雷达）

### 发送消息：
```
你好，我要测试你的记忆和搜索系统。

第一步：使用 memory_store 存储：
"Amazon 2026-03 新政：VAT 合规要求加强，所有欧洲站点必须提供完整税务文件，否则将限制销售"

第二步：使用 memory_search 搜索"Amazon VAT"

第三步：使用 read 读取 /Users/xiaojiujiu2/.openclaw/workspace/xiaodong_crossborder_scout/AGENTS.md

第四步：使用 tavily_search 搜索"Amazon seller policy changes 2026"

第五步：总结测试结果。
```

### 预期行为：
- ✅ memory_store 正常
- ✅ memory_search 能找到记忆
- ✅ read 返回文件内容
- ✅ tavily_search 返回搜索结果

---

## 测试 3: finance（财务）

### 发送消息：
```
你好 Finance，测试你的记忆系统。

第一步：使用 memory_store 存储：
"财务预警规则：净利润较基线下降 30% 时触发预警，现金流低于 10 万时进入严肃模式"

第二步：使用 memory_search 搜索"净利润预警"

第三步：使用 read 读取 /Users/xiaojiujiu2/.openclaw/workspace/finance/AGENTS.md

第四步：使用 memory_list 列出所有记忆

第五步：总结测试结果。
```

### 预期行为：
- ✅ memory_store 正常
- ✅ memory_search 正常
- ✅ read 正常
- ✅ memory_list 正常
- ⚠️ 注意：finance 没有 write/edit 权限

---

## 测试 4: xiaoguan（小冠）

### 发送消息：
```
你好小冠，测试你的记忆和任务系统。

第一步：使用 memory_store 存储：
"客户张三偏好：周末不打扰，工作日 10-18 点联系，喜欢简洁沟通，对价格敏感"

第二步：使用 memory_search 搜索"客户张三"

第三步：使用 read 读取 /Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/AGENTS.md

第四步：使用 `feishu_task_task` 的 `action=create` 创建测试任务：
- 标题："跟进客户张三 - 记忆系统测试"
- 截止日期：明天
- 描述："这是一个测试任务，用于验证任务创建功能"

第五步：使用 `feishu_task_task` 的 `action=list` 列出任务

第六步：总结测试结果。
```

### 预期行为：
- ✅ memory_store 正常
- ✅ memory_search 正常
- ✅ read 正常
- ✅ task_create 正常
- ✅ task_list 正常

---

## 测试 5: aduan（ceo_aduan）

### 发送消息：
```
你好阿段，测试你的文件读取和调度能力。

第一步：使用 read 读取 /Users/xiaojiujiu2/.openclaw/workspace/aduan/HEARTBEAT.md

第二步：使用 read 读取 /Users/xiaojiujiu2/.openclaw/workspace/aduan/ADUAN_DATA_CONTRACT.md

第三步：使用 sessions_list 查看当前会话列表

第四步：使用 knowledge_search 搜索"公司通识"

第五步：总结测试结果。
```

### 预期行为：
- ✅ read 正常
- ✅ sessions_list 正常
- ✅ knowledge_search 正常
- ⚠️ 注意：aduan 没有 memory 工具

---

## 测试 6: echo（艾可）

### 发送消息：
```
你好艾可，测试你的记忆和工具系统。

第一步：使用 memory_store 存储：
"Boss 偏好：喜欢简洁的日报格式，不要过多细节，重点突出关键指标和异常情况"

第二步：使用 memory_search 搜索"日报格式"

第三步：使用 read 读取 /Users/xiaojiujiu2/.openclaw/workspace/echo/AGENTS.md

第四步：使用 tavily_search 搜索"AI productivity tools 2026"

第五步：总结测试结果。
```

### 预期行为：
- ✅ memory_store 正常
- ✅ memory_search 正常
- ✅ read 正常
- ✅ tavily_search 正常

---

## 图片处理测试（可选）

### 准备测试图片
创建一个简单的测试图片，包含文字或图表。

### 测试 xiaodong
1. 在飞书中向小东发送图片
2. 发送消息："请描述这张图片的内容，并使用 memory_store 存储图片相关信息"

### 测试 xiaoguan
1. 在飞书中向小冠发送图片
2. 发送消息："请分析这张图片，并存储相关信息到记忆中"

### 测试 echo
1. 在飞书中向艾可发送图片
2. 发送消息："请识别图片内容，并记录到记忆系统"

---

## 测试完成后

1. 收集所有 agent 的响应
2. 在 test_execution_log.md 中记录结果
3. 标记 ✅ 成功 或 ❌ 失败
4. 记录任何错误信息或异常行为
5. 总结发现的问题

---

## 常见问题排查

### 如果 memory 工具不工作：
1. 检查 openclaw.json 中 agent 的 tools.allow 列表
2. 检查 Mem0 插件是否启用
3. 检查环境变量 QDRANT_URL 和 QDRANT_API_KEY
4. 查看 OpenClaw 日志

### 如果 read 工具不工作：
1. 检查文件路径是否正确
2. 检查 agent 的 workspace 配置
3. 检查文件权限

### 如果 task 工具不工作：
1. 检查 feishu-task-plugin 是否启用
2. 检查用户 token 配置
3. 检查飞书 API 权限

---

## 测试时间估计

- 每个 agent 测试：5-10 分钟
- 总计：30-60 分钟
- 建议分批测试，避免疲劳

---

## 下一步

完成测试后，根据结果：
1. 修复发现的问题
2. 更新配置文件
3. 重新测试失败的功能
4. 编写测试报告
