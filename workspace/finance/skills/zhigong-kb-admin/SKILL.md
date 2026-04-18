---
name: zhigong-kb-admin
description: 管理【智工空间】飞书知识库财务相关页面的技能。用户提到智工空间、飞书知识库、目录治理、Handoff、ADR、归档时触发。默认先 dry-run 输出待变更清单，只有用户明确说“执行/apply”才写入。使用官方 `feishu_fetch_doc` / `feishu_search_doc_wiki` / `feishu_wiki_space_node` / `feishu_update_doc`；创建/移动/重命名需求必须输出人工步骤，不假执行。
---

# Zhigong KB Admin (finance)

## 1) 工具边界

- 仅可使用：`feishu_fetch_doc`、`feishu_search_doc_wiki`、`feishu_wiki_space_node`、`feishu_update_doc`。
- 不具备：创建节点、移动、重命名、删除。

## 2) 默认执行策略

1. 先 dry-run，列出待写入页面与字段。
2. 提示风险（页面不存在、重名、权限不足）。
3. 等待明确确认词后 apply。

## 3) apply 触发词

- `执行apply`
- `确认执行`
- `开始执行`

## 4) 财务治理重点

- 优先维护：预算、现金流、风险提示、财务复盘页面。
- 对口径不完整的写入，先标注“待确认”再追加。

## 5) 固定回执

- 模式：dry-run/apply
- 页面：标题 + node_token（可得则填）
- 结果：成功/部分成功/失败
- 追溯：obj_token（可得则填）
- 未完成项：需要人工处理的创建/重命名动作
