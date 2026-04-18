# OpenClaw 架构概览

## 核心组件

### 1. Gateway（网关）
- **作用**：WebSocket 服务器，负责路由、会话管理、消息分发
- **地址**：ws://127.0.0.1:18789（本地）
- **服务管理**：通过 LaunchAgent/systemd 管理
- **命令**：
  - `openclaw gateway run` - 前台运行
  - `openclaw gateway start/stop/restart` - 服务管理
  - `openclaw gateway status` - 查看状态

### 2. Agents（智能体）
- **定义**：独立的 AI 助手实例，每个有自己的身份、配置和工作空间
- **配置位置**：`openclaw.json` 中的 `agents.list`
- **核心属性**：
  - `id`: 唯一标识符
  - `name`: 显示名称
  - `identity`: 身份信息（emoji、头像等）
  - `workspace`: 工作目录
  - `agentDir`: Agent 配置目录（存放 auth-profiles.json 等）
  - `model`: 使用的 AI 模型
  - `tools`: 允许使用的工具列表
  - `heartbeat`: 心跳配置（定期检查）
  - `sandbox`: 沙箱模式

### 3. Channels（通道）
- **作用**：连接外部消息平台（Telegram、Feishu、Discord 等）
- **路由机制**：通过 `agents.bindings` 将 channel + accountId 映射到具体 agent
- **示例**：
  ```
  laojin <- feishu accountId=laojin
  xiaodong <- telegram accountId=xiaodong
  ```

### 4. Skills（技能）
- **定义**：可扩展的能力模块，类似插件系统
- **位置**：
  - 内置：`/opt/homebrew/lib/node_modules/openclaw/skills/`
  - 扩展：`openclaw-runtime/extensions/*/skills/`
  - 工作空间：`workspace/*/skills/`（通过 `openclaw-workspace` 加载）
- **结构**：每个 skill 包含 `SKILL.md`（使用指南）和相关脚本/工具
- **分类**：
  - 飞书集成（bitable、calendar、doc、task、im-read）
  - 记忆管理（memory-triage、memory-dream）
  - 开发工具（coding-agent、github、clawhub）
  - 系统工具（apple-notes、1password、peekaboo）

### 5. Sessions（会话）
- **作用**：管理对话上下文、历史记录、token 使用
- **类型**：
  - `direct`: 直接对话
  - `cron`: 定时任务会话
- **查看**：`openclaw sessions list`
- **特性**：
  - 支持多模型切换
  - 上下文管理（200k tokens）
  - 自动压缩和清理

### 6. Memory（记忆系统）
- **插件**：`openclaw-mem0`
- **模式**：
  - `platform`: 云端存储
  - `open-source`: 本地存储
- **功能**：
  - `autoCapture`: 自动捕获对话
  - `autoRecall`: 自动召回记忆
  - `skills`: 记忆技能（triage/recall/dream）

## 配置文件

### openclaw.json
- **位置**：`/Volumes/KenDisk/Coding/openclaw-runtime/openclaw.json`
- **核心配置**：
  - `agents.defaults`: 默认配置（模型、工具、沙箱等）
  - `agents.list`: Agent 列表
  - `channels`: 通道配置
  - `gateway`: 网关配置
  - `plugins`: 插件配置

### Agent 工作空间文件
- `AGENTS.md`: Agent 行为规范
- `SOUL.md`: Agent 人格定义
- `USER.md`: 用户信息
- `IDENTITY.md`: Agent 身份
- `TOOLS.md`: 工具配置笔记
- `MEMORY.md`: 长期记忆索引
- `HEARTBEAT.md`: 心跳任务清单
- `memory/YYYY-MM-DD.md`: 每日工作日志

## 工作流程

1. **消息接收**：Channel 接收外部消息
2. **路由**：Gateway 根据 bindings 路由到对应 Agent
3. **会话管理**：Session 加载上下文和历史
4. **技能加载**：根据 prompt 中的 `<available_skills>` 加载相关 skill
5. **工具调用**：Agent 通过 tools 执行操作
6. **记忆存储**：重要信息通过 memory 系统持久化
7. **响应返回**：通过 Channel 返回给用户

## 版本信息
- **当前版本**：2026.4.2 (d74a122)
- **Node.js**：v25.2.1
- **平台**：macOS 15.7.4 (arm64)
