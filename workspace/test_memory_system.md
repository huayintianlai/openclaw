# Memory System Test Plan (2026-03-13)

## 测试目标

验证 Mem0 记忆系统在各个 agent 中的功能完整性：
1. 记忆存储能力（memory_store）
2. 记忆检索能力（memory_search）
3. 记忆列表能力（memory_list）
4. 记忆遗忘能力（memory_forget）
5. 文件读取能力（read）
6. 图片处理能力（如果支持）

## 测试矩阵

| Agent ID | 记忆工具 | 文件工具 | 搜索工具 | 飞书工具 | 任务工具 |
|----------|---------|---------|---------|---------|---------|
| xiaodong | ✓ | ✓ | ✓ | ✓ | ✓ |
| xiaodong_crossborder_scout | ✓ | ✓ | ✓ | Bitable only | ✗ |
| xiaodong_ai_scout | ✓ | ✓ | ✓ | ✗ | ✗ |
| xiaoguan | ✓ | ✓ | ✓ | ✓ | ✓ |
| finance | ✓ | ✓ | ✗ | Bitable read-only | ✗ |
| aduan | ✗ | ✓ | ✗ | Wiki read-only | ✗ |
| echo | ✓ | ✓ | ✓ | ✓ | ✗ |

## 测试场景设计

### 场景 1: xiaodong - 全功能测试
**测试内容：**
1. 存储记忆：记住一个小红书投放策略
2. 检索记忆：查询之前存储的策略
3. 文件读取：读取 workspace 中的配置文件
4. 搜索能力：搜索最新的小红书投放趋势
5. 任务创建：创建一个测试任务

**预期结果：** 所有功能正常工作

### 场景 2: xiaodong_crossborder_scout - 跨境情报测试
**测试内容：**
1. 存储记忆：记住一个 Amazon 政策变化
2. 检索记忆：查询之前的政策记录
3. 文件读取：读取 AGENTS.md
4. Bitable 操作：查询情报中心表格元数据
5. 搜索能力：搜索跨境电商最新政策

**预期结果：** 记忆和搜索正常，Bitable 工具可用

### 场景 3: finance - 只读测试
**测试内容：**
1. 存储记忆：记住一个财务指标阈值
2. 检索记忆：查询之前的阈值
3. 文件读取：读取财务数据文件
4. Bitable 读取：查询飞书表格数据

**预期结果：** 记忆和读取正常，无写入权限

### 场景 4: xiaoguan - 客户管理测试
**测试内容：**
1. 存储记忆：记住一个客户偏好
2. 检索记忆：查询客户历史
3. 任务管理：创建跟进任务
4. Bitable 操作：读写客户数据表

**预期结果：** 全功能正常

### 场景 5: aduan - 战略调度测试
**测试内容：**
1. 文件读取：读取 HEARTBEAT.md 和 ADUAN_DATA_CONTRACT.md
2. 飞书 Wiki：全局只读知识库
3. sessions_spawn：调度子 agent
4. sessions_history：查询历史会话

**预期结果：** 只读和调度功能正常，无记忆工具

## 测试数据准备

### 测试记忆内容
- xiaodong: "小红书 CPA 目标控制在 50 元以内，ROI >= 2.0"
- xiaodong_crossborder_scout: "Amazon 2026-03 新政：VAT 合规要求加强"
- finance: "净利润预警阈值：较基线下降 30%"
- xiaoguan: "客户张三偏好：周末不打扰，工作日 10-18 点联系"
- echo: "Boss 喜欢简洁的日报格式，不要过多细节"

### 测试文件路径
- xiaodong: `/Users/xiaojiujiu2/.openclaw/workspace/xiaodong/AGENTS.md`
- xiaodong_crossborder_scout: `/Users/xiaojiujiu2/.openclaw/workspace/xiaodong_crossborder_scout/AGENTS.md`
- finance: `/Users/xiaojiujiu2/.openclaw/workspace/finance/AGENTS.md`
- xiaoguan: `/Users/xiaojiujiu2/.openclaw/workspace/xiaoguan/AGENTS.md`
- aduan: `/Users/xiaojiujiu2/.openclaw/workspace/aduan/HEARTBEAT.md`

## 执行顺序

1. xiaodong（最全功能）
2. xiaodong_crossborder_scout（跨境专用）
3. finance（只读限制）
4. xiaoguan（客户管理）
5. aduan（战略调度）

## 成功标准

- ✅ 记忆存储后能成功检索
- ✅ 文件读取返回正确内容
- ✅ 权限边界正确执行（该拒绝的拒绝）
- ✅ 搜索工具返回相关结果
- ✅ 任务工具正常创建和查询

## 失败处理

- 记录失败的 agent 和功能
- 检查 openclaw.json 配置
- 检查环境变量
- 检查插件状态
