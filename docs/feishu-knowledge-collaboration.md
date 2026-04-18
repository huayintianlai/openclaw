# 飞书知识库协作方案（小东主编）

## 1. 治理原则

- 小东负责知识库结构治理、目录发布、制度页维护。
- 小冠、finance、阿段按职责直写业务页；制度类页面仅小东维护。
- 第一阶段自动化仅覆盖 `Docx + 多维表格`，不纳入幻灯片/问卷/思维笔记。
- Docx 采用“追加段落”写入模型，页面模板必须可追加，不依赖复杂块级编辑。

## 2. 目录架构（父文档即分组）

- `00_董事会首页`：北极星、现金流、三大风险、本周决策
- `01_战略与目标`
- `02_客户与销售`
- `03_产品与研发`
- `04_运营与交付`
- `05_财务与法务`
- `06_协作中心`：Handoff、ADR、会议纪要
- `07_Agent工作台`：xiaodong / xiaoguan / finance / aduan
- `99_归档`

命名规范：`NN_模块名`，文档状态统一 `Draft / Review / Published`。

## 3. 多维表格设计（结构化索引）

### 文档台账

- `doc_name`
- `owner`
- `status`
- `last_update`
- `node_token`
- `obj_token`
- `module`

### 交接队列（Handoff）

- `requester`
- `receiver`
- `topic`
- `priority`（P0/P1/P2）
- `deadline`
- `status`（Draft/Doing/Done）
- `related_doc`

### 决策索引（ADR）

- `adr_id`
- `topic`
- `decision`
- `owner`
- `review_date`
- `risk_level`
- `related_doc`

## 4. 角色分工

- `xiaodong`：结构治理、发布节奏、跨部门协调。
- `xiaoguan`：客户运营、交付跟进、SOP执行反馈。
- `finance`：预算、现金流、财务风险与复盘。
- `aduan`：决策结论、红线、止损线、owner/deadline 定版。

## 5. 协作流程

- 常规更新：责任 Agent 直写业务页 -> 小东日内巡检。
- 重大事项：必须先形成 ADR，再进入执行。
- 跨部门协作：先建 Handoff，再执行，禁止口头流转。

## 6. 页面模板（Docx）

每页头部固定字段：

- `Owner`
- `Status`
- `Last Update`
- `Related Task`
- `Source`
- `Next Action`

## 7. 目录去重约定（2026-03）

- 不再为每个一级模块自动创建 `00_目录文档`，避免层级重复。
- 总目录维护在主目录文档（如 `首页` / `00_董事会首页`）内统一管理。
- `scripts/bootstrap_feishu_wiki_templates.sh` 仅负责 `06_协作中心` 模板页初始化。
