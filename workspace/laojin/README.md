# JWT Authentication Middleware

Express 中间件，用于验证 JWT token。

## 安装依赖

```bash
npm install express jsonwebtoken dotenv
```

## 快速开始

1. **复制环境变量配置**
```bash
cp .env.example .env
```

2. **生成安全的 JWT_SECRET**
```bash
node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"
```
将生成的密钥替换 `.env` 中的 `JWT_SECRET`

3. **启动服务器**
```bash
node jwt-auth-example.js
```

## API 测试

### 1. 登录获取 token
```bash
curl -X POST http://localhost:3000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

响应示例：
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": "24h"
}
```

### 2. 访问公开接口（无需认证）
```bash
curl http://localhost:3000/api/public
```

### 3. 访问受保护接口（需要认证）
```bash
# 将 YOUR_TOKEN 替换为登录返回的 token
curl http://localhost:3000/api/protected \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. 访问管理员接口（需要认证 + 角色权限）
```bash
curl http://localhost:3000/api/admin/users \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 文件说明

- `jwt-auth-middleware.js` - JWT 验证中间件核心逻辑
- `jwt-auth-example.js` - 完整使用示例
- `.env.example` - 环境变量配置模板

## 中间件特性

✅ 标准 Bearer token 格式验证  
✅ Token 过期检测  
✅ 详细的错误信息  
✅ 用户信息自动注入 `req.user`  
✅ 支持角色权限控制（可选）  

## 错误处理

| 错误类型 | HTTP 状态码 | 说明 |
|---------|-----------|------|
| 缺少 Authorization header | 401 | 未提供认证信息 |
| 格式错误 | 401 | 不是 "Bearer <token>" 格式 |
| Token 过期 | 401 | Token 已过期 |
| Token 无效 | 401 | Token 签名验证失败 |
| 权限不足 | 403 | 角色权限不匹配 |

## 生产环境建议

1. **使用强随机密钥**：至少 256 位
2. **HTTPS only**：生产环境必须使用 HTTPS
3. **Token 刷新机制**：实现 refresh token 避免频繁登录
4. **速率限制**：防止暴力破解
5. **日志记录**：记录认证失败事件

## 扩展功能

如需添加更多功能（如 token 刷新、黑名单、多设备管理），请告诉我具体需求。
