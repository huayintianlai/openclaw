# 阿峰飞书Bot创建完成

## 创建信息

**创建时间**：2026-04-16  
**Bot名称**：阿峰  
**Bot ID**：afeng  
**App ID**：cli_a96a6b2526f89cc3

## 配置位置

### 1. 飞书Channel配置
- 文件：`/Volumes/KenDisk/Coding/openclaw-runtime/openclaw.json`
- 位置：`channels.feishu.accounts.afeng`
- 配置内容：
  ```json
  {
    "allowFrom": ["ou_8a7c44fa19bac7c9c3b2aeb74ee0a440"],
    "appId": "cli_a96a6b2526f89cc3",
    "appSecret": "${FEISHU_AFENG_APP_SECRET}",
    "botName": "阿峰",
    "dmPolicy": "allowlist",
    "enabled": true,
    "groupPolicy": "allow",
    "requireMention": true
  }
  ```

### 2. Agent配置
- 文件：`/Volumes/KenDisk/Coding/openclaw-runtime/openclaw.json`
- 位置：`agents.list[]`
- Agent目录：`/Volumes/KenDisk/Coding/openclaw-runtime/agents/afeng/agent`
- 工作区：`/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng`

### 3. 环境变量
- 文件：`/Volumes/KenDisk/Coding/openclaw-runtime/.env`
- 变量：
  ```
  FEISHU_AFENG_APP_ID=cli_a96a6b2526f89cc3
  FEISHU_AFENG_APP_SECRET=RUKdDTqzAxIMG5oA4TmoTfOhuN8ZR5QM
  ```

### 4. Secrets文件
- 文件：`~/.openclaw/credentials/lark.secrets.json`
- 内容：包含appSecret

## 阿峰的能力定位

### 主要职责
海外公司注册和海外平台注册专员

### 核心能力
1. **网页自动化填写表单**
   - 自动填写公司注册表单
   - 自动填写电商平台入驻表单
   - 表单数据验证和提交

2. **制作审核材料**
   - 根据要求生成各类注册文件
   - 整理和格式化审核材料
   - 文档翻译和本地化

3. **文件识别能力**
   - 快速提取身份证、护照等证件信息
   - 识别营业执照、税务登记等企业文件
   - 提取合同、协议中的关键信息

4. **新人流程指引**
   - 提供注册流程的详细指导
   - 解答常见问题
   - 提供最佳实践建议

### 主要服务场景
- **法国公司注册**：SARL、SAS、个体工商户等
- **欧盟电商平台注册**：Amazon、eBay等欧洲站

## 已授权工具

- `browser` - 网页自动化
- `bill_ocr_id_card` - 身份证识别
- `bill_generate` - 文档生成
- 飞书消息、文档、多维表格等工具
- 文件读写、记忆存储等基础工具

## 使用方式

### 1. 飞书中直接对话
在飞书中找到"阿峰"机器人，发送消息即可开始对话。

### 2. 通过OpenClaw CLI
```bash
openclaw agent --to afeng --message "你好"
```

### 3. 权限设置
当前仅允许用户 `ou_8a7c44fa19bac7c9c3b2aeb74ee0a440` 使用。
如需添加其他用户，修改配置中的 `allowFrom` 数组。

## 状态

✅ Bot创建成功  
✅ 配置已完成  
✅ Gateway已重启  
✅ 可以开始使用

## 下一步

1. 在飞书中测试与阿峰的对话
2. 根据实际使用情况调整工具权限
3. 完善AGENT.md中的详细指引
4. 添加具体的注册流程文档
