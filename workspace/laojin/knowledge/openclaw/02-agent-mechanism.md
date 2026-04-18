# OpenClaw Agent 工作机制

## Agent 生命周期

### 1. 启动阶段
1. **加载配置**：从 `openclaw.json` 读取 agent 配置
2. **初始化工作空间**：读取 workspace 文件（AGENTS.md、SOUL.md、USER.md 等）
3. **加载 Skills**：根据 `<available_skills>` 扫描可用技能
4. **建立会话**：创建或恢复 session
5. **记忆召回**：如果启用 autoRecall，自动加载相关记忆

### 2. 消息处理流程
```
外部消息 → Channel → Gateway → Routing → Agent → Session
                                                    ↓
                                            Skill 匹配
                                                    ↓
                                            Tool 调用
                                                    ↓
                                            Memory 存储
                                                    ↓
                                            响应生成 → Channel → 用户
```

### 3. Skill 触发机制
- **自动触发**：根据 `<available_skills>` 中的 `<description>` 匹配
- **手动触发**：用户明确提到 skill 关键词
- **Skill 加载**：
  1. 扫描 description，判断是否匹配当前任务
  2. 如果匹配，使用 `read` 工具加载 `SKILL.md`
  3. 按照 SKILL.md 中的指令执行

### 4. Tool 调用约束
- **工具白名单**：`agents.list[].tools.allow` 定义允许的工具
- **沙箱模式**：
  - `off`: 无沙箱限制
  - `all`: 所有操作在沙箱中执行
- **工作空间限制**：`tools.fs.workspaceOnly=true` 限制文件操作在 workspace 内

## Agent 配置详解

### 基础配置
```json
{
  "id": "laojin",
  "name": "老金",
  "identity": {
    "name": "老金",
    "emoji": "👨💻"
  },
  "workspace": "/path/to/workspace/laojin",
  "agentDir": "/path/to/agents/laojin/agent",
  "model": "yunyi-claude/claude-opus-4-6"
}
```

### 模型配置
```json
{
  "model": {
    "primary": "yunyi-claude/claude-opus-4-6",
    "fallbacks": [
      "custom/gpt-5.4",
      "minimax/MiniMax-M2.5"
    ]
  }
}
```

### 心跳配置
```json
{
  "heartbeat": {
    "every": "30m",
    "target": "last",
    "directPolicy": "allow",
    "activeHours": {
      "start": "08:30",
      "end": "22:00",
      "timezone": "Asia/Shanghai"
    },
    "lightContext": true
  }
}
```

- `every`: 心跳间隔
- `target`: 心跳目标（`last` = 最后活跃的会话）
- `directPolicy`: 直接消息策略（`allow` = 允许）
- `activeHours`: 活跃时间段（避免深夜打扰）
- `lightContext`: 轻量级上下文（减少 token 消耗）

### 子 Agent 配置
```json
{
  "subagents": {
    "maxConcurrent": 8,
    "allowAgents": [
      "xiaodong_crossborder_scout",
      "xiaodong_ai_scout"
    ]
  }
}
```

## Workspace 文件规范

### 必读文件（Session 启动时）
1. **SOUL.md**：人格定义，决定说话风格和行为方式
2. **USER.md**：用户信息，了解服务对象
3. **memory/YYYY-MM-DD.md**：今天和昨天的工作日志
4. **MEMORY.md**（仅主会话）：长期记忆索引

### 可选文件
- **AGENTS.md**：工作规范和最佳实践
- **TOOLS.md**：工具配置笔记（SSH、摄像头等）
- **HEARTBEAT.md**：心跳任务清单
- **BOOTSTRAP.md**：首次启动指南（读完后删除）

### 记忆文件组织
```
workspace/laojin/
├── MEMORY.md              # 长期记忆索引
└── memory/
    ├── 2026-04-05.md      # 每日工作日志
    ├── 2026-04-04.md
    └── heartbeat-state.json  # 心跳状态追踪
```

## 工具系统

### 核心工具
- **文件操作**：`read`、`write`、`edit`、`glob`、`grep`
- **命令执行**：`bash`、`exec`、`process`
- **会话管理**：`sessions_spawn`、`sessions_send`
- **记忆管理**：`memory_store`、`memory_search`、`memory_forget`、`memory_list`
- **浏览器**：`browser`（支持 chrome-relay 和 user profile）
- **搜索**：`tavily_search`、`tavily_fetch`

### 飞书工具（laojin 可用）
- **多维表格**：`feishu_bitable_*`
- **文档**：`feishu_create_doc`、`feishu_update_doc`、`feishu_fetch_doc`
- **日历**：`feishu_calendar_*`
- **任务**：`feishu_task_*`
- **消息**：`feishu_im_*`

### Coding Agent 调用
- **工具**：`sessions_spawn`
- **可用 Agent**：
  - **Codex**：快速代码生成（需要 pty:true）
  - **Claude Code**：复杂架构分析（使用 --print --permission-mode bypassPermissions）
  - **Pi**：通用编程助手
- **使用场景**：
  - ✅ 多文件代码生成
  - ✅ 复杂架构设计
  - ✅ PR 审查（在临时目录）
  - ❌ 简单配置文件（<100行，直接生成）
  - ❌ 读取代码（使用 read 工具）

## 最佳实践

### 1. 需求把握度评估
在动手前评估三个维度：
- **技术理解度**：是否完全理解技术实现细节？
- **业务理解度**：是否理解需求在业务中的作用？
- **需求明确度**：需求描述是否足够具体？

**决策树**：
- 三个维度都 >= 80% → 直接行动
- 任一维度 < 80% → 一问一答确认

### 2. 记忆管理
- **每日日志**：记录到 `memory/YYYY-MM-DD.md`
- **长期记忆**：重要决策、经验教训更新到 `MEMORY.md`
- **定期整理**：通过 heartbeat 定期回顾和整理记忆

### 3. 代码生成原则
- **简单任务**（<100行）：直接生成
- **复杂任务**：调用 coding agent
- **架构设计**：调用 Claude Code
- **快速实现**：调用 Codex

### 4. 心跳任务
- **批量检查**：将多个定期检查合并到 heartbeat
- **轮换检查**：不同任务轮流执行，避免每次都检查所有
- **状态追踪**：使用 `heartbeat-state.json` 记录上次检查时间
- **主动工作**：利用 heartbeat 做后台整理（更新 MEMORY.md、git commit 等）

## 安全约束

### 文件操作
- **沙箱限制**：只能访问 workspace 目录
- **敏感文件**：不能读取 `/opt/homebrew/lib/node_modules/openclaw/` 等系统目录
- **权限检查**：`auth-profiles.json` 应该是 600 权限

### 外部操作
- **需要确认**：发送邮件、发推、公开发布
- **内部操作**：读文件、搜索、组织工作空间可自由进行
- **群聊谨慎**：在群聊中不要泄露用户私密信息

### 工具使用
- **白名单机制**：只能使用 `tools.allow` 中列出的工具
- **审批机制**：某些敏感操作需要用户审批（通过 `/approve` 命令）
