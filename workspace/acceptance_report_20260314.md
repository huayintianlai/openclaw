# 记忆系统与文件知识库验收报告（2026-03-14）

## 参考规范

- OpenClaw Agent Send: https://docs.openclaw.ai/tools/agent-send
- OpenClaw Session Management: https://docs.openclaw.ai/concepts/session
- OpenClaw Feishu Channel: https://docs.openclaw.ai/channels/feishu
- OpenClaw Telegram Channel: https://docs.openclaw.ai/channels/telegram

核对要点：

- `openclaw agent` 默认经 Gateway 运行，`--local` 为嵌入式本地运行。
- `--agent <id>` 使用该 agent 的 `main` session。
- 默认 direct DM 会折叠到 `agent:<agentId>:main`。
- session store 是 `agents/<agentId>/sessions/sessions.json`，其中包含 `deliveryContext` / `origin`，这正是 `knowledge_return_file` 回传附件的路由依据。
- Feishu 官方文档页给出的默认媒体限制是 `mediaMaxMb=30`。
- Telegram 官方文档页给出的默认媒体限制是 `mediaMaxMb=100`。

## 验收结果总表

| Agent | 运行方式 | 记忆工具 | 知识入库/检索/取回 | 附件真实回传 | 结论 |
|---|---|---|---|---|---|
| xiaodong | Gateway + 真实 Feishu 主会话 | 通过 | 通过（PDF） | 通过 | 通过 |
| xiaoguan | Gateway + 真实 Feishu 主会话 | 通过 | 通过（PPTX） | 通过 | 通过 |
| finance | Gateway + 真实 Feishu 主会话 | 通过 | 通过（图片） | 通过 | 通过 |
| echo | Gateway + 真实 Feishu 主会话 | 通过 | 通过（PDF） | 通过 | 通过 |
| xiaodong_crossborder_scout | Local 实际 Agent 回合 | 通过 | 通过（PPTX） | 无真实会话目标，未验证 | 通过（功能链路） |
| xiaodong_ai_scout | Local 实际 Agent 回合 | 通过 | 通过（图片） | 无真实会话目标，未验证 | 通过（功能链路） |
| aduan_growth | Local 实际 Agent 回合 | 通过 | 通过（PDF） | 无真实会话目标，未验证 | 通过（功能链路） |
| aduan | Local 实际 Agent 回合 | 仅 `memory_search/get` 可见 | knowledge 工具实际不可见 | 不适用 | 失败（运行态工具缺失） |
| aduan_learner | Local 实际 Agent 回合 | 仅 `memory_search/get` 可见 | knowledge 工具实际不可见 | 不适用 | 失败（运行态工具缺失） |
| aduan_reflector | Local 实际 Agent 回合 | 仅 `memory_search/get` 可见 | knowledge 工具实际不可见 | 不适用 | 失败（运行态工具缺失） |

## 关键实测

### 1. 小东（重点验收）

- 真实会话目标：`feishu -> user:ou_87bb675cf1a555992cf71df25f860c63`
- memory:
  - `memory_store` 成功
  - `memory_search` 命中数 `3`
- knowledge:
  - 入库文件：`workspace/xiaodong/qa-assets/kb-smoke.pdf`
  - `file_id`: `9763db43-8dfa-446f-893a-7574a90b709f`
  - `knowledge_get_file` 成功
  - `knowledge_return_file` 成功
- 外部核验：
  - `/files/9763db43-8dfa-446f-893a-7574a90b709f/meta` 返回正常
  - 下载后的 SHA256 与原始 PDF 一致：
    - `c927f124328062ebd59c08255c988d903b739dec7a641254d596676d20edba30`
- 日志已确认真实 Feishu 发文件动作：
  - `sendFileLark: target=user:ou_87bb675cf1a555992cf71df25f860c63`

### 2. 小冠

- 真实会话目标：`feishu -> user:ou_dc95eabe8982323faf7e9f3701e61e22`
- memory:
  - `memory_store` 成功
  - `memory_search` 命中数 `2`
- knowledge:
  - 入库文件：`workspace/xiaoguan/qa-assets/kb-smoke.pptx`
  - `file_id`: `9c7b2e36-c8be-4efc-b1d3-4b472ec6599e`
  - `knowledge_get_file` 成功
  - `knowledge_return_file` 成功
- 外部核验：
  - `/files/9c7b2e36-c8be-4efc-b1d3-4b472ec6599e/meta` 返回正常
  - 下载后的 SHA256 与原始 PPTX 一致：
    - `a862b17599b3900cad5c3113bd2622f26f7edcba915d080f467f56ef9a42f59e`
- 日志已确认真实 Feishu 发文件动作：
  - `sendFileLark: target=user:ou_dc95eabe8982323faf7e9f3701e61e22`

### 3. 财务

- 真实会话目标：`feishu -> user:ou_7e15e0ba20128ad3914123824f2fde3d`
- memory:
  - `memory_store` 成功
  - `memory_search` 命中数 `0`
- knowledge:
  - 入库文件：`workspace/finance/qa-assets/kb-smoke-image.png`
  - `file_id`: `99c7b562-5661-488a-be2f-66449989f643`
  - `knowledge_get_file` 成功
  - `knowledge_return_file` 成功
- 外部核验：
  - `/files/99c7b562-5661-488a-be2f-66449989f643/meta` 返回正常
  - 下载后的 SHA256 与原始图片一致：
    - `a745c50e0ecc40e1b0ef9c0e841ed7c968078c218a5ef15818ba661c7310a04d`
- 日志已确认真实 Feishu 发文件动作：
  - `sendFileLark: target=user:ou_7e15e0ba20128ad3914123824f2fde3d`

### 4. 艾可

- 真实会话目标：`feishu -> user:ou_deb896dc0dd4234e4c7b7339f69565e8`
- memory:
  - `memory_store` 成功
  - `memory_search` 命中数 `1`
- knowledge:
  - 入库文件：`workspace/echo/qa-assets/kb-smoke.pdf`
  - `file_id`: `a471c22a-14ec-4c07-b70f-cd868ba1f010`
  - `knowledge_get_file` 成功
  - `knowledge_return_file` 成功
- 外部核验：
  - `/files/a471c22a-14ec-4c07-b70f-cd868ba1f010/meta` 返回正常
  - 下载后的 SHA256 与原始 PDF 一致：
    - `c927f124328062ebd59c08255c988d903b739dec7a641254d596676d20edba30`
- 日志已确认真实 Feishu 发文件动作：
  - `sendFileLark: target=user:ou_deb896dc0dd4234e4c7b7339f69565e8`

### 5. 无真实会话目标的子 Agent

- `xiaodong_crossborder_scout`
  - `file_id`: `70cb2b6f-65a7-456a-b76c-121017a551a0`
  - memory 命中数 `0`
  - `knowledge_get_file` 成功
  - 由于 `sessions.json` 中 `deliveryContext` 为空，未验证真实附件回传

- `xiaodong_ai_scout`
  - `file_id`: `d48b58ca-87bc-4856-b8c3-6341d0652a6a`
  - memory 命中数 `0`
  - `knowledge_get_file` 成功
  - 由于 `sessions.json` 中 `deliveryContext` 为空，未验证真实附件回传

- `aduan_growth`
  - `file_id`: `455912bf-6b1e-4c02-ae88-bd8e189a6193`
  - memory 命中数 `1`
  - `knowledge_get_file` 成功
  - 由于 `sessions.json` 中 `deliveryContext` 为空，未验证真实附件回传

## 缺陷与风险

### P1: 阿段系三个 Agent 运行态工具缺失

受影响：

- `aduan`
- `aduan_learner`
- `aduan_reflector`

现象：

- 配置文件里允许了更多工具，但实际 `systemPromptReport.tools.entries` 只暴露：
  - `memory_search`
  - `memory_get`
- `knowledge_*`、`memory_store`、`memory_list`、`memory_forget` 在运行态不可见

这不是口头判断，是实际 Agent 回合结果。

### P2: 本机 shell 的 `OPENAI_API_KEY` 与项目 `.env` 不一致

现象：

- 当前 shell 环境里 `OPENAI_API_KEY` 前缀是 `sk-MDNGU...`
- 项目 `.env` 里的 `OPENAI_API_KEY` 是另一把 key，并且直接调用 `https://api.openai.com/v1/models` 可通
- 如果 `openclaw agent` 在 Gateway 不可达时 fallback 到 `--local`，会污染 Mem0 测试结果，出现 401

影响：

- 本地 embedded 回合的记忆测试会不稳定
- 验收时必须显式覆盖 `OPENAI_API_KEY`

### P3: 本地 CLI / Gateway 连接稳定性一般

现象：

- 出现过：
  - `gateway not connected`
  - `connect challenge timeout`
  - `gateway closed (1012): service restart`

影响：

- `openclaw agent` 在 Gateway 重启窗口会 fallback 到 embedded
- 如果不显式控制环境变量，会把 embedded 的问题误当成 Gateway 问题

## 结论

- 文件知识库主链路已经可用，并且不是“只能搜不能回”：
  - 图片、PDF、PPTX 三种材料都已通过实际入库
  - `knowledge_get_file` 已通过
  - Feishu 真实附件回传已在 4 个 Agent 上验证通过
- 记忆系统在大多数 Agent 上可用，但稳定性还没到“最优”：
  - 小东、小冠、财务、艾可、子 Agent、阿段增长 的记忆工具可跑
  - 阿段主线 / learner / reflector 的运行态工具暴露明显异常，必须继续修
- 如果把“高可用”定义成“所有配置中的 Agent 都能按声明拿到同样的 memory/knowledge 工具”，当前结论是：
  - **文件知识库：基本通过**
  - **记忆系统：未完全通过**
