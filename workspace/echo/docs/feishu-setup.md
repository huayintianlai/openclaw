# Echo 飞书机器人配置指南

## 一、环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# Echo 飞书机器人配置
FEISHU_ECHO_APP_ID=cli_xxxxxxxxxxxxxxxx
FEISHU_ECHO_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## 二、获取 App ID 和 App Secret

### 1. 登录飞书开放平台

访问：https://open.feishu.cn/app

### 2. 创建企业自建应用

1. 点击"创建企业自建应用"
2. 应用名称：**艾可**（Echo）
3. 应用描述：新媒体运营与获客数字员工
4. 应用图标：上传 Echo 的头像

### 3. 获取凭证

在应用详情页 → "凭证与基础信息"：
- **App ID**：复制到 `FEISHU_ECHO_APP_ID`
- **App Secret**：复制到 `FEISHU_ECHO_APP_SECRET`

### 4. 配置权限

在"权限管理"中添加以下权限：

#### 消息与群组权限
- ✅ 获取与发送单聊、群组消息
- ✅ 以应用的身份发消息
- ✅ 接收群聊中@机器人消息事件
- ✅ 获取群组信息

#### 多维表格权限
- ✅ 查看、编辑和管理多维表格
- ✅ 查看多维表格
- ✅ 编辑多维表格

#### 云文档权限（可选）
- ✅ 查看、评论和编辑云空间中所有文件
- ✅ 查看云空间中所有文件

### 5. 配置事件订阅

在"事件订阅"中添加：

#### 消息事件
- ✅ 接收消息 v2.0
- ✅ 消息已读

#### 请求网址配置
- 请求网址：`http://your-gateway-url:18789/channels/feishu/webhook`
- 加密策略：不加密（或根据需要配置）

### 6. 发布版本

1. 在"版本管理与发布"中创建版本
2. 填写版本说明
3. 提交审核
4. 审核通过后发布

### 7. 添加可用范围

在"可用性"中：
- 添加可用人员（ou_dc95eabe8982323faf7e9f3701e61e22, ou_87bb675cf1a555992cf71df25f860c63）
- 或添加可用部门

---

## 三、OpenClaw 配置

### 已完成的配置

在 `openclaw.json` 中已添加：

#### 1. 环境变量引用
```json
"env": {
  "FEISHU_ECHO_APP_ID": "${FEISHU_ECHO_APP_ID}",
  "FEISHU_ECHO_APP_SECRET": "${FEISHU_ECHO_APP_SECRET}"
}
```

#### 2. 飞书账号配置
```json
"channels": {
  "feishu": {
    "accounts": {
      "echo": {
        "appId": "${FEISHU_ECHO_APP_ID}",
        "appSecret": "${FEISHU_ECHO_APP_SECRET}",
        "botName": "艾可",
        "enabled": true,
        "groupPolicy": "allowlist",
        "groupAllowFrom": ["oc_660c980239cd01d78c7dfe45d1a2d944"],
        "requireMention": true,
        "dmPolicy": "allowlist",
        "allowFrom": [
          "ou_dc95eabe8982323faf7e9f3701e61e22",
          "ou_87bb675cf1a555992cf71df25f860c63"
        ]
      }
    }
  }
}
```

#### 3. Agent 绑定
```json
"bindings": [
  {
    "agentId": "echo",
    "match": {
      "channel": "feishu",
      "accountId": "echo"
    }
  }
]
```

---

## 四、测试配置

### 1. 重启 OpenClaw Gateway

```bash
cd /Users/xiaojiujiu2/Documents/openclaw-docker
docker-compose restart openclaw-gateway
```

### 2. 检查日志

```bash
docker-compose logs -f openclaw-gateway | grep echo
```

### 3. 测试飞书消息

1. 在飞书中找到"艾可"机器人
2. 发送测试消息：`你好`
3. 检查是否收到回复

### 4. 测试群组消息

1. 将"艾可"机器人添加到测试群组
2. @艾可 发送消息
3. 检查是否收到回复

---

## 五、通知功能配置（可选）

如果需要 Echo 主动发送通知（如文章待审批通知），有两种方案：

### 方案 A：使用飞书机器人发送消息

通过 OpenClaw 的飞书工具发送消息到指定用户或群组。

**优点**：
- 集成在 OpenClaw 中，无需额外配置
- 可以发送富文本消息（卡片、按钮等）

**缺点**：
- 需要用户先与机器人建立会话

### 方案 B：使用飞书 Webhook

创建群组 Webhook，Echo 直接发送消息到群组。

**步骤**：
1. 在飞书群组中添加"自定义机器人"
2. 获取 Webhook URL
3. 在 `.env` 中配置：
   ```bash
   FEISHU_ECHO_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx
   ```
4. Echo 使用 `exec curl` 发送通知

**优点**：
- 简单直接，无需建立会话
- 可以发送到指定群组

**缺点**：
- 只能发送文本和简单格式
- 需要额外配置

---

## 六、常见问题

### Q1：机器人无法收到消息

**检查项**：
1. App ID 和 App Secret 是否正确
2. 事件订阅是否配置正确
3. 请求网址是否可访问
4. 用户是否在可用范围内
5. OpenClaw Gateway 是否正常运行

### Q2：机器人无法发送消息

**检查项**：
1. 是否有"发送消息"权限
2. 用户是否先与机器人建立过会话
3. 群组中是否添加了机器人

### Q3：多维表格无法访问

**检查项**：
1. 是否有多维表格权限
2. 表格是否共享给机器人
3. App Token 和 Table ID 是否正确

---

## 七、下一步

配置完成后，Echo 将能够：

1. ✅ 通过飞书接收用户消息
2. ✅ 在飞书中回复用户
3. ✅ 访问飞书多维表格（情报中心、内容日历表）
4. ✅ 发送通知（如果配置了通知功能）

**建议测试流程**：
1. 测试基本对话功能
2. 测试多维表格读写
3. 测试通知功能（如果需要）
4. 测试完整的公众号文章创作流程

---

**文档版本**：v1.0
**最后更新**：2026-03-13
**维护人**：Echo（艾可）
