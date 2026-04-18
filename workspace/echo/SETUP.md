# Echo Agent 配置总结

## 已完成

### 1. 工作区初始化 ✅
- 创建 `/instances/kentclaw/data/workspace/echo/` 目录
- 配置核心文件：
  - `SOUL.md` - Echo 的身份和价值观
  - `USER.md` - 用户信息（小九九）
  - `AGENTS.md` - 工作流程和职责说明
  - `TOOLS.md` - 工具使用指南
  - `MEMORY.md` - 长期记忆
  - `memory/2026-03-13.md` - 今日记录

### 2. GoldFinger CLI 集成 ✅
- 创建软链接：`/workspace/echo/goldfinger` → GoldFinger CLI
- Echo 可以通过 `exec` 工具调用：
  ```bash
  goldfinger collect "关键词"
  goldfinger status
  goldfinger schedules
  ```

### 3. OpenClaw Agent 配置 ✅
- 在 `openclaw.json` 中添加 Echo Agent
- 配置工具权限：
  - 飞书多维表格读写
  - 浏览器自动化
  - exec 执行命令
  - 知识库搜索
  - 记忆系统

### 4. Heartbeat 配置 ✅
- 每 24 小时自动检查
- 工作时间：09:00-21:00（Asia/Shanghai）
- 自动提醒：待审核客户、公众号发布、采集任务状态

---

## 待完成

### 1. 飞书机器人配置 ⏳
**需要用户提供**：
- `FEISHU_ECHO_APP_ID` - Echo 飞书机器人的 APP ID
- `FEISHU_ECHO_APP_SECRET` - Echo 飞书机器人的 APP SECRET

**添加位置**：
```bash
# /instances/kentclaw/.env
FEISHU_ECHO_APP_ID=cli_xxxxx
FEISHU_ECHO_APP_SECRET=xxxxx
```

**openclaw.json 配置**：
```json
{
  "channels": {
    "feishu": {
      "accounts": {
        "echo": {
          "appId": "${FEISHU_ECHO_APP_ID}",
          "appSecret": "${FEISHU_ECHO_APP_SECRET}",
          "botName": "艾可",
          "enabled": true,
          "dmPolicy": "allowlist",
          "allowFrom": ["ou_dc95eabe8982323faf7e9f3701e61e22"],
          "groupPolicy": "allowlist",
          "groupAllowFrom": ["oc_660c980239cd01d78c7dfe45d1a2d944"],
          "requireMention": true
        }
      }
    }
  },
  "bindings": [
    {
      "agentId": "echo",
      "match": {
        "channel": "feishu",
        "accountId": "echo"
      }
    }
  ]
}
```

### 2. GoldFinger 环境变量 ⏳
**需要配置**：
```bash
# /instances/kentclaw/.env
GOLDFINGER_API_URL=http://localhost:8000  # 或 Docker 内部地址
```

### 3. 公众号自动化排版脚本 ⏳
- 需要编写 Playwright 脚本
- 参考 GoldFinger 的浏览器自动化实现
- 实现功能：
  - 登录公众号后台
  - 创建图文素材
  - 自动排版（标题、正文、图片）
  - 预览和发布

### 4. 飞书多维表格确认 ⏳
**需要确认**：
- GoldFinger 潜力笔记池的 `table_id`（TOOLS.md 中标记为"需确认"）
- 是否需要为 Echo 创建单独的内容日历表格

---

## 架构总结

### 角色定位

```
┌─────────────────────────────────────┐
│  Echo (OpenClaw Agent)              │
│  - 决策中枢                          │
│  - 内容创作                          │
│  - 任务调度                          │
│  - 数据分析                          │
└─────────────────────────────────────┘
              ↓ HTTP API / CLI
┌─────────────────────────────────────┐
│  GoldFinger (RPA 引擎)              │
│  - 浏览器自动化                      │
│  - 小红书采集                        │
│  - 自动回复                          │
│  - 数据持久化                        │
└─────────────────────────────────────┘
```

### 数据流

**采集流程**：
```
Echo 决策（关键词、筛选条件）
  ↓
goldfinger CLI 调用
  ↓
GoldFinger 执行采集
  ↓
写入 PostgreSQL + 飞书多维表格
  ↓
Echo 读取飞书表格分析结果
  ↓
审核意向客户和回复话术
  ↓
批准后 GoldFinger 自动回复
```

**公众号流程**：
```
飞书 06_情报中心（跨境情报）
  ↓
Echo 读取并分析
  ↓
结合小红书热点（GoldFinger 采集）
  ↓
撰写文章草稿
  ↓
browser 工具自动化排版
  ↓
发布到公众号
  ↓
记录到内容日历
```

### 职责划分

**Echo 负责**：
- ✅ 决定什么时候采集、采集什么关键词
- ✅ 公众号选题策划和文章撰写
- ✅ 审核 AI 生成的回复话术
- ✅ 分析获客数据，优化策略
- ✅ 公众号自动化排版（通过 browser 工具）

**GoldFinger 负责**：
- ✅ 浏览器自动化（Playwright）
- ✅ 小红书笔记和评论采集
- ✅ AI 识别意向客户
- ✅ 自动发送私信回复
- ✅ 数据持久化到 PostgreSQL 和飞书

**明确边界**：
- Echo 不直接操作浏览器采集（那是 GoldFinger 的工作）
- GoldFinger 不做决策（只执行 Echo 下发的任务）
- Echo 通过 CLI 或 HTTP API 调用 GoldFinger

---

## 下一步行动

### 立即需要（用户提供）
1. **飞书 Echo 机器人凭证**
   - APP_ID
   - APP_SECRET
   - 用户 Open ID（用于 allowFrom 配置）

2. **确认 GoldFinger 部署方式**
   - 本地运行？Docker 运行？
   - API 地址是什么？

### 后续开发
1. **测试 Echo Agent**
   - 重启 OpenClaw 服务
   - 在飞书中 @艾可 测试响应
   - 测试 goldfinger CLI 调用

2. **开发公众号排版脚本**
   - 编写 Playwright 脚本
   - 集成到 Echo 工作流

3. **数据分析功能**
   - 文章阅读量跟踪
   - 获客转化率分析
   - 关键词效果评估

---

## 技术细节

### GoldFinger CLI 调用示例

```bash
# Echo 通过 exec 工具执行
exec("cd /Users/xiaojiujiu2/.openclaw/workspace/echo && ./goldfinger collect 'cdiscount'")

# 或者设置环境变量后直接调用
export GOLDFINGER_API_URL=http://localhost:8000
exec("goldfinger collect 'cdiscount'")
```

### 飞书表格操作示例

```python
# 读取情报中心
feishu_bitable_list_records(
    app_token="PthAwTfrViHCr5kS2xUc4gNLnEd",
    table_id="tblR0Ox7ZZTEeZay",
    filter='CurrentValue.[验证状态] = "已验证"',
    page_size=20
)

# 读取意向客户
feishu_bitable_list_records(
    app_token="PClsbQNDJaj4oks2YfQcXVGxnnf",
    table_id="tbldDJnE3nkErnim",
    filter='CurrentValue.[审核状态] = "待审核"'
)

# 更新审核状态
feishu_bitable_update_record(
    app_token="PClsbQNDJaj4oks2YfQcXVGxnnf",
    table_id="tbldDJnE3nkErnim",
    record_id="recXXXX",
    fields={"审核状态": "已批准"}
)
```

---

## 总结

Echo 的架构设计遵循了你的原则：
- ✅ **优先配置，后写代码**：复用 OpenClaw 原生能力（Agent、Tools、Heartbeat）
- ✅ **最小改动**：只添加 Echo Agent 配置，不修改现有架构
- ✅ **兼容现有架构**：与其他 Agent 协作，共享飞书多维表格
- ✅ **基于事实**：所有配置基于 OpenClaw 3.8 文档和现有项目实现

Echo 和 GoldFinger 的角色定位清晰：
- **Echo = 大脑**：决策、创作、分析
- **GoldFinger = 手脚**：执行、采集、自动化

这样的架构既保持了灵活性，又避免了职责混乱。
