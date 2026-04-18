# OpenClaw 2026-03-24 TODO

## 背景

本轮排障与验收基于本地运行目录 `~/.openclaw`、官方 `OpenClaw 2026.3.23-2`、官方 Feishu 插件与当前项目自定义扩展完成。

目标：

- 恢复并稳定官方最新版 Feishu 通道
- 校准 Agent 的官方工具表面
- 修复知识库附件回传链路
- 给出后续待办清单，作为继续迭代的唯一 TODO 基线

## 本轮优先修复

- [x] 将 Agent 的 Feishu 工具 allowlist 从旧 OAPI/自定义工具名迁移到官方 2026.3.22 的真实工具表面
- [x] 修复 `knowledge-search-plugin` 的 `knowledge_return_file` 对旧 `openclaw-lark` 路径的硬依赖
- [x] 打开官方 `feishu_wiki` 能力，并按官方知识库读写路径校准相关配置
- [x] 完成修复后的回归测试和验收

## 已确认问题

### P0

- [x] `knowledge_return_file` 仍然引用旧路径 `../openclaw-lark/src/messaging/outbound/media.js`，导致最新版官方 Feishu 插件环境下附件回传失败
- [x] 多个 Agent 的 allowlist 仍然使用旧工具名，如 `feishu_fetch_doc`、`feishu_bitable_app_table_field`、`feishu_task_tasklist`
- [x] 官方 2026.3.22 Feishu 插件当前实际暴露的是聚合/新版工具表面，与旧自定义 Lark 插件不兼容

### P1

- [x] `xiaoguan` 的任务管理能力已恢复到官方 `feishu_task_*` 原生工作流；当前通过官方 `@larksuite/openclaw-lark` 暴露
- [x] `memory_store` 在当前直连 Agent 会话里未暴露，需确认是官方 mem0 设计如此，还是现有工具策略屏蔽了写入
- [x] `sessions_history` 的典型调用方式需要补一层参数约束，避免像 `aduan_reflector` 这样把 `sessionKey` 错传成 `aduan`

### P2

- [x] `.txt` 文件目前无法被 `knowledge_ingest_file` 接受，返回 `Unsupported file type`
- [x] `xiaoguan` 相关 Agent/Workspace 活跃提示词已从“文档任务板替代”清理并回迁到官方 native task 工作流

## 后续待办

### Agent 与 Prompt

- [x] 全部 10 个 Agent 的 Feishu allowlist 已统一迁移到官方 `openclaw-lark` 真实工具名
- [x] 当前活跃 Agent / workspace 提示词中，旧聚合工具名残留已清零
- [x] 为 `xiaoguan` 制定“官方插件无 task 工具时”的降级行为，不再让模型反复尝试不存在的工具
- [x] 在官方 `@larksuite/openclaw-lark` 可用后，将 `xiaoguan` 回迁到真正的 `feishu_task_*` 原生工作流
- [x] 为 `aduan_reflector` 和类似 Agent 补充 `sessions_history` 的正确 session 选择规则

### 记忆与知识库

- [ ] 明确 mem0 在本项目中的“自动捕获 vs 显式写入”策略，并补一份操作文档
- [ ] 为知识库附件链路补充文本、图片、PDF、回传四类自动化回归用例
- [x] 评估是否要给文本类附件补一层转 PDF/Markdown 的官方兼容入库流程

### 测试与验收

- [ ] 建立一份可重复执行的 10 Agent 验收脚本
- [ ] 增加一份“官方插件能力矩阵”文档，区分当前官方已支持能力与历史自定义能力
- [ ] 对 Feishu 私聊、群聊、附件回传、知识库读写分别建立验收 checklist

## 本轮回归结果摘要

- [x] 10 个 Agent 基础回复回归全部通过
- [x] `xiaodong / finance / xiaodong_ai_scout` 已能真实调用官方 `feishu_wiki`
- [x] `xiaodong_crossborder_scout` 已能真实调用新版 `feishu_bitable_list_fields`
- [x] `aduan_growth` 的 `knowledge_return_file` 已恢复，Feishu 附件回传成功
- [x] 官方 `@larksuite/openclaw-lark@2026.3.25` 已安装并加载，原生 `feishu_task_*` 已在真实运行时出现
- [x] bundled `stock:feishu` 已禁用，当前运行态仅保留官方 `openclaw-lark`
- [x] `xiaoguan` 已从 `feishu_doc` 任务板替代回迁到官方 `feishu_task_*` 原生任务流
- [x] `xiaoguan` 已在真实 Feishu 私聊会话中完成原生 Task 验收：`list`、`tasks`、`create`、`patch completed`
- [x] 其余 9 个 Agent 已切换到官方 `openclaw-lark` 真实工具表面，并完成基础回复 + 工具暴露回归
- [x] CLI 直跑时，用户态飞书工具会因缺少消息 `ticket` 返回 `need_user_authorization`；真实 Feishu 私聊链路不受此限制
- [x] `aduan_reflector` 已通过 `tools.sessions.visibility=all` + `tools.agentToAgent.allow` 修复跨 Agent 会话读取
- [x] `.txt` 已通过兼容层转换后完成入库、检索和获取
- [x] `mem0` 显式写入与被动自动捕获链路已完成验收

## 当前未完成项

- [ ] 还未补齐“官方插件能力矩阵”与可重复执行的自动化验收脚本
