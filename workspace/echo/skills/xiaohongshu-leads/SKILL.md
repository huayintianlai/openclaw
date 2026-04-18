---
name: xiaohongshu-leads
description: 小红书意向客户管理与私信话术生成。通过本地 xiaohongshu-mcp（localhost:18060）搜索笔记、采集评论、识别意向客户，自动生成私信话术草稿（[模拟稿]前缀），写入飞书「意向客户池」供人工审核。适用场景：(1) 按关键词采集新线索并生成话术；(2) 查看/处理待跟进线索；(3) 更新跟进状态；(4) 用户提到「意向客户」「私信」「话术」「线索」「小红书获客」「采集」。
---

# 小红书意向客户 Skill

## 依赖

- **xiaohongshu-mcp**：本地 MCP 服务，地址 `http://localhost:18060/mcp`，已用账号 `xiaohongshu-mcp` 登录
- **飞书意向客户池**：app_token `PClsbQNDJaj4oks2YfQcXVGxnnf`，table_id `tbldDJnE3nkErnim`

## MCP 调用方式

```python
import subprocess, json

def call_mcp(tool_name, arguments):
    payload = json.dumps([
        {"jsonrpc": "2.0", "method": "initialize",
         "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "echo", "version": "1.0"}}, "id": 1},
        {"jsonrpc": "2.0", "method": "tools/call",
         "params": {"name": tool_name, "arguments": arguments}, "id": 2}
    ])
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", "http://localhost:18060/mcp",
         "-H", "Content-Type: application/json", "-d", payload],
        capture_output=True, text=True
    )
    responses = json.loads(result.stdout)
    for r in responses:
        if r.get("id") == 2:
            return r["result"]["content"][0]["text"]
```

## 可用 MCP 工具

| 工具 | 用途 | 必填参数 |
|------|------|----------|
| `check_login_status` | 检查登录态 | 无 |
| `search_feeds` | 搜索笔记 | keyword |
| `get_feed_detail` | 获取笔记详情+评论 | feed_id, xsec_token |
| `send_comment` | 发评论 | feed_id, xsec_token, content |
| `user_profile` | 查用户主页 | user_id, xsec_token |

## 核心工作流

### Step 1：搜索笔记

```python
# 按关键词搜索，取最新笔记
result = call_mcp("search_feeds", {
    "keyword": "法国公司注册",
    "filters": {
        "sort_by": "最新",
        "publish_time": "一周内",
        "note_type": "不限"
    }
})
# result 是 JSON 字符串，解析后得到 feeds 列表
# 每条 feed 包含：id(=feed_id), xsecToken, noteCard.user, noteCard.interactInfo
```

### Step 2：获取评论

```python
# 对每条笔记获取评论（最多 50 条一级评论）
detail = call_mcp("get_feed_detail", {
    "feed_id": feed["feed_id"],
    "xsec_token": feed["xsec_token"],
    "load_all_comments": True,
    "limit": 50
})
```

### Step 3：过滤意向客户

参考 `references/filters.md` 中的同行特征词和意向关键词。

**过滤逻辑（按顺序）**：
1. 跳过作者自己的评论
2. 跳过同行广告（昵称或内容含同行特征词）
3. 跳过无意向评论（内容不含任何意向关键词）
4. 通过的记录，判断需求类型和优先级

### Step 4：生成私信话术

根据「需求类型」+「评论原文」+「笔记标题」生成话术。
话术模板见 `references/templates.md`。

生成规则：
- 第一句呼应评论原文关键词
- 提供具体价值，不空洞
- 80-120 字，结尾引导加微信
- 写入时加 `[模拟稿]` 前缀

### Step 5：写入飞书

```javascript
// 单条写入
feishu_bitable_app_table_record({
  action: "create",
  app_token: "PClsbQNDJaj4oks2YfQcXVGxnnf",
  table_id: "tbldDJnE3nkErnim",
  fields: {
    "笔记ID": feed_id,
    "🔗笔记链接": {"link": "https://www.xiaohongshu.com/explore/" + feed_id},
    "📝笔记标题": title,
    "关键词": keyword,
    "👤评论用户": nickname,
    "💬评论原文": comment_content,
    "🏷️需求类型": demand_type,  // 单选选项名
    "📝私信话术": "[模拟稿] " + generated_script,
    "⭐优先级": priority  // 高/中/低
  }
});

// 如果记录已存在（笔记ID+评论用户重复），改用 update
```

### Step 6：汇报审核

生成完成后向小九九汇报：
- 本次采集笔记数 / 评论总数
- 通过筛选的意向客户数
- 各需求类型分布
- 高优先级线索摘要（最多 5 条）
- 飞书链接：https://99love.feishu.cn/base/PClsbQNDJaj4oks2YfQcXVGxnnf

等待审核指令（可发/需改/禁发），按反馈处理。

---

## 常见操作

### 查看待审核线索

```javascript
feishu_bitable_app_table_record({
  action: "list",
  app_token: "PClsbQNDJaj4oks2YfQcXVGxnnf",
  table_id: "tbldDJnE3nkErnim",
  filter: {
    conjunction: "and",
    conditions: [
      { field_name: "跟进状态", operator: "is", value: ["待跟进"] },
      { field_name: "📝私信话术", operator: "isNotEmpty" }
    ]
  },
  sort: [{field_name: "创建时间", desc: true}],
  page_size: 50
});
```

### 更新跟进状态

```javascript
feishu_bitable_app_table_record({
  action: "update",
  app_token: "PClsbQNDJaj4oks2YfQcXVGxnnf",
  table_id: "tbldDJnE3nkErnim",
  record_id: "recXXXX",
  fields: {
    "跟进状态": "已私信",
    "📝跟进备注": "已发送私信"
  }
});
```

---

## 回复草稿生成原则（核心约束）

### 硬性禁止
- **不能发私信**，只能做评论区公开回复（`send_comment`）
- **回复内容绝对不能出现**：微信号、QR码、任何联系方式（封号风险）
- **不能有 AI 味**：禁用「欢迎咨询」「专业团队」「多年经验」「首先/其次/最后」等结构

### 回复目标
让对方觉得「这人懂」→ 主动来私信你。引流终点是私信，不是评论区成交。

### 人设动态切换

| 评论者特征 | 扮演角色 | 风格 |
|-----------|---------|------|
| 刚起步新卖家 | 过来人大佬 | 点破一个关键坑，语气像指点晚辈 |
| 有经验但卡住 | 同行交流 | 平等探讨，分享具体经验 |
| 明确找服务商 | 专业服务商 | 直接回应痛点，展示专业度 |
| 吐槽平台 | 懂行旁观者 | 共情+给出一个实用解法 |

### 好回复的结构
1. 一个具体有价值的信息点（让人觉得「这人懂」）
2. 轻微悬念或钩子（让人想追问）
3. 口语化，有点个人色彩，控制在 30-60 字

**示例**（评论者问「法国公司注册资质要求高吗」）：
> 资质不是卡点，卡的是银行开户那一步。很多人注册完才发现账户根本开不了，白忙一场。

### 审核流程（所有回复必须经此流程）

```
发现意向评论
    ↓
Echo 生成回复草稿 → 推飞书消息给小九九（含：笔记标题/评论原文/草稿）
    ↓
小九九选择：【用这条】【我来改（直接回复消息）】【跳过】
    ↓
Echo 执行 send_comment（或放弃）
```

**Echo 不得在未经审核的情况下自主调用 `send_comment`。**

---

## 注意事项

- 话术写入时**必须加 `[模拟稿]` 前缀**
- `📅评论时间` MCP 返回的是时间戳或字符串，写入前需转为毫秒时间戳
- `同行拉黑` 是按钮字段（type=3001），无法 API 写入，需飞书界面操作
- MCP 每次调用间隔 ≥1 秒，避免触发限流
- 每次处理上限 50 条评论/10 条笔记，分批执行
- 登录态失效时，运行 `check_login_status` 确认，失效则提示小九九重新扫码登录
