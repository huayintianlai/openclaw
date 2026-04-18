# 工作流触发问题修复总结

## 问题描述

当用户在飞书中对阿峰说"编辑公证文件"时，阿峰没有自动启动工作流，而是回复：
> "好的，我来帮您处理公证文件。请问您需要：编辑现有的公证文件？还是准备新的公证文件？..."

## 根本原因

OpenClaw 的工作流系统不会自动识别和触发工作流。Agent 需要在其 AGENT.md 配置文件中明确定义触发规则和执行流程。

## 解决方案

### 1. 调整工作流文件结构

将工作流文件从 flows 根目录移动到子目录，匹配 OpenClaw 的标准结构：

**之前**：
```
/flows/edit-certificate.json
/flows/edit-certificate-trigger.json
```

**之后**：
```
/flows/edit-certificate/
  ├── flow.json
  ├── trigger.json
  └── FLOW.md
```

### 2. 更新 Agent 配置

在 `/agents/afeng/agent/AGENT.md` 中添加了明确的工作流触发规则：

```markdown
## 工作流触发规则（CRITICAL - 必须执行）

### 编辑公证文件工作流

**触发条件**：当用户消息包含以下任一关键词时，必须立即启动工作流
- "编辑公证文件"
- "修改资本存款证明"
- "生成公证文件"
- "公证文件"
- "资本存款"

**执行流程**（必须严格按顺序执行）：

1. 第一步：收集公司名称
2. 第二步：收集公司地址
3. 第三步：收集资本存款日期
4. 第四步：收集落款日期
5. 第五步：确认信息
6. 第六步：执行工作流
7. 第七步：返回结果
```

### 3. 创建工作流文档

创建了 `/flows/edit-certificate/FLOW.md`，详细说明：
- 业务背景
- 触发关键词
- 工作流步骤
- 技术特点
- 错误处理
- 使用示例

## 关键改进

### 明确的触发规则
- 在 AGENT.md 中明确列出触发关键词
- 标记为 CRITICAL 优先级
- 告诉 Agent 必须立即启动工作流

### 详细的执行流程
- 逐步收集信息（不要一次性询问所有信息）
- 每个步骤都有明确的提示词
- 包含验证规则和默认值处理

### 明确的禁止行为
- 不要问"需要编辑现有文件还是准备新文件"
- 不要跳过任何步骤
- 不要一次性询问所有信息

## 测试步骤

重启 OpenClaw 服务后，在飞书中测试：

### 测试 1：基本触发
```
用户：编辑公证文件
预期：阿峰直接询问"📌 请输入公司名称（例如：FinalTest SARL）"
```

### 测试 2：完整流程
```
用户：编辑公证文件
阿峰：📌 请输入公司名称（例如：FinalTest SARL）
用户：TestCompany SARL
阿峰：📍 请输入公司地址（例如：123 Rue de Paris, 75001 Paris）
用户：123 Rue de Paris, 75001 Paris
阿峰：📅 请输入资本存款日期（YYYY-MM-DD 格式，留空默认为两天后）
用户：[留空]
阿峰：✍️  请输入落款日期（YYYY-MM-DD 格式，留空默认为两天后）
用户：[留空]
阿峰：
📝 确认信息：
   公司名称: TestCompany SARL
   公司地址: 123 Rue de Paris, 75001 Paris
   资本存款日期: 2026-04-19
   落款日期: 2026-04-19

⏳ 正在生成 PDF 文件...

✅ 工作流完成！
📄 PDF 文件: /Users/xiaojiujiu2/Downloads/资本存款_TestCompany_SARL_20260417_123456.pdf
```

### 测试 3：其他触发词
```
用户：生成公证文件
预期：同样启动工作流

用户：修改资本存款证明
预期：同样启动工作流
```

## 重启服务

需要重启 OpenClaw 服务以加载新配置：

```bash
# 查找 OpenClaw 进程
ps aux | grep openclaw-gateway

# 重启服务（具体命令取决于启动方式）
# 如果是通过 systemd/launchd 管理，使用相应的重启命令
# 如果是手动启动，需要先 kill 进程再重新启动
```

## 文件清单

已修改/创建的文件：
- ✅ `/agents/afeng/agent/AGENT.md` - 添加工作流触发规则
- ✅ `/flows/edit-certificate/flow.json` - 工作流配置（移动）
- ✅ `/flows/edit-certificate/trigger.json` - 触发器配置（移动）
- ✅ `/flows/edit-certificate/FLOW.md` - 工作流文档（新建）
- ✅ `/workspace/WORKFLOW_FIX_SUMMARY.md` - 本文档

## 预期结果

重启服务后：
- ✅ 用户说"编辑公证文件"时，阿峰立即启动工作流
- ✅ 阿峰逐步收集信息，不会问"编辑现有还是准备新的"
- ✅ 收集完信息后自动调用 Python 脚本生成 PDF
- ✅ 将生成的 PDF 返回到聊天窗口

## 注意事项

1. **必须重启服务**：配置更改需要重启 OpenClaw 服务才能生效
2. **GPT 模型**：阿峰使用的是 GPT 模型，已在多个层面添加业务上下文说明
3. **工作区路径**：确保 afeng 的 workspace 路径正确配置为 `/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng`
4. **Python 脚本**：确保 certificate_workflow.py 有执行权限
5. **Photoshop**：确保 Photoshop 正在运行且可以接收 ExtendScript 命令

## 如果仍然不工作

如果重启后仍然不工作，可能的原因：

1. **Agent 没有读取 AGENT.md**
   - 检查 openclaw.json 中 afeng 的 agentDir 配置
   - 确认 AGENT.md 文件路径正确

2. **GPT 模型忽略了触发规则**
   - 考虑切换到 Claude 模型（在 openclaw.json 中配置）
   - Claude 对指令的遵循度更高

3. **工作流系统不支持这种触发方式**
   - 可能需要使用 OpenClaw 的官方工作流 API
   - 需要查看 OpenClaw 的工作流文档

## 备选方案

如果上述方案无效，可以考虑：

1. **使用 Skill 系统**：将工作流封装为 Skill
2. **使用工具调用**：创建自定义 MCP 工具
3. **直接在 AGENT.md 中内联脚本**：不依赖外部工作流系统
