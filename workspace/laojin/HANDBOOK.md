# 老金工作手册

## 快速参考

### Codex vs Claude Code 选择指南

**快速代码生成 → 用 Codex (yunyi-codex/gpt-5.4)**
- 代码片段、配置文件
- API 调用示例
- 简单重构

**深度分析 → 用 Claude Code (kimi/kimi-code)**
- 架构设计
- 代码审查
- 技术债务分析
- 复杂重构

### 项目档案模板

每个新项目在 `projects/{project-name}/` 下创建：
- `architecture.md` - 架构设计
- `decisions.md` - ADR 技术决策记录
- `tech-debt.md` - 技术债务清单
- `changelog.md` - 技术演进日志

### 常用命令

```bash
# 查看所有 Agent
openclaw agents list

# 重启网关
openclaw gateway restart

# 查看日志
openclaw logs --follow
```

---

持续更新此手册。
