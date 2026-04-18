# Browser 自动化使用指南

**目标**：使用 OpenClaw Browser 工具自动化公众号文章发布流程

---

## 一、架构说明

### OpenClaw Route #3 架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Docker 容器                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  OpenClaw Gateway (openclaw-gateway)                 │  │
│  │  - 运行 Echo Agent                                    │  │
│  │  - 调用 browser 工具                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTP
┌─────────────────────────────────────────────────────────────┐
│                      Mac 主机                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Chrome 浏览器 + OpenClaw Browser Relay 扩展         │  │
│  │  - 接收 Gateway 的指令                                │  │
│  │  - 执行浏览器操作                                     │  │
│  │  - 返回页面快照和结果                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**关键点**：
- Gateway 在 Docker 容器内运行
- Browser 在 Mac 主机上运行
- 通过 HTTP 通信（需要网络可达）

---

## 二、前置条件

### 1. Mac 主机配置

**安装 Chrome 浏览器**：
```bash
# 确认 Chrome 已安装
open -a "Google Chrome"
```

**安装 OpenClaw Browser Relay 扩展**：
1. 打开 Chrome
2. 访问扩展商店或加载本地扩展
3. 启用 OpenClaw Browser Relay 扩展
4. **重要**：用户需要手动点亮扩展图标（激活状态）

### 2. 网络配置

**确认 Gateway 可以访问 Mac 主机**：
```bash
# 在 Docker 容器内测试
curl http://host.docker.internal:PORT

# 或使用 Mac 主机的 IP 地址
curl http://192.168.x.x:PORT
```

### 3. Browser 节点配置

**在 openclaw.json 中配置 Browser 节点**：
```json
{
  "browser": {
    "nodes": [
      {
        "id": "mac-browser-node",
        "host": "host.docker.internal",
        "port": 9222,
        "profile": "chrome"
      }
    ]
  }
}
```

---

## 三、使用方法

### 基础用法

```javascript
// 打开公众号后台
await browser({
  target: "node",
  node: "mac-browser-node",  // 指定 Mac 主机上的 Browser 节点
  profile: "chrome",
  url: "https://mp.weixin.qq.com"
});
```

### 完整流程示例

```javascript
async function publishArticleWithBrowser(article) {
  try {
    // Step 1: 打开公众号后台
    await browser({
      target: "node",
      node: "mac-browser-node",
      profile: "chrome",
      url: "https://mp.weixin.qq.com"
    });

    // Step 2: 等待页面加载，检查登录状态
    // 如果未登录，提示用户扫码
    const isLoggedIn = await checkLoginStatus();
    if (!isLoggedIn) {
      await notifyUser("请在浏览器中扫码登录公众号后台");
      await waitForLogin();
    }

    // Step 3: 点击"新建图文"
    await clickElement('button[text="新建图文"]');

    // Step 4: 等待编辑器加载
    await waitForElement('.editor-container');

    // Step 5: 粘贴文章内容
    await pasteContent(article.html);

    // Step 6: 预览检查
    await clickElement('button[text="预览"]');
    await waitForPreview();

    // Step 7: 保存草稿
    await clickElement('button[text="保存"]');

    return { success: true };
  } catch (error) {
    console.error('Browser 自动化失败:', error);
    return { success: false, error: error.message };
  }
}
```

---

## 四、关键技术点

### 1. 页面快照优化

**问题**：完整页面快照可能很大，影响性能

**解决方案**：使用最小必要范围
```javascript
await browser({
  target: "node",
  node: "mac-browser-node",
  profile: "chrome",
  url: "https://mp.weixin.qq.com",
  snapshot: {
    mode: "minimal",  // 最小快照
    selector: ".editor-container"  // 只捕获编辑器区域
  }
});
```

### 2. 登录状态检测

**方法 A：检查特定元素**
```javascript
// 检查是否存在"新建图文"按钮
const isLoggedIn = await elementExists('button[text="新建图文"]');
```

**方法 B：检查 Cookie**
```javascript
// 检查是否存在登录 Cookie
const cookies = await getCookies();
const hasAuthCookie = cookies.some(c => c.name === 'auth_token');
```

### 3. 异常重试策略

```javascript
async function retryOperation(operation, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await sleep(1000 * (i + 1));  // 指数退避
    }
  }
}
```

### 4. 内容粘贴技巧

**方法 A：使用 JavaScript 注入**
```javascript
await executeScript(`
  const editor = document.querySelector('.editor-container');
  editor.innerHTML = ${JSON.stringify(article.html)};
`);
```

**方法 B：模拟粘贴操作**
```javascript
await focusElement('.editor-container');
await pasteFromClipboard(article.html);
```

---

## 五、常见问题

### Q1：Browser 工具无法连接

**可能原因**：
- OpenClaw Browser Relay 扩展未启用
- 网络不可达（Docker 无法访问 Mac 主机）
- 端口配置错误

**解决方案**：
1. 确认扩展已启用（图标点亮）
2. 测试网络连接：`curl http://host.docker.internal:9222`
3. 检查 openclaw.json 中的端口配置

### Q2：登录状态失效

**可能原因**：
- Cookie 过期
- 公众号后台强制重新登录

**解决方案**：
1. 提示用户重新扫码登录
2. 使用持久化 Cookie（如果支持）
3. 降级到手动发布流程

### Q3：页面改版导致脚本失效

**可能原因**：
- 公众号后台页面结构变化
- 元素选择器失效

**解决方案**：
1. 定期测试脚本
2. 使用更稳定的选择器（如 data-* 属性）
3. 及时更新脚本
4. 降级到手动发布流程

### Q4：内容粘贴后格式错乱

**可能原因**：
- HTML 格式不兼容
- 编辑器过滤了某些标签

**解决方案**：
1. 使用公众号兼容的 HTML 格式
2. 测试不同的粘贴方法
3. 降级到手动发布流程

---

## 六、降级方案

当 Browser 自动化失败时，自动切换到手动发布流程：

```javascript
async function publishArticle(article) {
  // 尝试 Browser 自动化
  const result = await publishArticleWithBrowser(article);

  if (!result.success) {
    // 降级到手动发布
    console.log('Browser 自动化失败，切换到手动发布流程');

    // 保存文章文件
    await saveFile(`articles/${article.id}.md`, article.markdown);
    await saveFile(`articles/${article.id}.html`, article.html);

    // 通知用户
    await notifyUser(`
文章《${article.title}》已准备好，请手动发布。

文件位置：
- Markdown: articles/${article.id}.md
- HTML: articles/${article.id}.html

发布指南：docs/publish-guide.md
    `);

    return { success: true, method: 'manual' };
  }

  return { success: true, method: 'automated' };
}
```

---

## 七、最佳实践

### 1. 先手动操作一遍

在编写自动化脚本前：
1. 手动完成一次完整的发布流程
2. 记录每个步骤的操作
3. 识别关键元素和选择器
4. 确定可能的异常情况

### 2. 使用稳定的选择器

**优先级**：
1. `data-*` 属性（最稳定）
2. `id` 属性
3. `class` 属性（可能变化）
4. 文本内容（最不稳定）

### 3. 添加充足的等待时间

```javascript
// 等待元素出现
await waitForElement('.editor-container', { timeout: 10000 });

// 等待页面加载
await sleep(2000);

// 等待网络请求完成
await waitForNetworkIdle();
```

### 4. 记录详细日志

```javascript
console.log('[Browser] 打开公众号后台');
console.log('[Browser] 检查登录状态');
console.log('[Browser] 点击新建图文');
console.log('[Browser] 粘贴文章内容');
console.log('[Browser] 保存草稿');
```

### 5. 定期测试和维护

- 每周测试一次自动化脚本
- 公众号后台更新后立即测试
- 及时更新选择器和逻辑
- 保持降级方案可用

---

## 八、参考资料

- **OpenClaw Browser 文档**：查看 OpenClaw 官方文档
- **GoldFinger Playwright 脚本**：`/Users/xiaojiujiu2/Documents/coding/GoldFinger/`
- **小东 Browser 操作文档**：`/Users/xiaojiujiu2/Documents/openclaw-docker/docs/xiaodong-browser-ops.md`

---

**文档版本**：v1.0
**最后更新**：2026-03-13
**维护人**：Echo（艾可）
