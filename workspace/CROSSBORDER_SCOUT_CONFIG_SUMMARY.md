# 跨境雷达系统配置总结

## 更新日期
2026-03-13

## 核心变更

### 1. 调用关系调整
- ❌ 旧：由 aduan 通过 sessions_spawn 调用
- ✅ 新：由 xiaodong 负责调用和管理

### 2. 监测范围明确

#### 宏观层面（系统性风险）
- 法国公司注册
- 德国公司注册
- 欧盟税号（VAT）
- 支付、物流、合规政策

#### 微观层面（16 个平台）
- Cdiscount, Worten, Emag, 法国乐天, Bol, MediaMarkt
- 乐华梅兰, ManoMano, 速卖通, Allegro, Kaufland.de
- Conforama, BUT, Fnac, PCC, 法国 Coupang

### 3. 信息沉淀分层

#### 第一层：Mem0 知识库
- **内容：** 所有采集的情报
- **工具：** `memory_store`
- **用途：** 长期知识积累，可检索

#### 第二层：飞书多维表格
- **内容：** 高风险/立即影响的情报
- **位置：** `06_情报中心` → `06.1_跨境情报调研`
- **工具：** `feishu_bitable_create_record`
- **触发条件：**
  - 四大高风险：注册受阻、资金链、运营生存、政策窗口关闭
  - 立即影响：需求端变化、正在交付的订单受影响

### 4. 判定逻辑
- **由 xiaodong_crossborder_scout 自己判定**
- 判定内容：
  - 是否高风险
  - 是否立即影响生意
  - 是否适合公众号素材
  - 归属哪个分类

### 5. 通知机制
- 高风险/立即影响的情报写入飞书表格后
- 通过飞书私聊通知 xiaodong
- 通知内容：风险类型、影响范围、建议动作

### 6. 运行频率
- **每周自动执行**（由 xiaodong 调度）
- 或根据需要手动触发

## 已更新的文件

### xiaodong_crossborder_scout workspace
1. **AGENTS.md**
   - 更新调用方为 xiaodong
   - 明确两层沉淀策略
   - 更新飞书表格位置

2. **TOOLS.md**
   - 详细的宏观/微观监测清单
   - 两层沉淀策略说明
   - 判定逻辑流程图
   - 字段映射和写入规则

3. **HEARTBEAT.md**
   - 更新宏观雷达范围
   - 明确两层沉淀方式

### xiaodong workspace
1. **AGENTS.md**
   - 更新子 Agent 协作说明
   - 明确 xiaodong 负责调用 scout
   - 添加调用示例和情报处理流程

2. **TOOLS.md**
   - 添加跨境雷达调用快速指南
   - 关键原则说明

3. **CROSSBORDER_SCOUT_GUIDE.md**（新建）
   - 完整的调用指南
   - 调用时机和方式
   - 返回结果处理
   - 常见问题排查

### 共享文档
1. **FEISHU_BITABLE_CONFIG.md**（新建）
   - 飞书多维表格完整配置
   - 字段列表和类型
   - 4 个 Tab 视图配置
   - 权限配置
   - 使用流程和数据示例

## 飞书多维表格配置

### 表格信息
- **app_token:** `PthAwTfrViHCr5kS2xUc4gNLnEd`
- **table_id:** `tblR0Ox7ZZTEeZay`
- **位置：** `06_情报中心` → `06.1_跨境情报调研`

### 字段设计（13 个字段）
1. 分类（单选）：宏观风险/平台政策/高风险预警/行业动态
2. 平台或主题（文本）
3. 变化摘要（多行文本）
4. 对中国卖家的影响（多行文本）
5. 风险等级（单选）：低/中/高
6. 是否立即影响（单选）：是/否
7. 是否适合公众号（单选）：是/否
8. 来源链接1（超链接）
9. 来源链接2（超链接）
10. 来源链接3（超链接，可选）
11. 验证状态（单选）：已验证/待验证/同行反馈
12. 采集时间（日期时间）
13. 采集人（文本）

### 4 个 Tab 视图
1. **宏观风险** - 筛选分类=宏观风险
2. **平台政策** - 筛选分类=平台政策
3. **高风险预警** - 筛选分类=高风险预警或风险等级=高
4. **行业动态** - 筛选分类=行业动态

## 工作流程

```
用户请求跨境扫描
    ↓
xiaodong 调用 sessions_spawn
    ↓
xiaodong_crossborder_scout 执行扫描
    ├─ 宏观雷达：公司注册、税号、支付、物流
    └─ 微观雷达：16 个平台政策、风险
    ↓
采集情报
    ↓
所有情报 → Mem0（memory_store）
    ↓
判定：高风险/立即影响？
    ├─ 是 → 飞书多维表格 + 通知 xiaodong
    └─ 否 → 仅存 Mem0
    ↓
xiaodong 收到通知
    ↓
评估影响 → 决策动作
    ↓
xiaoguan 可读取表格找公众号素材
```

## 下一步行动

### 1. 配置飞书多维表格 ✓
- 创建表格和字段
- 配置 4 个 Tab 视图
- 设置权限

### 2. 测试完整流程
- xiaodong 手动触发一次扫描
- 验证 Mem0 存储
- 验证飞书表格写入
- 验证通知机制

### 3. 配置定时任务
- 设置 xiaodong 的 heartbeat 或 cron
- 每周自动执行一次扫描

### 4. 培训和文档
- 告知 xiaoguan 如何读取表格
- 说明公众号素材筛选方法

## 关键原则

1. **xiaodong 负责调用**，不是 aduan
2. **不要反问用户**，直接调用默认口径
3. **两层沉淀**，Mem0 全部 + 飞书表格高风险
4. **scout 自己判定**，不需要 xiaodong 二次判定
5. **及时通知**，高风险立即告知 xiaodong

## 文件位置

### xiaodong_crossborder_scout
```
/Users/xiaojiujiu2/.openclaw/workspace/xiaodong_crossborder_scout/
├── AGENTS.md          # 身份定义
├── TOOLS.md           # 详细 SOP
├── HEARTBEAT.md       # 心跳规则
├── SOUL.md            # 性格定义
├── USER.md            # 服务对象
└── IDENTITY.md        # 角色标识
```

### xiaodong
```
/Users/xiaojiujiu2/.openclaw/workspace/xiaodong/
├── AGENTS.md                      # 包含子 Agent 协作说明
├── TOOLS.md                       # 包含快速调用指南
└── CROSSBORDER_SCOUT_GUIDE.md     # 完整调用指南
```

### 共享文档
```
/Users/xiaojiujiu2/.openclaw/workspace/
└── FEISHU_BITABLE_CONFIG.md       # 飞书表格配置
```

---

**配置完成日期：** 2026-03-13
**配置人员：** Claude (Kiro)
**审核状态：** 待测试
