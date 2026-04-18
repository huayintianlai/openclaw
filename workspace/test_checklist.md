# 记忆系统测试 - 快速检查清单

## 测试日期：2026-03-13

---

## 快速测试清单

### Agent: xiaodong (小东)
- [ ] 飞书机器人可访问
- [ ] memory_store 工具可用
- [ ] memory_search 工具可用
- [ ] memory_list 工具可用
- [ ] read 工具可用
- [ ] tavily_search 工具可用
- [ ] xiaodong_task_create 工具可用
- [ ] 图片处理功能正常

**测试消息（复制粘贴）：**
```
测试记忆系统：
1. memory_store: "小红书 CPA 目标 50 元，ROI >= 2.0"
2. memory_search: "小红书 CPA"
3. memory_list: 列出所有记忆
4. read: /Users/xiaojiujiu2/.openclaw/workspace/xiaodong/AGENTS.md
5. 报告结果
```

**结果：**
```
[在此粘贴小东的回复]
```

---

### Agent: xiaodong_crossborder_scout (跨境雷达)
- [ ] 可通过 sessions_spawn 调用
- [ ] memory_store 工具可用
- [ ] memory_search 工具可用
- [ ] read 工具可用
- [ ] tavily_search 工具可用
- [ ] feishu_bitable 工具可用

**测试消息（通过 aduan 调用）：**
```
阿段，请 spawn xiaodong_crossborder_scout，让他测试：
1. memory_store: "Amazon VAT 新政 2026-03"
2. memory_search: "Amazon VAT"
3. read: AGENTS.md
4. 报告结果
```

**结果：**
```
[在此粘贴结果]
```

---

### Agent: finance (财务)
- [ ] 飞书机器人可访问
- [ ] memory_store 工具可用
- [ ] memory_search 工具可用
- [ ] memory_list 工具可用
- [ ] read 工具可用
- [ ] feishu_bitable_list_records 可用（只读）
- [ ] 确认无 write/edit 权限

**测试消息：**
```
测试记忆系统：
1. memory_store: "净利润预警阈值 30%"
2. memory_search: "净利润"
3. memory_list: 列出记忆
4. read: /Users/xiaojiujiu2/.openclaw/workspace/finance/AGENTS.md
5. 报告结果
```

**结果：**
```
[在此粘贴 finance 的回复]
```

---

### Agent: xiaoguan (小冠)
- [ ] 飞书机器人可访问
- [ ] memory_store 工具可用
- [ ] memory_search 工具可用
- [ ] read 工具可用
- [ ] xiaoguan_task_create 工具可用
- [ ] xiaoguan_task_list 工具可用
- [ ] feishu_bitable 读写功能正常

**测试消息：**
```
测试系统：
1. memory_store: "客户张三偏好：周末不打扰"
2. memory_search: "客户张三"
3. xiaoguan_task_create: "测试任务 - 跟进张三"
4. xiaoguan_task_list: 列出任务
5. read: AGENTS.md
6. 报告结果
```

**结果：**
```
[在此粘贴小冠的回复]
```

---

### Agent: aduan (ceo_aduan)
- [ ] 飞书机器人可访问
- [ ] read 工具可用
- [ ] sessions_spawn 工具可用
- [ ] sessions_list 工具可用
- [ ] sessions_history 工具可用
- [ ] knowledge_search 工具可用
- [ ] feishu_wiki_list_global 可用
- [ ] 确认无 memory 工具
- [ ] 确认无 write/edit 权限

**测试消息：**
```
测试你的工具：
1. read: HEARTBEAT.md
2. read: ADUAN_DATA_CONTRACT.md
3. sessions_list: 查看会话
4. knowledge_search: "公司通识"
5. 报告结果
```

**结果：**
```
[在此粘贴阿段的回复]
```

---

### Agent: echo (艾可)
- [ ] 飞书机器人可访问
- [ ] memory_store 工具可用
- [ ] memory_search 工具可用
- [ ] read 工具可用
- [ ] tavily_search 工具可用
- [ ] feishu_bitable 读写功能正常
- [ ] browser 工具可用

**测试消息：**
```
测试记忆系统：
1. memory_store: "Boss 喜欢简洁日报"
2. memory_search: "日报"
3. read: /Users/xiaojiujiu2/.openclaw/workspace/echo/AGENTS.md
4. tavily_search: "AI productivity 2026"
5. 报告结果
```

**结果：**
```
[在此粘贴艾可的回复]
```

---

## 图片处理测试

### 测试图片准备
创建一个包含以下内容的测试图片：
- 文字："OpenClaw Memory Test 2026-03-13"
- 简单图表或表格
- 二维码（可选）

### xiaodong 图片测试
- [ ] 发送图片成功
- [ ] 能识别图片内容
- [ ] 能存储图片相关记忆

**结果：**
```
[粘贴结果]
```

### xiaoguan 图片测试
- [ ] 发送图片成功
- [ ] 能识别图片内容
- [ ] 能存储图片相关记忆

**结果：**
```
[粘贴结果]
```

### echo 图片测试
- [ ] 发送图片成功
- [ ] 能识别图片内容
- [ ] 能存储图片相关记忆

**结果：**
```
[粘贴结果]
```

---

## 跨 Agent 记忆隔离测试

### 测试目的
验证不同 agent 的记忆是否正确隔离

### 测试步骤
1. 在 xiaodong 中存储："小东的秘密：测试数据 A"
2. 在 xiaoguan 中搜索："小东的秘密"
3. 预期：xiaoguan 不应该找到 xiaodong 的记忆

**结果：**
- [ ] 记忆隔离正常
- [ ] 记忆隔离失败（需要修复）

**详细记录：**
```
[粘贴测试结果]
```

---

## 记忆持久化测试

### 测试步骤
1. 在 xiaodong 中存储一条记忆
2. 等待 5 分钟
3. 重启 OpenClaw 容器
4. 再次在 xiaodong 中搜索该记忆

**结果：**
- [ ] 记忆持久化成功
- [ ] 记忆丢失（需要检查 Qdrant 配置）

**详细记录：**
```
[粘贴测试结果]
```

---

## 性能测试

### 记忆搜索响应时间
- xiaodong: _____ 秒
- xiaoguan: _____ 秒
- finance: _____ 秒
- echo: _____ 秒

### 文件读取响应时间
- xiaodong: _____ 秒
- xiaoguan: _____ 秒
- finance: _____ 秒
- aduan: _____ 秒

---

## 问题记录

### 发现的 Bug
1.
2.
3.

### 配置问题
1.
2.
3.

### 性能问题
1.
2.
3.

---

## 总体评分

| Agent | 记忆功能 | 文件功能 | 搜索功能 | 任务功能 | 图片功能 | 总分 |
|-------|---------|---------|---------|---------|---------|------|
| xiaodong | __/10 | __/10 | __/10 | __/10 | __/10 | __/50 |
| xiaodong_crossborder_scout | __/10 | __/10 | __/10 | N/A | N/A | __/30 |
| finance | __/10 | __/10 | N/A | N/A | N/A | __/20 |
| xiaoguan | __/10 | __/10 | __/10 | __/10 | __/10 | __/50 |
| aduan | N/A | __/10 | __/10 | N/A | N/A | __/20 |
| echo | __/10 | __/10 | __/10 | N/A | __/10 | __/40 |

---

## 测试结论

### ✅ 成功的功能


### ❌ 失败的功能


### ⚠️ 需要改进的功能


### 📝 建议


---

## 下一步行动

1. [ ] 修复发现的 Bug
2. [ ] 优化性能问题
3. [ ] 更新文档
4. [ ] 重新测试失败的功能
5. [ ] 编写最终测试报告

---

测试人员：___________
测试日期：2026-03-13
完成时间：___________
