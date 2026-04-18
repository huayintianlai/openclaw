# 其他 Agent 复制模板（下一阶段）

用于把 `zhigong-kb-admin` 复制到 `xiaoguan/finance/aduan`。

## 1. 复制路径

- 源：`/Users/xiaojiujiu2/.openclaw/workspace/xiaodong/skills/zhigong-kb-admin`
- 目标：`/Users/xiaojiujiu2/.openclaw/workspace/<agent>/skills/zhigong-kb-admin`

## 2. 触发语义调整

- 保留通用触发词：`智工空间`、`飞书知识库`、`目录治理`、`Handoff`、`ADR`、`归档`。
- 在 `description` 增加该 Agent 职责关键字（如财务、运营、决策）。

## 3. 工具边界映射

复制后必须确认该 Agent 的 `tools.allow` 至少具备：

- `feishu_wiki_list_<agent_scope>`
- `feishu_doc_append_text_<agent_scope>`

仅结构管理员（当前为老金）才保留：

- `feishu_wiki_create_node_<agent_scope>`

## 4. 统一执行策略

- 默认 dry-run。
- 仅收到明确确认词再 apply。
- 所有回执返回可追溯 token。

## 5. 禁止项

- 不在 Skill 文件中硬编码 app_id/app_secret/token。
- 不越过角色边界改写“总纲/制度页”。
