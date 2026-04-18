# OpenClaw Lark 官方授权 SOP

目标：让 `@larksuite/openclaw-lark` 的官方用户态工具真正可用，包括：

- `feishu_task_*`
- `feishu_calendar_*`
- `feishu_fetch_doc`
- `feishu_search_doc_wiki`

## 现状

- 官方插件已经加载完成，生产和 canary 都在运行。
- 官方 UAT 存储已经持久化到：
  - `instances/kentclaw/data/state/openclaw-feishu-uat/`
- 旧 `xiaodong` token 无法自动迁移，原因是 refresh token 已失效。

## 最短授权路径

在对应的飞书私聊窗口里，直接对对应机器人发一条真实业务请求，让它触发官方工具。

推荐最短触发语：

### 小东

```text
请列出我当前未完成的飞书任务，只返回前 3 条
```

或：

```text
请查询我的主日历
```

### 小冠

```text
请列出我当前未完成的飞书任务，只返回前 3 条
```

### 财务 / 阿段 / Echo

```text
请查询我的主日历
```

## 预期行为

如果该账号尚未完成官方授权，机器人应触发官方 OAuth 流程，而不是返回旧插件错误。

授权完成后，UAT 文件会落到：

```text
instances/kentclaw/data/state/openclaw-feishu-uat/
```

## 本地复验

```bash
./scripts/check_lark_uat.sh
```

如果要复验生产健康：

```bash
./scripts/healthcheck_openclaw.sh --instance kent --level quick
./scripts/healthcheck_openclaw.sh --instance kent --level full
```

## 已知限制

- 工具已注册，不等于用户已授权。
- 首次真实调用 `feishu_task_*` / `feishu_calendar_*` 时，仍可能返回 `need_user_authorization`。
- 这是正常现象，不是插件加载失败。
