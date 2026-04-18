---
name: tavily-usage-check
description: 查询 Tavily 控制台余额、配额与 usage 的专用技能。用户提到 Tavily余额、Tavily用量、Tavily配额、Tavily usage、Tavily剩余额度时必须使用。固定执行约束：优先用 browser(profile=chrome-relay,target=host) 接管用户当前 Chrome 标签页；仅当用户明确要求接管其已登录浏览器整体会话，或当前 attach 标签页不足以完成任务且用户人在电脑前可批准连接时，才改用 profile=user。优先复用已登录状态，若 Tavily 未登录则允许在页面中手动走 Google 登录并优先选择 huayintianlai@gmail.com；禁止猜测 API 或伪造余额；若未 attach Chrome tab，直接提示用户点击 OpenClaw Browser Relay。
---

# Tavily Usage Check Skill

按以下流程执行，不得跳步。

## 0) 目标

读取 Tavily 控制台中与额度/用量相关的可见字段，并结构化汇报给 Kent。
本技能只读，不执行充值、升级套餐、修改账户设置等写操作。

## 1) 触发条件

当用户提到以下意图时，优先使用本技能：

- Tavily 余额
- Tavily 用量
- Tavily usage
- Tavily 配额
- Tavily 剩余
- Tavily 还剩多少

## 2) 前置条件

1. 默认必须使用 `browser(profile="chrome-relay", target="host")`。
2. 仅当用户明确要求接管其已登录浏览器整体会话，或当前 attach 标签页不足以完成任务且用户人在电脑前可点击/批准连接提示时，才允许改用 `browser(profile="user", target="host")`。
3. 优先依赖用户已登录的 Tavily 控制台页面。
4. 若 Tavily 未登录，但当前 Chrome 已 attach，允许在页面中手动执行 Google 登录。
5. Google 登录时，优先选择账号 `huayintianlai@gmail.com`。
6. 若没有已 attach 的 Chrome 标签页，直接返回：

`前置条件不满足：请在已打开的 Tavily 页面点击 OpenClaw Browser Relay 后再让我读取。`

7. 禁止要求用户提供密码或 API key。
8. 禁止猜测 Tavily 的隐藏接口或余额数值。

## 3) 页面接管流程

1. 使用 `browser` 获取当前 Chrome tabs；默认按 `profile="chrome-relay"` 处理当前 attach 的标签页。
2. 优先定位 Tavily 控制台相关标签页。
3. 若未定位到目标标签页，但已有 attach tab，可让用户切到 Tavily 页面后重试。
4. 对目标 tab 做 `snapshot(refs="aria")`。
5. 若页面显示登录入口或 Google 登录按钮，允许继续执行登录流程。
6. 若出现 Google 账号选择页，优先选择 `huayintianlai@gmail.com`；若该账号不可见，不猜测其他账号。
7. 登录成功后重新 `snapshot(refs="aria")`，再识别页面中与 billing / usage / credits / quota 相关的区域。
8. 若用户明确要求接管整个已登录浏览器会话，或当前 attach 标签页不足以完成任务且用户可批准连接，再切换为 `profile="user"`；不要再使用旧写法 `profile="chrome"`。

## 4) 字段读取目标

尽量读取以下字段；若页面没有某项，就明确标注缺失，不得猜测：

- 当前套餐 / Plan
- 账期 / Billing period
- 已使用 / Used
- 剩余 / Remaining
- 总额度 / Limit 或 Credits
- 重置时间 / Reset date
- 其他可见的 usage 指标

提取原则：

- 优先读取页面可见原文。
- 数值保留原始单位。
- 若页面同时出现多个 usage 区块，优先读取最像总览/账单的模块。
- 若字段语义不确定，明确写“字段含义待确认”。

## 5) 异常处理

### 未登录

若页面显示登录入口、登录按钮或要求认证：

1. 先尝试在当前页面执行 Google 登录。
2. 优先选择账号 `huayintianlai@gmail.com`。
3. 登录成功后，重新定位 usage / billing / credits 区域。
4. 若登录失败、账号不可选或流程中断，再返回：

`失败（原因: Tavily 控制台未登录，且未能完成 Google 登录）`

### 未 attach

若 Chrome Relay 未连接，返回：

`失败（原因: 未连接到已登录的 Chrome 标签页）`

### 页面结构变化

若找不到 usage / billing / credits 相关字段，返回：

`失败（原因: 页面结构变化，未定位到 Tavily 用量字段）`

### 读取不完整

若只读到部分字段，返回：

`部分成功（缺失: ...）`

## 6) 固定输出模板

默认按以下结构输出：

- `状态：成功 / 部分成功 / 失败`
- `套餐：...`
- `账期：...`
- `已使用：...`
- `剩余：...`
- `总额度：...`
- `重置时间：...`
- `备注：...`

要求：

- 用结构化短块，不写成长段。
- 若信息不全，明确指出缺失项。
- 若成功，优先给一句判断，例如“当前额度充足”或“余额接近阈值”。

## 7) 默认回复风格

若用户只是随口问“还能用多少”，先给结果，再补字段。
若用户明确要求详细版，再输出完整结构。

## 8) 安全边界

- 不做任何账户写操作。
- 不泄露页面上可能出现的敏感 token。
- 不把页面里不可见的值当作事实。
- 不把估算值写成正式余额。
- 允许执行 Google 登录，仅用于进入 Tavily 控制台读取用量信息。
- 除 `huayintianlai@gmail.com` 外，不主动猜测或切换其他 Google 账号。

## 9) 后续演进建议

如果未来 Tavily 官方开放稳定的 usage API，可新增 API 模式；但在未验证前，默认坚持浏览器只读模式。
