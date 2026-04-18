# OpenClaw 知识库索引

## 目录结构

```
knowledge/
└── openclaw/
    ├── 01-architecture.md          # 架构概览
    ├── 02-agent-mechanism.md       # Agent 工作机制
    ├── 03-skills-development.md    # Skills 开发规范
    └── README.md                   # 本文件
```

## 学习路径

### 新手入门
1. 先读 `01-architecture.md` 了解整体架构
2. 再读 `02-agent-mechanism.md` 理解 Agent 如何工作
3. 最后读 `03-skills-development.md` 学习如何扩展能力

### 快速查询
- **配置相关**：查看 `01-architecture.md` 的"配置文件"章节
- **工具使用**：查看 `02-agent-mechanism.md` 的"工具系统"章节
- **Skill 开发**：查看 `03-skills-development.md`
- **最佳实践**：查看 `02-agent-mechanism.md` 的"最佳实践"章节

## 核心概念速查

### Gateway
- 地址：`ws://127.0.0.1:18789`
- 命令：`openclaw gateway start/stop/restart/status`
- 作用：路由、会话管理、消息分发

### Agent
- 配置：`openclaw.json` 中的 `agents.list`
- 工作空间：`workspace/{agent-id}/`
- 核心文件：SOUL.md、USER.md、MEMORY.md、AGENTS.md

### Skills
- 位置：内置 / 扩展 / 工作空间
- 结构：SKILL.md（必需）+ scripts/ + references/
- 触发：根据 description 自动匹配

### Tools
- 文件：read、write、edit、glob、grep
- 命令：bash、exec、process
- 会话：sessions_spawn、sessions_send
- 记忆：memory_store、memory_search、memory_forget

### Memory
- 每日日志：`memory/YYYY-MM-DD.md`
- 长期记忆：`MEMORY.md`
- 插件：openclaw-mem0（open-source 模式）

## 常用命令

```bash
# 查看状态
openclaw status
openclaw gateway status
openclaw agents list
openclaw skills list

# 管理服务
openclaw gateway start/stop/restart
openclaw gateway run  # 前台运行，方便调试

# 查看日志
openclaw logs --follow

# 配置管理
openclaw config file
openclaw config get agents.defaults.model.primary
openclaw config set agents.defaults.model.primary "new-model"

# Agent 管理
openclaw agents add <agent-id>
openclaw agents bind <agent-id> --channel feishu --account <account-id>
openclaw agents bindings

# Skills 管理
openclaw skills search <keyword>
openclaw skills install <skill-name>
openclaw skills update <skill-name>

# 会话管理
openclaw sessions list
openclaw message send --target <user-id> --message "Hello"

# 诊断工具
openclaw doctor
openclaw security audit
```

## 关键文件位置

```
openclaw-runtime/
├── openclaw.json                    # 主配置文件
├── agents/
│   └── laojin/
│       └── agent/
│           └── auth-profiles.json   # 认证配置
├── workspace/
│   └── laojin/
│       ├── SOUL.md                  # 人格定义
│       ├── USER.md                  # 用户信息
│       ├── MEMORY.md                # 长期记忆
│       ├── AGENTS.md                # 工作规范
│       ├── TOOLS.md                 # 工具配置
│       ├── HEARTBEAT.md             # 心跳任务
│       ├── memory/                  # 每日日志
│       ├── knowledge/               # 知识库
│       └── skills/                  # 自定义 skills
└── extensions/
    └── openclaw-*/
        └── skills/                  # 扩展 skills
```

## 学习资源

- **官方文档**：https://docs.openclaw.ai
- **本地文档**：`/opt/homebrew/lib/node_modules/openclaw/docs/`
- **社区**：https://discord.com/invite/clawd
- **技能市场**：https://clawhub.ai
- **源码**：https://github.com/openclaw/openclaw

## 更新记录

- **2026-04-05**：初始版本，基于 OpenClaw 2026.4.2
  - 完成架构概览
  - 完成 Agent 工作机制
  - 完成 Skills 开发规范

## 下一步计划

- [ ] 深入学习 Memory 系统（mem0 插件）
- [ ] 研究 ClawFlow 工作流编排
- [ ] 学习 Browser 工具的高级用法
- [ ] 研究多 Agent 协作模式
- [ ] 学习 Cron 定时任务配置
- [ ] 研究安全审计和权限管理
