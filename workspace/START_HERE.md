# 🚀 记忆系统测试 - 快速启动指南

## ✅ 预检查结果：全部通过！

系统状态良好，可以开始测试。

---

## 📋 测试文件清单

已为你准备好以下测试文件：

1. **test_memory_system.md** - 测试计划和测试矩阵
2. **test_execution_log.md** - 详细的测试执行日志模板
3. **test_guide.md** - 完整的操作步骤指南
4. **test_checklist.md** - 快速检查清单（推荐使用）
5. **troubleshooting_guide.md** - 问题排查和修复指南
6. **pre_test_check.sh** - 预检查脚本（已执行）

---

## 🎯 推荐测试流程

### 方案 A：完整测试（60 分钟）
适合首次测试或全面验证

1. 打开 `test_guide.md`
2. 按顺序测试所有 6 个 agent
3. 在 `test_execution_log.md` 中记录详细结果
4. 执行图片处理测试
5. 执行记忆隔离测试
6. 执行持久化测试

### 方案 B：快速测试（20 分钟）⭐ 推荐
适合快速验证核心功能

1. 打开 `test_checklist.md`
2. 只测试 3 个核心 agent：
   - xiaodong（全功能）
   - finance（只读限制）
   - aduan（战略调度）
3. 在 checklist 中勾选完成项
4. 记录关键问题

### 方案 C：单点测试（5 分钟）
适合验证特定功能

1. 选择一个 agent（推荐 xiaodong）
2. 只测试记忆功能：store → search → list
3. 快速验证是否正常

---

## 📱 测试入口

### 飞书机器人列表

| Agent | 机器人名称 | 测试重点 |
|-------|-----------|---------|
| xiaodong | 小东 | 全功能测试 |
| xiaoguan | 小冠 | 任务管理 |
| finance | Finance Bot | 只读权限 |
| aduan | ceo_aduan | 调度能力 |
| echo | 艾可 | 综合功能 |

### 快速测试消息（复制粘贴）

#### 测试 xiaodong（5 分钟）
```
测试记忆系统：
1. memory_store: "小红书 CPA 目标 50 元，ROI >= 2.0"
2. memory_search: "小红书 CPA"
3. memory_list: 列出所有记忆
4. 报告结果
```

#### 测试 finance（3 分钟）
```
测试记忆系统：
1. memory_store: "净利润预警阈值 30%"
2. memory_search: "净利润"
3. 报告结果
```

#### 测试 aduan（3 分钟）
```
测试工具：
1. read: HEARTBEAT.md
2. sessions_list: 查看会话
3. 报告结果
```

---

## 🎨 测试图片准备（可选）

如果要测试图片处理功能，准备一张包含以下内容的图片：

```
┌─────────────────────────────────┐
│  OpenClaw Memory Test           │
│  Date: 2026-03-13               │
│                                 │
│  Test Items:                    │
│  ✓ Image Recognition            │
│  ✓ Text Extraction              │
│  ✓ Memory Storage               │
│                                 │
│  Status: Testing...             │
└─────────────────────────────────┘
```

或者使用任何包含文字的截图。

---

## 📊 成功标准

### 最低要求（必须通过）
- ✅ xiaodong 的 memory_store 和 memory_search 正常
- ✅ finance 的 memory 工具正常
- ✅ aduan 的 read 和 sessions_list 正常
- ✅ 飞书机器人响应及时（< 5 秒）

### 理想目标（期望通过）
- ✅ 所有 agent 的记忆功能正常
- ✅ 任务工具正常（xiaodong, xiaoguan）
- ✅ 图片处理正常
- ✅ 记忆隔离正确
- ✅ 无明显性能问题

---

## 🐛 遇到问题？

### 立即查看
1. **troubleshooting_guide.md** - 详细的问题排查步骤
2. 容器日志：`docker logs -f kentclaw-openclaw-1`
3. 检查飞书机器人是否在线

### 常见问题快速修复

#### 问题：机器人不回复
```bash
# 重启容器
cd /Users/xiaojiujiu2/Documents/openclaw-docker
docker-compose restart openclaw
```

#### 问题：memory 工具不可用
检查 openclaw.json 中的 tools.allow 列表是否包含：
- memory_store
- memory_search
- memory_list
- memory_forget

#### 问题：文件读取失败
确保使用容器内路径：
- ✅ `/Users/xiaojiujiu2/.openclaw/workspace/xiaodong/AGENTS.md`
- ❌ `/Users/xiaojiujiu2/Documents/...`

---

## 📝 测试记录

### 推荐使用 test_checklist.md
这是最简洁的测试记录方式：
- 勾选完成项
- 粘贴 agent 回复
- 记录问题

### 或使用 test_execution_log.md
如果需要详细记录：
- 每个步骤的结果
- 错误信息
- 性能数据

---

## ⏱️ 时间规划

| 测试阶段 | 预计时间 | 说明 |
|---------|---------|------|
| 预检查 | 已完成 ✅ | 系统状态良好 |
| xiaodong 测试 | 5-10 分钟 | 全功能测试 |
| finance 测试 | 3-5 分钟 | 只读测试 |
| xiaoguan 测试 | 5-10 分钟 | 任务管理测试 |
| aduan 测试 | 3-5 分钟 | 调度测试 |
| echo 测试 | 5-10 分钟 | 综合测试 |
| 图片测试 | 10-15 分钟 | 可选 |
| 问题修复 | 视情况而定 | 如有问题 |
| **总计** | **20-60 分钟** | 根据方案选择 |

---

## 🎯 现在开始！

### 第一步：选择测试方案
- [ ] 方案 A：完整测试（60 分钟）
- [ ] 方案 B：快速测试（20 分钟）⭐
- [ ] 方案 C：单点测试（5 分钟）

### 第二步：打开测试文件
```bash
# 在 VSCode 中打开
code /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/workspace/test_checklist.md
```

### 第三步：打开飞书
找到对应的机器人，开始发送测试消息

### 第四步：记录结果
在 test_checklist.md 中勾选和记录

### 第五步：处理问题
如有问题，查看 troubleshooting_guide.md

---

## 📞 需要帮助？

如果测试过程中遇到任何问题：

1. 先查看 **troubleshooting_guide.md**
2. 检查容器日志
3. 尝试重启容器
4. 记录详细的错误信息

---

## ✨ 测试完成后

1. 在 test_checklist.md 中填写总体评分
2. 记录发现的问题
3. 如有需要，提交 bug 报告
4. 清理测试数据（可选）

---

**祝测试顺利！** 🎉

如果一切正常，你将看到：
- ✅ 记忆存储和检索流畅
- ✅ 文件读取快速准确
- ✅ 机器人响应及时
- ✅ 工具调用正常

现在就开始吧！打开飞书，找到"小东"机器人，发送第一条测试消息。
