# 飞书群消息无法读取问题诊断报告

**问题时间：** 2026-04-15
**报告人员：** Claude (Opus 4.6)

---

## 问题描述

Agent 无法读取飞书的群消息。

---

## 诊断结果

### ✅ 正常的配置

1. **openclaw-lark 插件已安装并启用**
   - 位置：`/Volumes/KenDisk/Coding/openclaw-runtime/extensions/openclaw-lark/`
   - 状态：enabled: true
   - 工具已注册：feishu_im_user_get_messages, feishu_chat_members 等

2. **飞书凭证配置正常**
   ```bash
   FEISHU_XIAODONG_APP_ID=cli_a904a148eab81bd8
   FEISHU_XIAODONG_APP_SECRET=l4qv5PgtwIzuWVfWVSCDtcbCXSv6TrQv
   ```

3. **工具权限已配置**
   - xiaodong agent 的 tools.allow 列表包含：
     - `feishu_im_user_get_messages` ✅
     - `feishu_chat_members` ✅
     - `feishu_im_user_search_messages` ✅
     - `feishu_chat` ✅

4. **日志显示插件加载成功**
   ```
   feishu_im: Registered feishu_im_user_message, feishu_im_user_get_messages, feishu_im_user_get_thread_messages, feishu_im_user_search_messages
   feishu_chat: Registered feishu_chat, feishu_chat_members
   ```

---

## ⚠️ 发现的问题

### 问题 1：群聊策略配置

**当前配置：**
```json
{
  "groupPolicy": "allowlist",
  "groups": {
    "oc_660c980239cd01d78c7dfe45d1a2d944": {
      "allowFrom": ["*"],
      "requireMention": true
    }
  },
  "requireMention": true
}
```

**问题分析：**
- `groupPolicy: "allowlist"` 表示只允许白名单中的群
- 当前只配置了一个群：`oc_660c980239cd01d78c7dfe45d1a2d944`
- 如果 Agent 需要读取其他群的消息，会被拒绝

**可能的原因：**
1. Agent 尝试读取的群不在白名单中
2. 群 ID 可能已经改变
3. 需要添加更多群到白名单

---

## 解决方案

### 方案 1：添加群到白名单（推荐）

如果你知道需要读取的群 ID，添加到配置中：

```json
{
  "groupPolicy": "allowlist",
  "groups": {
    "oc_660c980239cd01d78c7dfe45d1a2d944": {
      "allowFrom": ["*"],
      "requireMention": true
    },
    "oc_YOUR_NEW_GROUP_ID": {
      "allowFrom": ["*"],
      "requireMention": true
    }
  }
}
```

**如何获取群 ID：**
1. 在飞书群里发送消息给机器人
2. 查看 OpenClaw 日志，会显示 chat_id
3. 或使用 `feishu_chat` 工具列出所有群

### 方案 2：改为允许所有群（不推荐，安全风险）

```json
{
  "groupPolicy": "allow",  // 改为 allow
  "requireMention": true
}
```

### 方案 3：检查用户授权

Agent 使用**用户身份**读取消息，需要用户授权。

**检查步骤：**
1. 在飞书私聊窗口对机器人发送：
   ```
   请列出我当前未完成的飞书任务，只返回前 3 条
   ```

2. 如果提示需要授权，按照提示完成 OAuth 授权流程

3. 授权完成后，UAT 文件会保存到：
   ```
   /Volumes/KenDisk/Coding/openclaw-runtime/state/openclaw-feishu-uat/
   ```

---

## 诊断命令

### 1. 查看当前配置的群列表

```bash
jq '.channels.feishu.accounts.xiaodong.groups' /Volumes/KenDisk/Coding/openclaw-runtime/openclaw.json
```

### 2. 检查用户授权状态

```bash
ls -la /Volumes/KenDisk/Coding/openclaw-runtime/state/openclaw-feishu-uat/
```

### 3. 查看最近的飞书相关日志

```bash
tail -100 /Volumes/KenDisk/Coding/openclaw-runtime/logs/runtime-openclaw/openclaw-*.log | grep -i feishu
```

### 4. 测试飞书工具是否可用

在飞书私聊窗口对机器人说：
```
请使用 feishu_chat 工具列出我加入的所有群聊
```

---

## 下一步行动

1. **确认问题群的 ID**
   - 在目标群里 @机器人 发送消息
   - 查看日志获取 chat_id

2. **添加群到白名单**
   - 编辑 `openclaw.json`
   - 在 `groups` 对象中添加新的群 ID

3. **重启 OpenClaw**（如果修改了配置）
   ```bash
   # 如果 OpenClaw 在运行，需要重启
   ```

4. **验证修复**
   - 在群里 @机器人 发送消息
   - 检查机器人是否能正常响应

---

## 相关文档

- [飞书 IM 消息读取工具](../extensions/openclaw-lark/node_modules/@larksuite/openclaw-lark/skills/feishu-im-read/SKILL.md)
- [OpenClaw Lark 授权 SOP](./openclaw-lark-auth-sop.md)

---

**诊断时间：** 2026-04-15 15:45
**状态：** 待用户确认群 ID 并修复配置
