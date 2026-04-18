# 🎯 记忆系统功能测试 - 完整准备包

## ✅ 系统状态

**预检查结果：全部通过 ✓**

- Docker 容器运行正常
- 环境变量配置完整
- Mem0 插件已启用
- 所有 Agent 配置正确
- Workspace 目录完整
- Qdrant 连接正常

**你可以立即开始测试！**

---

## 📦 已准备的测试文件

### 1. **START_HERE.md** ⭐ 从这里开始
- 快速启动指南
- 三种测试方案（完整/快速/单点）
- 测试消息模板
- 时间规划

### 2. **test_checklist.md** ⭐ 推荐使用
- 快速检查清单
- 简洁的测试记录表格
- 复制粘贴测试消息
- 结果勾选框

### 3. **test_guide.md**
- 详细操作步骤
- 每个 Agent 的测试流程
- 预期行为说明
- 图片测试指南

### 4. **test_execution_log.md**
- 详细的执行日志模板
- 每个步骤的记录空间
- 适合完整测试

### 5. **test_memory_system.md**
- 测试计划和目标
- 测试矩阵
- 测试场景设计
- 成功标准

### 6. **troubleshooting_guide.md**
- 问题诊断树
- 常见问题排查
- 快速修复命令
- 性能优化建议

### 7. **test_final_report.md**
- 最终报告模板
- 功能矩阵
- 性能数据统计
- 问题汇总

### 8. **pre_test_check.sh** ✅ 已执行
- 系统预检查脚本
- 自动验证配置
- 已确认系统就绪

---

## 🚀 快速开始（3 步）

### 步骤 1：选择测试方案

#### 方案 A：快速验证（推荐，20 分钟）
测试 3 个核心 Agent：
- **xiaodong**（全功能）
- **finance**（只读限制）
- **aduan**（战略调度）

#### 方案 B：完整测试（60 分钟）
测试所有 6 个 Agent + 图片处理

#### 方案 C：单点测试（5 分钟）
只测试 xiaodong 的记忆功能

---

### 步骤 2：打开测试文件

```bash
# 在 VSCode 中打开快速检查清单
code /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/workspace/test_checklist.md
```

或者直接在文件浏览器中打开：
`/Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/workspace/test_checklist.md`

---

### 步骤 3：开始测试

#### 测试 xiaodong（5 分钟）

1. 打开飞书，找到"小东"机器人
2. 发送以下消息：

```
测试记忆系统：
1. memory_store: "小红书 CPA 目标 50 元，ROI >= 2.0"
2. memory_search: "小红书 CPA"
3. memory_list: 列出所有记忆
4. read: /Users/xiaojiujiu2/.openclaw/workspace/xiaodong/AGENTS.md
5. 报告结果
```

3. 等待小东回复
4. 在 test_checklist.md 中记录结果

#### 测试 finance（3 分钟）

1. 打开飞书，找到"Finance Bot"机器人
2. 发送以下消息：

```
测试记忆系统：
1. memory_store: "净利润预警阈值 30%"
2. memory_search: "净利润"
3. memory_list: 列出记忆
4. 报告结果
```

3. 在 test_checklist.md 中记录结果

#### 测试 aduan（3 分钟）

1. 打开飞书，找到"ceo_aduan"机器人
2. 发送以下消息：

```
测试工具：
1. read: HEARTBEAT.md
2. sessions_list: 查看会话
3. knowledge_search: "公司通识"
4. 报告结果
```

3. 在 test_checklist.md 中记录结果

---

## 📊 测试重点

### 核心功能（必测）
- ✅ memory_store - 记忆存储
- ✅ memory_search - 记忆检索
- ✅ read - 文件读取
- ✅ 飞书机器人响应

### 扩展功能（可选）
- ⭐ task 工具（xiaodong, xiaoguan）
- ⭐ tavily_search（xiaodong, echo）
- ⭐ sessions_spawn（aduan）
- ⭐ 图片处理（xiaodong, xiaoguan, echo）

---

## 🎯 成功标准

### 最低标准（必须通过）
- ✅ 至少 3 个 Agent 的 memory 工具正常
- ✅ 所有 Agent 的 read 工具正常
- ✅ 飞书机器人响应正常（< 5 秒）

### 理想标准（期望通过）
- ✅ 所有 memory 工具正常
- ✅ 记忆隔离正确
- ✅ 任务工具正常
- ✅ 无明显性能问题

---

## 🐛 遇到问题？

### 快速修复

#### 机器人不回复
```bash
cd /Users/xiaojiujiu2/Documents/openclaw-docker
docker-compose restart openclaw
```

#### 查看日志
```bash
docker logs -f kentclaw-openclaw-1
```

#### 详细排查
打开 `troubleshooting_guide.md` 查看完整的问题排查步骤

---

## 📝 测试记录

### 推荐流程
1. 在 `test_checklist.md` 中勾选完成项
2. 粘贴 Agent 的回复
3. 记录发现的问题
4. 完成后填写 `test_final_report.md`

---

## 📞 需要帮助？

### 文档索引
- **快速开始** → START_HERE.md
- **测试步骤** → test_guide.md
- **快速记录** → test_checklist.md
- **问题排查** → troubleshooting_guide.md
- **最终报告** → test_final_report.md

### 关键命令
```bash
# 查看容器状态
docker ps | grep kentclaw

# 查看日志
docker logs kentclaw-openclaw-1 --tail 100

# 重启容器
cd /Users/xiaojiujiu2/Documents/openclaw-docker
docker-compose restart openclaw

# 进入容器
docker exec -it kentclaw-openclaw-1 sh
```

---

## ✨ 测试完成后

1. 填写 `test_final_report.md`
2. 记录发现的问题
3. 如有需要，修复配置
4. 重新测试失败的功能

---

## 🎉 现在开始测试！

**第一步：** 打开 `START_HERE.md` 或 `test_checklist.md`

**第二步：** 打开飞书，找到"小东"机器人

**第三步：** 发送第一条测试消息

**预计时间：** 20-60 分钟（根据选择的方案）

---

## 📂 文件位置

所有测试文件都在：
```
/Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/workspace/
```

文件列表：
- START_HERE.md
- test_checklist.md ⭐
- test_guide.md
- test_execution_log.md
- test_memory_system.md
- troubleshooting_guide.md
- test_final_report.md
- pre_test_check.sh

---

**祝测试顺利！** 🚀

如果一切正常，你将看到：
- ✅ 记忆存储和检索流畅
- ✅ 文件读取快速准确
- ✅ 机器人响应及时
- ✅ 工具调用正常

**现在就开始吧！**
