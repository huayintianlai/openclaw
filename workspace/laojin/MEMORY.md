# MEMORY.md - 记忆索引

本文件用于索引老金的长期记忆。

## 记忆类型

### 项目记忆
- 存储在 `projects/{project-name}/` 目录
- 包含架构设计、技术决策、技术债务等

### 技术知识
- 存储在 `knowledge/` 目录
- 包含最佳实践、设计模式、问题排查手册

### 业务理解
- 定期从飞书知识库同步
- 确保技术决策符合业务方向

## 工作方式纠正（2026-04-05）

**重要：代码生成的正确方式**
- ❌ 错误：我自己直接用 write 工具生成代码
- ✅ 正确：通过 `sessions_spawn` 调用 coding agent
  - **Codex**：快速代码生成（如 JWT 中间件、配置文件）
  - **Claude Code**：复杂架构分析和设计
  - **调用方式**：使用 `sessions_spawn` 工具，而非直接写代码

**示例场景**：
- 生成 JWT 中间件 → 调用 Codex
- 多租户 SaaS 认证架构设计 → 调用 Claude Code
- 简单配置文件（<100行）→ 我可以直接生成
- 复杂业务逻辑代码 → 调用 Codex

**实际经验（2026-04-05）**：
- Codex 可能遇到 API 额度问题
- 简单配置文件（如 Redis 连接配置）直接生成更高效
- 复杂架构设计和多文件代码生成才需要 coding agent

## 工作习惯：需求把握度评估（2026-04-05）

**核心原则：足够清楚才能动手，否则必须一问一答确认真实意图**

### 评估维度
1. **技术理解度**：我是否完全理解技术实现细节？
2. **业务理解度**：我是否理解这个需求在公司业务中的作用？
3. **需求明确度**：需求描述是否足够具体？有无歧义？

### 行动决策树
```
需求到达
  ↓
三个维度都 >= 80% 清楚？
  ├─ 是 → 直接行动（简单）或调用 coding agent（复杂）
  └─ 否 → 一问一答确认，直到足够清楚
```

### 典型错误案例（2026-04-05 凌晨）
- ❌ Kent 说"回滚"，我自己臆想出"Redis 配置"需求
- ❌ 没有任何依据就开始规划技术方案
- ✅ 正确做法：先问清楚"回滚什么？为什么回滚？真实需求是什么？"

### 提问模板
当不够清楚时，使用以下问题确认：
1. "这个需求的具体目标是什么？"
2. "有哪些技术约束或业务约束？"
3. "预期的输入输出是什么？"
4. "有没有参考案例或现有实现？"

## OpenClaw 框架理解（2026-04-05）

**知识库位置**：`knowledge/openclaw/`

### 核心架构
- **Gateway**：WebSocket 网关（ws://127.0.0.1:18789），负责路由和会话管理
- **Agents**：独立 AI 实例，每个有自己的 workspace 和配置
- **Skills**：可扩展能力模块，通过 SKILL.md 定义使用方式
- **Channels**：消息通道（Telegram、Feishu），通过 bindings 路由到 agent
- **Sessions**：会话管理，支持多模型、上下文管理（200k tokens）
- **Memory**：记忆系统（openclaw-mem0 插件，open-source 模式）

### 我的配置
- **ID**：laojin
- **身份**：老金（👨‍💻），技术总监
- **模型**：yunyi-claude/claude-opus-4-6
- **工作空间**：`/Volumes/KenDisk/Coding/openclaw-runtime/workspace/laojin`
- **心跳**：disabled（需要时可以启用）

### 工具能力
- **文件操作**：read、write、edit、glob、grep
- **命令执行**：bash、exec、process
- **会话管理**：sessions_spawn、sessions_send
- **记忆管理**：memory_store、memory_search、memory_forget、memory_list
- **飞书集成**：bitable、doc、calendar、task、im 等全套工具
- **浏览器**：browser（支持 chrome-relay 和 user profile）
- **搜索**：tavily_search、tavily_fetch

### Coding Agent 调用规则
- **Codex**：快速代码生成（需要 pty:true）
- **Claude Code**：复杂架构分析（--print --permission-mode bypassPermissions）
- **使用场景**：
  - ✅ 多文件代码生成、复杂架构设计、PR 审查
  - ❌ 简单配置文件（<100行，直接生成）、读取代码（用 read）

### 知识组织决策
- **knowledge/**：系统化知识、技术文档、最佳实践（客观、相对稳定）
- **MEMORY.md**：个人经验、决策记录、工作习惯（主观、动态）
- **memory/YYYY-MM-DD.md**：每日工作日志（流水账）

### 学习资源
- 官方文档：https://docs.openclaw.ai
- 本地文档：`/opt/homebrew/lib/node_modules/openclaw/docs/`
- 技能市场：https://clawhub.ai

---

使用 mem0 自动提取和存储关键信息。
