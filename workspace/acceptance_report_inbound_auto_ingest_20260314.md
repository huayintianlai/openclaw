# Feishu 入站自动入库验收报告（2026-03-14）

## 范围

- 目标：修复“小东收到用户图片后，后续不能直接从知识库召回原图”的根因。
- 本次只覆盖：
  - Feishu 私聊入站媒体自动入库
  - 知识库检索命中
  - `knowledge_return_file` 真实回传
- 不覆盖：
  - 群聊自动入库
  - 非 Feishu 渠道自动入库
  - 首次收到附件当回合内向用户显式播报“已入库”

## 参考文档

- OpenClaw Feishu channel: https://docs.openclaw.ai/channels/feishu
- OpenClaw Session Management: https://docs.openclaw.ai/concepts/session
- OpenClaw CLI agent: https://docs.openclaw.ai/cli/agent

核对点：

- Feishu 会话路由和 session 绑定由 Gateway 维护，可作为附件回传目标来源。
- Agent CLI 经 Gateway 运行时，会复用该 session 的 `deliveryContext`。
- 现有知识库工具链已经支持 `knowledge_search` / `knowledge_return_file`，问题在于入站媒体未自动入库。

## 本次改动

- 在 `extensions/openclaw-lark/src/messaging/inbound/knowledge-auto-ingest.js` 新增入站自动入库 helper。
- 在 `extensions/openclaw-lark/src/messaging/inbound/dispatch.js` 将自动入库挂到 Feishu 入站分发阶段。
- 自动入库策略：
  - 仅 Feishu `p2p`
  - 仅支持图片 / PDF / PPT / PPTX
  - 后台并发执行，不阻塞当前回复
  - 默认入库到 `area=feishu-inbound`
  - `owner_type=agent`
  - `owner_id=<route.agentId>`
- 在 `workspace/xiaodong/AGENTS.md` 增加规则：
  - “刚才那张图 / 之前发的材料”优先查 `area=feishu-inbound`

## 真实验收

### 1. 自动入库

- 样本来源：真实 Feishu 历史图片资源
- 原始消息：
  - `message_id = om_x100b540cb8403904b2eb13a8db7a282`
  - `file_key = img_v3_02vo_fc1b5e2d-d60d-4672-b065-044ab4102a7g`
- 真实下载文件：
  - `/tmp/openclaw/im-resource-1773454785929-fc9380f3-f431-4720-a5fc-675069bcb9b0.jpg`
- 自动入库结果：
  - `file_id = 8b151239-bef9-4149-8d7d-e4cd6c90b27c`
  - `area = feishu-inbound`
  - `owner_id = xiaodong`

### 2. 元数据校验

- `/files/8b151239-bef9-4149-8d7d-e4cd6c90b27c/meta` 返回成功
- 服务端 metadata 已包含：
  - `tags = ["source:feishu", "ingest:auto", "sender:ou_87bb675cf1a555992cf71df25f860c63", "message:om_x100b540cb8403904b2eb13a8db7a282", "resource:image"]`
  - `channel_file_capable = true`
  - `storage_path` 指向原文件持久化路径

### 3. 检索命中

- 直接 API 检索：
  - 查询词：`父亲 年轻 纪念 照片`
  - 过滤：`area=feishu-inbound`, `owner_id=xiaodong`
  - 命中：1 条
  - 命中 `file_id = 8b151239-bef9-4149-8d7d-e4cd6c90b27c`

### 4. 小东真实回传

- 实际 Agent 指令：
  - “请只从 `area=feishu-inbound` 的知识库里找我之前那张家庭合影照片，然后把原图直接发回当前飞书会话。”
- 实际结果：
  - `knowledge_search` 命中 `area=feishu-inbound`
  - `knowledge_return_file(fileId=8b151239-bef9-4149-8d7d-e4cd6c90b27c)` 成功
  - Gateway 日志确认：
    - `sendFileLark: target=user:ou_87bb675cf1a555992cf71df25f860c63`

## 结论

- 根因已修复：Feishu 私聊入站附件不再只停留在本地下载路径，而会自动进入知识库。
- 小东已经可以从新入库的 `feishu-inbound` 材料里检索并真实回传原图。
- “记住了描述但回不了原图”的问题，在 Feishu 私聊这条链路上已闭环。

## 剩余风险

- 当前验收样本使用的是“真实 Feishu 图片资源的已下载文件”做自动入库调用；这验证了自动入库逻辑本身和后续 Agent 召回链路，但没有用一条全新的实时入站消息做 webhook 级回放。
- 某些历史图片资源再次调用 `feishu_im_user_fetch_resource` 时会出现 `need_user_authorization`，说明 Feishu 用户授权链路仍可能波动；这不影响“新消息已自动入库后”的后续召回，但会影响“历史补捞”兜底链路。
