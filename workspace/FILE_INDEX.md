# 📋 测试文件索引

## 文件清单（共 9 个文件）

| 文件名 | 大小 | 用途 | 优先级 |
|--------|------|------|--------|
| **README_TEST.md** | 5.7K | 总览和快速导航 | ⭐⭐⭐ |
| **START_HERE.md** | 6.1K | 快速启动指南 | ⭐⭐⭐ |
| **test_checklist.md** | 6.0K | 快速检查清单（推荐） | ⭐⭐⭐ |
| **test_guide.md** | 6.4K | 详细操作步骤 | ⭐⭐ |
| **troubleshooting_guide.md** | 9.4K | 问题排查指南 | ⭐⭐ |
| **test_final_report.md** | 6.1K | 最终报告模板 | ⭐⭐ |
| **test_execution_log.md** | 3.8K | 详细执行日志 | ⭐ |
| **test_memory_system.md** | 3.7K | 测试计划 | ⭐ |
| **pre_test_check.sh** | 5.4K | 预检查脚本（已执行✅） | ⭐ |

---

## 使用流程

### 🎯 快速测试流程（推荐）

```
1. 阅读 README_TEST.md（2 分钟）
   ↓
2. 打开 test_checklist.md（开始测试）
   ↓
3. 按照清单逐个测试 Agent
   ↓
4. 遇到问题查看 troubleshooting_guide.md
   ↓
5. 完成后填写 test_final_report.md
```

### 📚 完整测试流程

```
1. 阅读 START_HERE.md（5 分钟）
   ↓
2. 阅读 test_guide.md（10 分钟）
   ↓
3. 使用 test_execution_log.md 记录详细过程
   ↓
4. 参考 test_memory_system.md 了解测试目标
   ↓
5. 遇到问题查看 troubleshooting_guide.md
   ↓
6. 完成后填写 test_final_report.md
```

---

## 文件详细说明

### 📘 README_TEST.md
**用途：** 测试包总览
**内容：**
- 系统状态确认
- 文件清单
- 快速开始 3 步
- 测试重点
- 成功标准

**何时使用：** 第一次打开，了解整体情况

---

### 🚀 START_HERE.md
**用途：** 快速启动指南
**内容：**
- 3 种测试方案（完整/快速/单点）
- 测试消息模板（复制粘贴）
- 时间规划
- 测试入口

**何时使用：** 准备开始测试时

---

### ✅ test_checklist.md ⭐ 推荐
**用途：** 快速检查清单
**内容：**
- 每个 Agent 的测试清单
- 复制粘贴测试消息
- 结果勾选框
- 图片测试
- 记忆隔离测试
- 总体评分表

**何时使用：** 执行测试时的主要记录文件

---

### 📖 test_guide.md
**用途：** 详细操作步骤
**内容：**
- 每个 Agent 的完整测试流程
- 预期行为说明
- 测试消息模板
- 图片处理指南

**何时使用：** 需要详细指导时

---

### 🔧 troubleshooting_guide.md
**用途：** 问题排查和修复
**内容：**
- 7 大类常见问题
- 诊断步骤
- 快速修复命令
- 性能优化建议
- 测试后清理

**何时使用：** 遇到问题时

---

### 📊 test_final_report.md
**用途：** 最终测试报告
**内容：**
- 执行摘要
- 功能矩阵
- 性能数据
- 问题汇总
- 配置建议
- 下一步行动

**何时使用：** 测试完成后

---

### 📝 test_execution_log.md
**用途：** 详细执行日志
**内容：**
- 每个 Agent 的测试模板
- 详细记录空间
- 图片测试记录

**何时使用：** 需要详细记录每个步骤时

---

### 📋 test_memory_system.md
**用途：** 测试计划
**内容：**
- 测试目标
- 测试矩阵
- 测试场景设计
- 测试数据准备
- 成功标准

**何时使用：** 了解测试背景和目标时

---

### 🔍 pre_test_check.sh
**用途：** 系统预检查
**内容：**
- Docker 容器检查
- 环境变量检查
- 配置文件检查
- Workspace 检查
- 网络连接测试

**状态：** ✅ 已执行，所有检查通过

---

## 快速参考

### 我想...

#### 快速开始测试
→ 打开 **START_HERE.md** 或 **test_checklist.md**

#### 了解详细步骤
→ 打开 **test_guide.md**

#### 记录测试结果
→ 使用 **test_checklist.md**（推荐）或 **test_execution_log.md**

#### 解决问题
→ 查看 **troubleshooting_guide.md**

#### 编写最终报告
→ 填写 **test_final_report.md**

#### 了解测试目标
→ 阅读 **test_memory_system.md**

---

## 测试消息快速复制

### xiaodong
```
测试记忆系统：
1. memory_store: "小红书 CPA 目标 50 元，ROI >= 2.0"
2. memory_search: "小红书 CPA"
3. memory_list: 列出所有记忆
4. read: /Users/xiaojiujiu2/.openclaw/workspace/xiaodong/AGENTS.md
5. 报告结果
```

### finance
```
测试记忆系统：
1. memory_store: "净利润预警阈值 30%"
2. memory_search: "净利润"
3. memory_list: 列出记忆
4. 报告结果
```

### aduan
```
测试工具：
1. read: HEARTBEAT.md
2. sessions_list: 查看会话
3. knowledge_search: "公司通识"
4. 报告结果
```

---

## 文件位置

```
/Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/workspace/
├── README_TEST.md              # 总览
├── START_HERE.md               # 快速启动
├── test_checklist.md           # 检查清单 ⭐
├── test_guide.md               # 详细指南
├── test_execution_log.md       # 执行日志
├── test_memory_system.md       # 测试计划
├── test_final_report.md        # 最终报告
├── troubleshooting_guide.md    # 问题排查
└── pre_test_check.sh           # 预检查脚本 ✅
```

---

## 下一步

1. **现在就开始：** 打开 test_checklist.md
2. **需要指导：** 先看 START_HERE.md
3. **了解背景：** 阅读 README_TEST.md

---

**所有准备工作已完成，系统状态良好，可以开始测试！** 🚀
