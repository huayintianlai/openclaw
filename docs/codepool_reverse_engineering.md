# CodePool 插件逆向分析 —— 实现原理

> 分析版本：codepool-1.0.37.vsix（发布者 keg1255）
> 分析时间：2026-03-12
> 目的：技术研究，后续自行开发类似插件的参考

---

## 一、插件概览

| 项目 | 说明 |
|------|------|
| 名称 | AI号池（codepool） |
| 功能 | 一键切换 Windsurf / Augment 账号，绕过 free user account exceeded 限制 |
| 入口 | VS Code 扩展，`onStartupFinished` 激活 |
| 核心文件 | `dist/extension.js`（混淆），`dist/mcp-server.js`，`webview/pool.html` |
| 代码保护 | `javascript-obfuscator` + `webpack-obfuscator` 双重混淆 |
| 依赖 | axios（HTTP）、bson（序列化）、fs-extra（文件操作） |

---

## 二、核心机制

### 2.1 Patch Windsurf 内置 extension.js（关键）

插件启动时，定位并修改 Windsurf 安装目录下的内置扩展文件：

```
路径: {vscode.env.appRoot}/extensions/windsurf/dist/extension.js
```

**修改手法**：用正则匹配 Windsurf 源码中的登录认证逻辑：

```js
// 原始正则匹配模式
/\.LOGIN_WITH_AUTH_TOKEN,(\()?\(\)=>\{(\w+)\.provideAuthToken/

// 替换为
'.LOGIN_WITH_AUTH_TOKEN,$1(acc)=>{acc?$2.handleAuthToken(acc):$2.provideAuthToken'
```

**效果**：劫持 `LOGIN_WITH_AUTH_TOKEN` 事件处理函数，使其能接受外部注入的 `access_token`，而不是只走 Windsurf 官方的 OAuth 认证流程。

**如果无需修改**（已被 patch 过），日志输出：
```
'No modification needed for windsurf extension'
```

### 2.2 对 Augment 的类似处理

对 Augment 插件采用类似策略：

```
路径: {augment扩展目录}/dist/extension.js
```

- 匹配 `registerUriHandler` 和 `authRedirectURI.path` 相关代码
- 通过 `vscode-augment.directLogin` 命令注入凭证

### 2.3 设备码刷新（changeDeviceId）

Windsurf 用设备指纹（machineId）限制免费账号使用次数。插件暴露了 `changeDeviceId` 方法来重置/伪造设备标识，绕过"free user account exceeded"。

---

## 三、业务流程

```
用户输入激活码
    │
    ▼
POST /api/users/card-login { card: 激活码 }
    │
    ▼
后端返回用户信息 + access_token
    │
    ▼
插件调用 vscode.commands.executeCommand(
    'windsurf.loginWithAuthToken', access_token
)
    │
    ▼
Windsurf 被 patch 后的 extension.js 接受 token → 登录成功
```

### 号池管理 WebView

- 登录/退出、查看积分、VIP 过期时间
- 获取新账号（从池子中分配）
- 切换到指定账号
- 刷新设备码
- 公告系统（`/api/notice`）

---

## 四、关键 API 端点（后端）

| 端点 | 用途 |
|------|------|
| `/api/users/card-login` | 激活码登录 |
| `/api/users/whoami` | 获取当前用户信息 |
| `/api/account/switch` | 切换/获取新账号（推测） |
| `/api/device/refresh` | 刷新设备码（推测） |
| `/api/notice` | 获取公告内容 |

> 注：后端 baseURL 在混淆代码中，未完全解出。

---

## 五、关键 VS Code / Windsurf 命令

| 命令 | 说明 |
|------|------|
| `windsurf.loginWithAuthToken` | Windsurf 内置命令，用 token 登录 |
| `vscode-augment.directLogin` | Augment 内置命令，直接登录 |
| `codepool.openPoolPage` | 打开号池管理 WebView |
| `codepool.showLogs` | 显示日志面板 |
| `codepool.changeWindsurf` | Windsurf 登录 |
| `codepool.changeAugment` | Augment 登录 |

---

## 六、安全风险

| 风险等级 | 风险点 | 说明 |
|----------|--------|------|
| 🔴 高 | 修改 IDE 源码 | 直接 patch Windsurf 安装目录中的 JS 文件 |
| 🔴 高 | 共享账号 | 使用池子里的第三方账号，非用户自有 |
| 🟡 中 | 代码双重混淆 | 刻意隐藏实现细节 |
| 🟡 中 | 远端可控 | 后端完全控制分配的账号和 token |
| 🟡 中 | 违反 ToS | 修改内部文件 + 账号共享违反 Windsurf 服务条款 |

---

## 七、自研插件技术方向（参考）

如果要自己实现一个**用自有 API Key 驱动 Windsurf** 的插件，可参考以下路线：

### 路线 A：Token 注入（CodePool 的方式）

1. **Patch Windsurf extension.js**，劫持 `LOGIN_WITH_AUTH_TOKEN` 流程
2. **用自己的 Windsurf 账号 token** 注入（而非共享号池）
3. 局限：仍然走 Windsurf 的积分体系，只是自动化了登录切换

### 路线 B：请求拦截代理（更彻底）

1. **拦截 Windsurf → Codeium 后端的请求**（通过 HTTP Proxy 设置）
2. **将请求转发到自己的 OpenAI/Anthropic API**
3. **需要做协议转换**：Codeium 私有协议 ↔ OpenAI Chat Completions API
4. 难点：Codeium 用的是 gRPC/protobuf（非标准 REST），协议逆向成本高

### 路线 C：替换 Cascade 面板（最灵活）

1. **不碰 Windsurf 内置 Cascade**
2. **自建 WebView 面板**，UI 模仿 Cascade 体验
3. **直接调用 OpenAI/Anthropic API**
4. **通过 VS Code API 操作编辑器**（读写文件、执行命令等）
5. 优点：完全独立，不受 Windsurf 版本更新影响
6. 缺点：需要自己实现 Agent 能力（工具调用、上下文管理等）

### 路线 D：利用 BYOK（官方支持，最安全）

1. Windsurf 已官方支持 **Bring Your Own Key**
2. 目前仅限 **Claude 4 系列**（Sonnet / Opus）
3. 配置入口：https://windsurf.com/subscription/provider-api-keys
4. **不支持 OpenAI GPT 系列**（截至 2026-03）

---

## 八、文件结构参考

```
codepool-1.0.37.vsix (解压后)
├── [Content_Types].xml
├── extension.vsixmanifest
└── extension/
    ├── package.json          # 插件清单
    ├── README.md             # 使用说明
    ├── CHANGELOG.md
    ├── LICENSE.md
    ├── dist/
    │   ├── extension.js      # 核心逻辑（混淆，628KB）
    │   └── mcp-server.js     # MCP 服务端（Zod schema，v1.0.37 新增）
    ├── resources/
    │   ├── icon.png
    │   ├── darg.png
    │   ├── device.png
    │   └── switch.png
    └── webview/
        └── pool.html         # 号池管理界面（906行）
```

---

## 九、待研究项

- [ ] Codeium gRPC 协议逆向（路线 B 的前置条件）
- [ ] Windsurf `loginWithAuthToken` 命令的完整参数签名
- [ ] Windsurf 设备指纹生成机制（machineId 来源）
- [ ] VS Code Extension API 中可用于构建 Agent 面板的能力边界
- [ ] BYOK 是否会扩展到 OpenAI GPT 系列
