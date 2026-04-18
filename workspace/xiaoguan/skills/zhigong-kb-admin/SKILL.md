---
name: zhigong-kb-admin
description: 管理【智工空间】飞书知识库协作页面的技能。用户提到智工空间、飞书知识库、目录治理、Handoff、ADR、归档时触发。默认先 dry-run 输出待变更清单，只有用户明确说“执行/apply”才写入。使用官方 `feishu_fetch_doc` / `feishu_search_doc_wiki` / `feishu_wiki_space_node` / `feishu_update_doc`；不具备创建/移动/重命名能力时必须给人工步骤，不假执行。
---

# Zhigong KB Admin (xiaoguan)

## 1) 工具边界

- 仅可使用：`feishu_fetch_doc`、`feishu_search_doc_wiki`、`feishu_wiki_space_node`、`feishu_update_doc`。
- 禁止声称已执行以下动作：创建节点、移动、重命名、删除。

## 2) 默认流程

1. 先 `dry-run`：盘点目标页面与待追加内容。
2. 输出待变更清单与风险（重名、权限不足、目标页不存在）。
3. 明确提示“回复执行apply后写入”。

## 3) apply 触发词

仅当用户明确确认才写入，例如：

- `执行apply`
- `确认执行`
- `开始执行`

## 4) 回执格式

- 模式：dry-run/apply
- 目标页面：标题 + node_token（可得则填）
- 写入结果：成功/部分成功/失败
- 追溯字段：obj_token（可得则填）
- 未完成项：人工步骤（如需创建新页面）

## 5) 角色侧重点

- 小冠优先维护：客户运营、交付跟进、SOP 执行反馈页面。
- 对“总纲/制度页”请求，仅给建议，不直接改写。
