# TOOLS.md - Echo 工具配置

## GoldFinger CLI

GoldFinger 是小红书 RPA 采集系统，Echo 通过 CLI 调用它的功能。

### 环境变量

```bash
# GoldFinger API 地址（本地开发）
GOLDFINGER_API_URL=http://localhost:8000

# 生产环境（Docker）
GOLDFINGER_API_URL=http://goldfinger-control:8000
```

### 常用命令

```bash
# 立即采集指定关键词
goldfinger collect "cdiscount店铺"

# 查询当前任务状态
goldfinger status

# 查询定时任务列表
goldfinger schedules

# 暂停定时任务
goldfinger schedule-pause 1

# 恢复定时任务
goldfinger schedule-resume 1

# 立即运行定时任务
goldfinger schedule-run 1

# 创建定时任务（每天 09:00-10:00 随机执行）
goldfinger schedule-add "fnac" "09:00" "10:00"

# 取消正在运行的任务
goldfinger cancel "cdiscount"
```

### CLI 脚本位置

```bash
/Users/xiaojiujiu2/Documents/coding/GoldFinger/skills/goldfinger-cli/goldfinger
```

可以在 Echo workspace 创建软链接：

```bash
ln -s /Users/xiaojiujiu2/Documents/coding/GoldFinger/skills/goldfinger-cli/goldfinger \
      /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/workspace/echo/goldfinger
```

---

## Mobile Runtime

Echo 现在通过共享 `mobile_*` 工具调度安卓手机，适合做小红书观察、搜索和微信草稿准备。

### 推荐设备

- `echo-xhs-1`：主力小红书手机
- `echo-xhs-2`：备用小红书手机
- `xiaodong-main`：跨应用编排时的通用手机

### 任务模板优先

- 小红书搜索：`mobile_run_task` + `flow_id: "search_in_app"`
- 微信只读检查：`mobile_run_task` + `flow_id: "wechat_read_only"`
- 草稿准备：`mobile_run_task` + `flow_id: "draft_message"`，并显式审批

### 示例

```javascript
await mobile_run_task({
  device_selector: { alias: "echo-xhs-1" },
  flow_id: "search_in_app",
  inputs: {
    app: "xhs",
    query: "cdiscount 店铺"
  },
  approval_policy: "auto"
});
```

不要在 Echo 的业务流程中直接使用手机序列号、`adb` 或 AutoGLM 脚本。

---

## 飞书多维表格

## 官方飞书工具迁移说明

- 当前仓库已切换到官方 `openclaw-lark`。
- 多维表格统一使用官方工具：`feishu_bitable_app` / `feishu_bitable_app_table` / `feishu_bitable_app_table_field` / `feishu_bitable_app_table_record` / `feishu_bitable_app_table_view`。
- 记录查询、创建、更新统一通过 `feishu_bitable_app_table_record` 的 `action=list|create|update` 完成。
- 字段读取统一使用 `feishu_bitable_app_table_field` 的 `action=list`。

### 情报中心（06_情报中心）

**用途**：读取跨境平台情报，作为公众号选题素材

```
app_token: PthAwTfrViHCr5kS2xUc4gNLnEd
table_id: tblR0Ox7ZZTEeZay
```

**关键字段**：
- 雷达层级：宏观/店铺/同行
- 平台或主题
- 变化摘要
- 对中国卖家的潜在影响
- 来源链接
- 验证状态

**使用示例**：

```javascript
# 读取最近已验证的情报
feishu_bitable_app_table_record({
  action: "list",
  app_token: "PthAwTfrViHCr5kS2xUc4gNLnEd",
  table_id: "tblR0Ox7ZZTEeZay",
  filter: {
    conjunction: "and",
    conditions: [
      { field_name: "验证状态", operator: "is", value: ["已验证"] }
    ]
  },
  sort: [{ field_name: "创建时间", desc: true }],
  page_size: 20
});
```

### 内容日历表（02_内容日历）

**用途**：记录公众号文章创作、审批、发布全流程

```
app_token: Z3DEboviLaJAlXsdUPvcItgrnZd
table_id: tblIv3haHPEPAd3Y
view_id: vewGAQfmMX
```

**关键字段**：
- 📅 创建时间（日期时间，自动）
- 📝 文章标题（文本）
- 📄 文章内容（多行文本，Markdown 格式）
- 🏷️ 选题方向（单选：平台政策/实操案例/行业趋势/其他）
- 📊 素材来源（多选：情报中心/知识库/网络搜索/小红书）
- ✅ 审批状态（单选：待审批/已批准/已拒绝/需修改）
- 💬 审批备注（多行文本）
- 📅 发布时间（日期时间）
- 🔗 公众号链接（URL）
- 👁️ 阅读量（数字）
- 💰 转化客户数（数字）

**使用示例**：

```javascript
# 创建新文章记录
feishu_bitable_app_table_record({
  action: "create",
  app_token: "Z3DEboviLaJAlXsdUPvcItgrnZd",
  table_id: "tblIv3haHPEPAd3Y",
  fields: {
    "文章标题": "Cdiscount 2026 最新招商政策解读",
    "文章内容": "# Cdiscount 2026 最新招商政策解读\n\n...",
    "选题方向": "平台政策",
    "素材来源": ["情报中心", "知识库"],
    "审批状态": "待审批"
  }
});

# 读取待审批的文章
feishu_bitable_app_table_record({
  action: "list",
  app_token: "Z3DEboviLaJAlXsdUPvcItgrnZd",
  table_id: "tblIv3haHPEPAd3Y",
  filter: {
    conjunction: "and",
    conditions: [
      { field_name: "审批状态", operator: "is", value: ["待审批"] }
    ]
  },
  page_size: 10
});

# 更新审批状态
feishu_bitable_app_table_record({
  action: "update",
  app_token: "Z3DEboviLaJAlXsdUPvcItgrnZd",
  table_id: "tblIv3haHPEPAd3Y",
  record_id: "recXXXX",
  fields: {
    "审批状态": "已批准",
    "审批备注": "内容质量很好，可以发布"
  }
});

# 更新发布数据
feishu_bitable_app_table_record({
  action: "update",
  app_token: "Z3DEboviLaJAlXsdUPvcItgrnZd",
  table_id: "tblIv3haHPEPAd3Y",
  record_id: "recXXXX",
  fields: {
    "发布时间": 1710316800000,
    "公众号链接": "https://mp.weixin.qq.com/s/xxxxx",
    "阅读量": 1500,
    "转化客户数": 3
  }
});
```

### 公众号运营表（02_公众号运营）

**用途**：记录公众号运营数据和效果分析

```
app_token: Z3DEboviLaJAlXsdUPvcItgrnZd
table_id: tblDy6PjwFobTQs7
view_id: vewCUrjqdy
```

**说明**：此表用于汇总分析，具体字段结构待确认。建议主要使用"内容日历表"进行日常操作。

### 意向客户池（GoldFinger）

**用途**：读取 AI 识别的意向客户，审核回复话术

```
app_token: PClsbQNDJaj4oks2YfQcXVGxnnf
table_id: tbldDJnE3nkErnim
```

**关键字段**：
- 🔗笔记链接
- 📝笔记标题
- 👤评论用户
- 💬评论原文
- 🏷️需求类型
- 📝私信话术
- 🎯意向等级
- ✅审核状态

**使用示例**：

```javascript
# 读取待审核的意向客户
feishu_bitable_app_table_record({
  action: "list",
  app_token: "PClsbQNDJaj4oks2YfQcXVGxnnf",
  table_id: "tbldDJnE3nkErnim",
  filter: {
    conjunction: "and",
    conditions: [
      { field_name: "审核状态", operator: "is", value: ["待审核"] }
    ]
  },
  page_size: 50
});

# 更新审核状态
feishu_bitable_app_table_record({
  action: "update",
  app_token: "PClsbQNDJaj4oks2YfQcXVGxnnf",
  table_id: "tbldDJnE3nkErnim",
  record_id: "recXXXX",
  fields: {
    "审核状态": "已批准",
    "审核备注": "话术符合品牌调性，可以发送"
  }
});
```

---

## 知识库搜索

使用 `knowledge_search` 查询历史文章、行业资料、公司文档。

```python
# 搜索跨境电商相关内容
knowledge_search(query="Cdiscount平台政策", top_k=5)

# 搜索历史公众号文章
knowledge_search(query="速卖通运营技巧", top_k=3)
```

---

## Markdown 转换

### 转换方案

**目标**：将 Markdown 格式文章转换为公众号可用的 HTML 格式

**推荐方案**：使用在线转换 API

#### 选项 A：md.openwrite.cn（推荐）

```javascript
async function convertMarkdownToWechat(markdown) {
  // 调用转换 API
  const response = await fetch('https://md.openwrite.cn/api/convert', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ markdown })
  });

  const html = await response.text();
  return html;
}
```

#### 选项 B：lab.lyric.im/wxformat

```javascript
// 使用 lyric.im 的转换服务
// API 文档：https://lab.lyric.im/wxformat/
```

#### 选项 C：本地部署 md2wx

```bash
# 部署开源工具 md2wx
# 更可控，但需要维护
```

**使用流程**：
1. Echo 生成 Markdown 文章
2. 调用转换 API 获取格式化 HTML
3. 保存 HTML 文件到 `articles/` 目录
4. 使用 Browser 工具或手动复制粘贴到公众号后台

---

## 浏览器自动化

### 公众号后台排版（Browser 工具）

**架构**：OpenClaw Route #3（Gateway 在 Docker，Browser 在 Mac 主机）

**前置条件**：
- Mac 主机上已安装 Chrome 浏览器
- OpenClaw Browser Relay 扩展已启用（用户需手动点亮）
- Gateway 可以访问 Mac 主机的 Browser 节点

**步骤**：

#### 1. 打开公众号后台
```javascript
await browser({
  target: "node",
  node: "mac-browser-node",  // Mac 主机上的 Browser 节点
  profile: "chrome",
  url: "https://mp.weixin.qq.com"
});
```

#### 2. 检查登录状态
```javascript
// 检查是否已登录
// 如果未登录，提示用户扫码登录
// 等待用户完成登录
```

#### 3. 创建新图文
```javascript
// 点击"新建图文"按钮
// 等待编辑器加载
```

#### 4. 粘贴内容
```javascript
// 将转换后的 HTML 粘贴到编辑器
// 使用 JavaScript 注入或模拟粘贴操作
```

#### 5. 预览和保存
```javascript
// 点击预览按钮
// 检查格式是否正确
// 保存草稿
```

**关键技术点**：
- 使用 OpenClaw Route #3 架构（Gateway 在 Docker，Browser 在 Mac 主机）
- 需要用户手动点亮 OpenClaw Browser Relay 扩展
- 页面快照优化（使用最小必要范围）
- 异常重试策略

**参考文档**：`/Users/xiaojiujiu2/Documents/openclaw-docker/docs/xiaodong-browser-ops.md`

**降级方案**：
如果 Browser 自动化失败（登录失效、页面改版等）：
1. Echo 生成 Markdown 文件
2. 保存到 `articles/` 目录
3. 提供转换后的 HTML 文件
4. 用户手动复制粘贴到公众号后台

**注意**：
- 浏览器自动化脚本需要根据实际页面结构编写
- 建议先手动操作一遍，记录步骤
- 可以参考 GoldFinger 的 Playwright 脚本
- 定期测试，及时更新脚本（应对页面改版）

---

## 记忆系统（Mem0）

**Echo 使用 Mem0 作为唯一的记忆管理系统。**

### 可用工具

```javascript
// 1. 存储记忆
memory_store({
  content: "[类型] 主题 - 核心内容\n时间：YYYY-MM-DD\n效果：数据指标\n来源：触发事件"
});

// 2. 搜索记忆
memory_search({
  query: "搜索关键词"
});

// 3. 列出所有记忆
memory_list();

// 4. 获取特定记忆
memory_get({
  memory_id: "mem_xxx"
});

// 5. 删除记忆
memory_forget({
  memory_id: "mem_xxx"
});
```

### 使用场景

#### 场景 1：公众号文章发布后

```javascript
// 存储文章效果
memory_store({
  content: `[公众号] ${文章标题} - 发布效果记录
时间：${发布日期}
效果：阅读量 ${阅读量}，转化客户 ${转化数} 人
素材来源：${情报中心/小红书/知识库}
选题方向：${平台政策/实操案例/行业趋势}
读者反馈：${正面/负面/建议}`
});
```

#### 场景 2：小红书采集任务完成后

```javascript
// 存储关键词效果
memory_store({
  content: `[关键词效果] ${关键词} - 采集结果分析
时间：${采集日期}
效果：采集 ${总数} 条，意向客户 ${意向数} 人，转化率 ${转化率}%
笔记质量：平均点赞 ${平均点赞}，平均评论 ${平均评论}
建议：${优先级调整建议}`
});
```

#### 场景 3：审批话术学习

```javascript
// 存储审批通过的案例
memory_store({
  content: `[审批案例-通过] ${需求类型} - 话术模板
时间：${审批日期}
评论原文：${评论内容}
回复话术：${话术内容}
审批备注：${人工反馈}
效果：${是否收到私信回复}`
});

// 存储审批拒绝的案例
memory_store({
  content: `[审批案例-拒绝] ${需求类型} - 避免模式
时间：${审批日期}
评论原文：${评论内容}
拒绝原因：${人工反馈}
教训：${避免什么样的话术或场景}`
});
```

#### 场景 4：策略优化

```javascript
// 每周分析时，搜索历史数据
const 关键词数据 = await memory_search({
  query: "关键词效果 转化率"
});

const 公众号数据 = await memory_search({
  query: "公众号 阅读量 转化"
});

// 分析后存储优化建议
memory_store({
  content: `[策略优化] 每周数据分析 - ${日期}
时间：${分析日期}
发现：
1. ${发现1}
2. ${发现2}
优化建议：
1. ${建议1}
2. ${建议2}
预期效果：${预期提升}`
});
```

### 记忆检索技巧

```javascript
// 1. 搜索特定类型的记忆
memory_search({ query: "公众号 转化率" });
memory_search({ query: "关键词效果 cdiscount" });
memory_search({ query: "审批案例 店铺咨询" });

// 2. 搜索时间相关的记忆
memory_search({ query: "2026-03 公众号" });
memory_search({ query: "最近 关键词效果" });

// 3. 搜索效果数据
memory_search({ query: "转化率 高于 30%" });
memory_search({ query: "阅读量 2000" });
```

### 自动召回机制

**Mem0 配置了自动召回（autoRecall: true）**

每次对话开始时，Mem0 会自动：
1. 分析当前对话上下文
2. 从向量数据库中检索最相关的 5 条记忆（topK=5）
3. 将记忆注入到对话上下文中
4. 帮助 Echo 做出更好的决策

**无需手动调用 `memory_search`，除非需要特定查询。**

---

## 协作工具

### 与小东协作

- 读取小东的任务清单（如有需要）
- 共享情报中心数据

### 与小冠协作

- 提供意向客户线索
- 获取客户反馈，优化内容方向

---

## 开发计划

### Phase 1：基础功能（当前）
- ✅ 读取飞书情报中心
- ✅ 调用 GoldFinger CLI
- ✅ 配置 Mem0 记忆系统
- ⏳ 公众号文章撰写
- ⏳ 意向客户审核

### Phase 2：自动化排版
- ⏳ 公众号后台浏览器自动化
- ⏳ 图片自动插入
- ⏳ 格式自动调整

### Phase 3：数据分析与学习
- ⏳ 文章阅读量跟踪
- ⏳ 获客转化率分析
- ⏳ 基于 Mem0 的策略优化
- ⏳ 审批偏好学习（自动决策）
