# OpenClaw Skills 开发规范

## Skill 结构

### 标准目录结构
```
skill-name/
├── SKILL.md           # 必需：技能使用指南
├── README.md          # 可选：对外说明文档
├── scripts/           # 可选：辅助脚本
│   ├── setup.sh
│   └── helper.py
├── references/        # 可选：参考文档
│   ├── api-docs.md
│   └── examples.md
└── config/            # 可选：配置文件模板
    └── template.json
```

### SKILL.md 规范

#### 1. 文件头部（必需）
```markdown
# Skill Name

Brief description of what this skill does.

## When to Use This Skill

- Trigger condition 1
- Trigger condition 2
- Keywords: "keyword1", "keyword2", "keyword3"
```

#### 2. 核心内容
- **工具说明**：列出使用的工具和命令
- **使用流程**：分步骤说明如何使用
- **示例**：提供实际使用案例
- **注意事项**：列出限制和约束
- **故障排查**：常见问题和解决方案

#### 3. 相对路径处理
- Skill 内引用文件时使用相对路径
- Agent 读取时会自动解析为绝对路径
- 示例：`./scripts/setup.sh` → `/path/to/skills/skill-name/scripts/setup.sh`

## Skill 加载机制

### 1. 扫描阶段
OpenClaw 在启动时扫描以下位置：
- 内置 skills：`/opt/homebrew/lib/node_modules/openclaw/skills/`
- 扩展 skills：`openclaw-runtime/extensions/*/skills/`
- 工作空间 skills：`workspace/*/skills/`（需要 `openclaw-workspace` 插件）

### 2. 注册阶段
每个 skill 的 `<description>` 会被注入到 agent prompt 的 `<available_skills>` 块中：
```xml
<available_skills>
  <skill>
    <name>skill-name</name>
    <description>Brief description...</description>
    <location>/path/to/skill/SKILL.md</location>
  </skill>
</available_skills>
```

### 3. 触发阶段
- Agent 根据用户消息判断是否需要某个 skill
- 如果匹配，使用 `read` 工具加载 `SKILL.md`
- 按照 SKILL.md 中的指令执行

### 4. 执行阶段
- Skill 可以调用任何 agent 允许的工具
- Skill 可以引用自己目录下的脚本和配置
- Skill 可以调用外部 CLI 工具

## Skill 开发最佳实践

### 1. Description 编写
- **简洁明确**：一句话说清楚 skill 的作用
- **触发条件**：明确列出何时使用此 skill
- **关键词**：列出用户可能提到的关键词
- **中英文**：如果面向中文用户，使用中文 description

示例：
```markdown
<description>
飞书多维表格（Bitable）的创建、查询、编辑和管理工具。

**当以下情况时使用此 Skill**：
(1) 需要创建或管理飞书多维表格 App
(2) 需要在多维表格中新增、查询、修改、删除记录
(3) 用户提到"多维表格"、"bitable"、"数据表"、"记录"、"字段"
</description>
```

### 2. 工具调用模式

#### 直接调用工具
```markdown
## Usage

1. Use the `feishu_bitable_app` tool to list apps
2. Use the `feishu_bitable_app_table_record` tool to query records
```

#### 调用外部 CLI
```markdown
## Usage

1. Run `./scripts/setup.sh` to initialize
2. Run `cli-tool --option value` to execute
```

#### 调用 Coding Agent
```markdown
## Usage

When complex code generation is needed:
1. Use `sessions_spawn` to call Codex or Claude Code
2. Provide clear requirements and context
3. Review and integrate the generated code
```

### 3. 错误处理
- **预检查**：在执行前检查前置条件
- **友好提示**：错误时给出明确的解决方案
- **降级方案**：提供备选方案

示例：
```markdown
## Troubleshooting

### Error: API key not found
**Solution**: Run `openclaw config set feishu.appId YOUR_APP_ID`

### Error: Permission denied
**Solution**: Check if the app has the required scopes in Feishu Admin Console
```

### 4. 配置管理
- **环境变量**：敏感信息使用环境变量
- **配置文件**：结构化配置使用 JSON/YAML
- **用户配置**：在 workspace 的 TOOLS.md 中记录用户特定配置

### 5. 文档组织
- **SKILL.md**：给 Agent 看的执行指南（简洁、可执行）
- **README.md**：给人类看的说明文档（详细、友好）
- **references/**：API 文档、示例代码等参考资料

## Skill 类型

### 1. 工具封装型
封装现有 CLI 工具或 API，提供统一接口。

示例：`apple-notes`、`1password`、`github`

### 2. 流程编排型
组合多个工具，实现复杂业务流程。

示例：`clawflow-inbox-triage`、`gh-issues`

### 3. 知识库型
提供特定领域的知识和最佳实践。

示例：`healthcheck`、`node-connect`、`feishu-troubleshoot`

### 4. 代理型
调用其他 AI agent 完成任务。

示例：`coding-agent`

## Skill 发布

### 1. 本地开发
```bash
# 在 workspace 创建 skill
mkdir -p workspace/laojin/skills/my-skill
cd workspace/laojin/skills/my-skill
touch SKILL.md

# 重启 gateway 加载新 skill
openclaw gateway restart
```

### 2. 发布到 ClawHub
```bash
# 安装 clawhub CLI
npm install -g clawhub

# 发布 skill
clawhub publish ./my-skill

# 其他用户安装
clawhub install my-skill
```

### 3. 版本管理
- 使用语义化版本（semver）
- 在 SKILL.md 中记录版本历史
- 重大变更提供迁移指南

## 示例：创建一个简单的 Skill

### 场景
创建一个查询天气的 skill（假设已有 `weather` CLI 工具）

### 1. 创建目录
```bash
mkdir -p workspace/laojin/skills/weather-check
cd workspace/laojin/skills/weather-check
```

### 2. 编写 SKILL.md
```markdown
# Weather Check

Query current weather and forecast for any location.

## When to Use This Skill

- User asks about weather, temperature, or forecast
- Keywords: "天气", "weather", "温度", "temperature", "forecast"

## Tools Required

- `exec` tool to run `weather` CLI

## Usage

1. Parse the location from user's message
2. Run `weather --location "LOCATION"` to get current weather
3. Run `weather --location "LOCATION" --forecast` for forecast
4. Format the result in a user-friendly way

## Examples

User: "北京今天天气怎么样？"
Action: `weather --location "北京"`

User: "What's the weather in New York this week?"
Action: `weather --location "New York" --forecast`

## Error Handling

- If location is ambiguous, ask user to clarify
- If `weather` CLI is not installed, suggest installation: `brew install weather`
```

### 3. 测试
```bash
# 重启 gateway
openclaw gateway restart

# 在飞书中测试
"北京今天天气怎么样？"
```

## 进阶技巧

### 1. 条件触发
在 description 中使用更精确的条件：
```markdown
**当以下情况时使用此 Skill**：
(1) 用户明确提到"多维表格"或"bitable"
(2) 需要批量操作数据（>10条记录）
(3) 需要复杂筛选或聚合查询
```

### 2. 技能组合
一个 skill 可以调用其他 skills：
```markdown
## Dependencies

This skill requires:
- `feishu-fetch-doc` for reading documents
- `feishu-bitable` for data storage
```

### 3. 动态配置
根据用户配置调整行为：
```markdown
## Configuration

Check `TOOLS.md` for user-specific settings:
- Preferred weather unit (Celsius/Fahrenheit)
- Default location
- Notification preferences
```

### 4. 状态管理
使用 JSON 文件追踪状态：
```markdown
## State Management

Maintain state in `workspace/laojin/state/weather-check.json`:
```json
{
  "lastCheck": "2026-04-05T09:00:00Z",
  "locations": ["北京", "上海"],
  "alerts": []
}
```
```

## 总结

好的 Skill 应该：
- ✅ 有清晰的触发条件
- ✅ 提供可执行的步骤
- ✅ 处理常见错误
- ✅ 文档简洁明了
- ✅ 易于测试和调试
