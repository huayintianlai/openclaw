---
name: zhigong-kb-admin
description: 管理【智工空间】飞书知识库的治理技能。用户提到智工空间、飞书知识库、目录治理、Handoff、ADR、归档，或直接发送 feishu.cn/wiki 链接时触发。默认先做 dry-run 盘点并输出待变更清单，只有用户明确说“执行/apply”才做写入。使用官方 `feishu_fetch_doc` / `feishu_search_doc_wiki` / `feishu_wiki_space_node` / `feishu_create_doc` / `feishu_update_doc`；遇到超出工具边界的需求时，输出人工操作步骤，不假执行。
---

# Zhigong KB Admin

按以下流程执行，不得跳步。

## 0) 工具与边界

- 只可使用：`feishu_fetch_doc`、`feishu_search_doc_wiki`、`feishu_wiki_space_node`、`feishu_create_doc`、`feishu_update_doc`。
- 禁止伪造执行结果，禁止把“计划动作”写成“已完成”。
- 对“移动节点/重命名节点/删除节点”类动作，必须输出人工步骤或管理员流程。
- 对知识库任务禁止要求用户安装 Browser Relay、Gateway token、浏览器插件；这些不是本技能前置条件。
- 不得优先走浏览器抓取；必须先走飞书 wiki API 工具。

## 0.1) Wiki 链接直查规则

- 若用户消息含 `feishu.cn/wiki/` 链接，先抽取 `<node_token>`。
- 优先返回该节点可见信息与子节点列表（通过 `feishu_fetch_doc`、`feishu_search_doc_wiki` 或 `feishu_wiki_space_node(action=list)` 获取）。
- 不得要求用户手抄一级目录，不得把“无浏览器”当成知识库读取失败原因。

## 1) 默认模式：dry-run

当用户发起治理需求时，先做盘点，不写入：

1. 用 `feishu_search_doc_wiki` 或 `feishu_wiki_space_node(action=list)` 读取目标节点结构。
2. 输出“将要变更的节点清单”：
   - 目标父节点
   - 新建文档/目录标题
   - 将追加内容的目标文档（若有）
   - 风险提示（重名、层级不明确、权限不足）
3. 明确提示：`当前为 dry-run，未写入。回复“执行apply”后才会写入。`

## 2) 执行模式：apply（需明确确认）

仅当用户出现明确确认词时执行写入，例如：

- `执行apply`
- `确认执行`
- `开始执行`

执行规则：

1. 创建节点时使用 `feishu_create_doc` 或 `feishu_wiki_space_node(action=create)`。
2. 模板补齐时使用 `feishu_update_doc`。
3. 每次写入后立即记录可追溯信息：`title`、`node_token`、`obj_token`（可获取时）。

## 3) 场景化治理模板

### 盘点重复目录文档

- dry-run 输出重复页候选清单与所在父节点。
- 不做移动/重命名；仅给人工操作建议。

### 补齐协作中心模板

- 目标页面：`Handoff_跨Agent交接单`、`ADR_决策记录`、`会议纪要_模板`。
- 若缺失：先 dry-run 报告，确认后新建。
- 若存在：仅在确认后追加模板字段，不覆盖历史内容。

### 新增治理页面

- 先检查重名。
- 默认在用户指定父节点下创建 `docx`。
- 未指定父节点时先返回候选父节点列表，不盲建。

## 4) 固定回执格式

### dry-run 回执

- `模式`: dry-run  
- `目标`: <需求摘要>  
- `待变更清单`: <逐条>  
- `风险`: <逐条>  
- `下一步`: 回复“执行apply”后写入

### apply 回执

- `模式`: apply  
- `执行结果`: 成功/部分成功/失败  
- `变更明细`: 标题 + node_token + obj_token（可得则填）  
- `未完成项`: 权限/边界导致的剩余事项  
- `建议`: 下一步人工处理项（如移动/重命名）
