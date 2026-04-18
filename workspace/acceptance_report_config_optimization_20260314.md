# 配置优化验收报告（2026-03-14）

## 本次优化

- 清理飞书 Wiki 相关残留暴露
  - `config/channels.json` 中 `channels.feishu.tools.wiki` 已关闭
  - `config/agents.json` 中各 agent 的 `feishu_search_doc_wiki` / `feishu_wiki_space` / `feishu_wiki_space_node` 白名单已移除
- 调整 DM 会话隔离
  - `openclaw.json` 中 `session.dmScope = per-channel-peer`

## 参考依据

- OpenClaw Session field details:
  - `dmScope` 支持 `main / per-peer / per-channel-peer / per-account-channel-peer`
- OpenClaw 官方建议：
  - 多用户 DM 场景优先使用 `per-channel-peer`

## 验收结果

### 1. Wiki 工具已从运行态移除

- `xiaodong`
  - 运行态 `systemPromptReport.tools.entries` 中已无任何 `wiki` 工具
- `xiaoguan`
  - `has_wiki_tools = false`
- `aduan`
  - `has_wiki_tools = false`
  - `knowledge_return_file` 仍然存在，说明本次清理没有误伤知识库链路

说明：

- Gateway 启动日志里仍会看到底层插件注册 `feishu_search_doc_wiki`
- 但它已经不再进入 agent 的实际可用工具清单
- 因此从 agent 行为角度，旧 Wiki 能力已被收敛掉

### 2. DM Scope 已切换到按渠道 + 对端隔离

- 配置读取结果：
  - `openclaw config get session.dmScope` 返回 `per-channel-peer`

- 使用 OpenClaw 已安装运行时导出的 `buildAgentPeerSessionKey` 做构造验证：

1. 旧行为
   - 输入：
     - `agentId=xiaodong`
     - `channel=feishu`
     - `peerId=ou_87bb675cf1a555992cf71df25f860c63`
     - `dmScope=main`
   - 输出：
     - `agent:xiaodong:main`

2. 新行为
   - 输入：
     - `agentId=xiaodong`
     - `channel=feishu`
     - `peerId=ou_87bb675cf1a555992cf71df25f860c63`
     - `dmScope=per-channel-peer`
   - 输出：
     - `agent:xiaodong:feishu:direct:ou_87bb675cf1a555992cf71df25f860c63`

3. Telegram 同理
   - 输出：
     - `agent:xiaodong:telegram:direct:8294029208`

## 影响说明

- 从现在开始，新的直聊消息不再全部折叠进 `agent:<agentId>:main`
- 同一 agent 下，不同渠道 / 不同对端会分到独立 DM session
- 这能降低：
- 多人 DM 串上下文
- 飞书与 Telegram 私聊内容互相污染

## 存量清理

本轮额外做了旧 `main` 直聊桶收口，并先做了逐 agent 备份。

备份文件：

- `agents/xiaodong/sessions/sessions.json.backup-pre-dm-scope-cleanup-20260314T113719.json`
- `agents/xiaoguan/sessions/sessions.json.backup-pre-dm-scope-cleanup-20260314T113719.json`
- `agents/finance/sessions/sessions.json.backup-pre-dm-scope-cleanup-20260314T113719.json`
- `agents/aduan/sessions/sessions.json.backup-pre-dm-scope-cleanup-20260314T113719.json`
- `agents/echo/sessions/sessions.json.backup-pre-dm-scope-cleanup-20260314T113719.json`

清理规则：

- `xiaodong`
  - 已存在新的 scoped 私聊桶，且比旧 `main` 更新，因此删除旧 `agent:xiaodong:main`
- `xiaoguan / finance / aduan / echo`
  - 旧 `main` 都是 `toolscan-*` 验收测试会话，不应再挂到未来真实私聊上，因此删除旧 `main`

清理后验证：

- `xiaodong`
  - 保留：
    - `agent:xiaodong:feishu:direct:ou_87bb675cf1a555992cf71df25f860c63`
  - 删除：
    - `agent:xiaodong:main`
- `xiaoguan / finance / aduan / echo`
  - `agent:<id>:main` 已删除
  - 当前没有错误地把测试桶迁移成真实私聊桶

## 剩余说明

- 历史已经存在的 `main` 会话不会自动改名；新的入站 DM 才会使用新的 key 形状
- 本次已经完成“旧 main 会话清理”，但没有做大规模 transcript 级迁移；这是刻意保守处理，避免把测试上下文并进真实用户会话
