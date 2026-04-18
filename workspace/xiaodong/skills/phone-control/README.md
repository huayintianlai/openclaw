# 手机控制技能文档

## 概述
通过 OpenClaw Agent 控制4台安卓手机执行小红书获客任务。

## 可用设备
- 设备1: a7b24c15 (M2002J9E)
- 设备2: ac7b4cb9 (M2002J9E)
- 设备3: e2879f39 (Redmi K30)
- 设备4: e2d6f5c3 (Redmi K30 5G)

## 使用方法

### 在 OpenClaw 对话中调用

用户可以直接对 xiaodong 说：

```
"用手机1打开小红书搜索跨境电商"
"让手机2监控Cdiscount关键词"
"所有手机同时搜索速卖通"
```

### Agent 执行命令

```bash
# 单个任务
exec ~/scripts/phone_control.sh 1 "打开小红书搜索跨境电商"

# 多手机并发
exec ~/scripts/phone_control.sh 1 "监控速卖通" &
exec ~/scripts/phone_control.sh 2 "监控Cdiscount" &
exec ~/scripts/phone_control.sh 3 "监控Bol" &
exec ~/scripts/phone_control.sh 4 "监控Coupang" &
```

## 常见任务模板

### 1. 关键词监控
```bash
exec ~/scripts/phone_control.sh 1 "打开小红书，搜索'速卖通开店'，每10分钟刷新一次，发现新帖子立即截图"
```

### 2. 评论区挖掘
```bash
exec ~/scripts/phone_control.sh 2 "打开小红书，搜索'跨境电商'，进入前10条笔记，找到所有咨询开店的评论"
```

### 3. 自动回复
```bash
exec ~/scripts/phone_control.sh 3 "打开小红书私信，回复所有未读消息：您好，关于开店问题可以详细聊聊"
```

### 4. 点赞引流
```bash
exec ~/scripts/phone_control.sh 4 "打开小红书，搜索'Cdiscount'，给前20条笔记点赞"
```

## 注意事项

1. **API Key 配置**：确保 `/Users/xiaojiujiu2/Documents/coding/AutoGLM/.env` 中已配置智谱 API Key
2. **手机连接**：确保4台手机通过 USB 连接到 Mac，运行 `adb devices` 验证
3. **成本控制**：智谱 API 按调用次数计费，建议设置每日预算
4. **防风控**：避免频繁操作同一账号，建议每台手机间隔5-10分钟
5. **后台运行**：使用 `&` 让任务在后台执行，不阻塞 Agent 对话

## 故障排查

### 手机连接失败
```bash
# 检查 ADB 连接
adb devices

# 重启 ADB 服务
adb kill-server && adb start-server
```

### API 调用失败
```bash
# 检查 API Key 配置
cat /Users/xiaojiujiu2/Documents/coding/AutoGLM/.env

# 测试 API 连接
curl -X POST https://open.bigmodel.cn/api/paas/v4/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"glm-4v-plus","messages":[{"role":"user","content":"测试"}]}'
```

### 任务执行超时
```bash
# 增加最大步骤数
export PHONE_AGENT_MAX_STEPS=200
```
