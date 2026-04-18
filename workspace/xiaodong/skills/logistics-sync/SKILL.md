# logistics-sync — 物流单号同步技能

## 触发条件

用户把1688的物流提醒（截图文字、转述、随口说）发过来，消息中同时包含以下两个信息时，立即执行本技能：

1. **阿里巴巴/1688订单号**：19位纯数字（如 `5104561176685404919`）
2. **运单号**：10～20位数字（如 `78991898172678`）

**任意格式均可触发，无需特定语法：**
- `订单5104561176685404919的运单号：78991898172678，同步。`
- `5104561176685404919 出物流了，单号78991898172678`
- `帮我把5104561176685404919的快递78991898172678填进去`
- `顺丰78991898172678，1688单5104561176685404919`
- 直接转发1688通知原文（含上述两个数字即可）

**背景：**
用户经营情侣恋爱时光小程序（记忆册打印服务）。用户下单后，通过1688采购打印，约3天后1688出物流。运单号需同步到内部系统，将订单状态从「未发货」改为「已发货」。

---

## 执行流程

### 第一步：从飞书表格查询商户订单号

- spreadsheet_token：`shtcnkNJV83oZqDGUqdCi83tKkh`
- sheet_id：`7e18c8`
- **表格结构：A列 = 商户订单号，C列 = 阿里巴巴订单号**
- ⚠️ 商户订单号是内部转换过的编号（如 `J326081039011066`），不是阿里原始格式

用 `feishu_bitable_app_table_record` 或直接调飞书 Sheets API 读取 A1:D500，在 C 列找匹配的阿里巴巴订单号，取同行 A 列的值作为商户订单号。

如果飞书 API 无权限，改用浏览器打开表格手动查找（fallback）。

---

### 第二步：浏览器自动化操作内部系统

使用 `browser` tool，`target=host`，`profile=openclaw`。
如果 targetId 已存在（上次会话残留），直接复用，无需重新登录。

#### 2.1 登录（如未登录）

```
打开：http://love.99uwen.com:3667/admin/#/login
找 placeholder=请填写用户名 的 input，type 填入：张建东
找 placeholder=请填写用户登录密码 的 input，type 填入：123456
点击登录按钮
snapshot 确认出现「退出登录」链接，说明登录成功
```

#### 2.2 导航到物流列表并搜索订单

```
导航到：http://love.99uwen.com:3667/admin/#/logistics/list
等待 2 秒让页面加载完成
```

**搜索关键代码（经过实测验证，唯一可靠方式）：**

```javascript
// 1. 定位第三个 input（index=2，placeholder=请输入订单编号）
const input = document.querySelectorAll('input')[2];

// 2. 通过 Vue 实例设置 params.order_no（响应式绑定）
let el = input;
while (el && !el.__vue__) el = el.parentElement;
let p = el && el.__vue__;
while (p) {
  if (p.$data && p.$data.params && 'order_no' in p.$data.params) {
    p.$data.params.order_no = '{商户订单号}';
    break;
  }
  p = p.$parent;
}

// 3. 同步 DOM 值
const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
setter.call(input, '{商户订单号}');
input.dispatchEvent(new Event('input', { bubbles: true }));
input.dispatchEvent(new Event('change', { bubbles: true }));

// 4. 调用表单组件的 onSubmit（只有 params，没有 onTapEdit 的那个）
el = input;
while (el && !el.__vue__) el = el.parentElement;
p = el && el.__vue__;
while (p) {
  const own = Object.keys(p.$options && p.$options.methods || {});
  const data = Object.keys(p.$data || {});
  // 表单组件特征：有 onSubmit，无 onTapEdit，有 params
  if (own.includes('onSubmit') && !own.includes('onTapEdit') && data.includes('params')) {
    p.onSubmit();
    break;
  }
  p = p.$parent;
}
```

**⚠️ 搜索后等待 2 秒，再验证结果（用 evaluate 读取行数）：**

```javascript
const rows = document.querySelectorAll('table tbody tr');
const pages = document.querySelectorAll('.el-pager li');
return { rowCount: rows.length, pageCount: pages.length };
```

- `rowCount === 1` 且 `pageCount === 1`：搜索成功，继续
- `rowCount > 1` 或 `pageCount > 1`：搜索未生效（服务器可能 502），**重试最多 3 次**，每次间隔 3 秒
- `rowCount === 0`：订单号有误，终止并告知用户

#### 2.3 点击编辑按钮

```
snapshot 后找到结果行中的编辑按钮（button "编辑"），点击
```

#### 2.4 填写物流信息

等待编辑页加载（URL 变为 `#/logistics/edit?id=xxx`），然后：

```javascript
const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
const inputs = document.querySelectorAll('input');
let statusInput, logisticsInput;
for (let i of inputs) {
  // 订单状态：值为 paid（或其他非 shipped 状态）
  if (i.value && i.value !== '' && i.placeholder === '') statusInput = i;
  // 物流单号：placeholder 为「请输入渠道名称」
  if (i.placeholder === '请输入渠道名称') logisticsInput = i;
}
// 改状态
setter.call(statusInput, 'shipped');
statusInput.dispatchEvent(new Event('input', { bubbles: true }));
statusInput.dispatchEvent(new Event('change', { bubbles: true }));
// 填运单号
setter.call(logisticsInput, '{运单号}');
logisticsInput.dispatchEvent(new Event('input', { bubbles: true }));
logisticsInput.dispatchEvent(new Event('change', { bubbles: true }));
// 返回确认
return { status: statusInput.value, logistics: logisticsInput.value };
```

确认返回 `{ status: 'shipped', logistics: '{运单号}' }` 后继续。

#### 2.5 提交

```
点击「提交修改」按钮
等待 2 秒
snapshot 确认：
  - 页面跳回列表页，或
  - 列表中该订单状态变为「已发货」
```

---

## 完成后回复用户

```
✅ 订单 {阿里巴巴订单号} 同步完成
- 商户订单号：{商户订单号}
- 运单号：{运单号}
- 状态：已发货
```

---

## 重试策略

- 服务器 502/9999 是系统偶发问题，不是操作错误
- 搜索步骤：最多重试 3 次，间隔 3 秒
- 登录 token 过期时：重新走登录流程
- 超过重试次数仍失败：告知用户「系统当前不可用，请稍后再试」

---

## 已知问题

- PUT `/cms/shopOrderList/order` 后端持续 9999 错误，**不要用 API**，只用浏览器操作
- 搜索接口 POST `/cms/shopOrderList/search` 偶发 502，加重试解决
- 浏览器使用 openclaw profile（不依赖用户 Chrome，无需用户在场）
