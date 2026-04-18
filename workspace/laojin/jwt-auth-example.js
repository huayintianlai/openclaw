/**
 * JWT Authentication Middleware - Usage Example
 */

const express = require('express');
const jwt = require('jsonwebtoken');
const jwtAuth = require('./jwt-auth-middleware');

const app = express();
app.use(express.json());

// ============================================
// 1. 登录接口 - 生成 JWT token
// ============================================
app.post('/api/login', (req, res) => {
  const { username, password } = req.body;
  
  // 这里应该验证用户名密码（示例简化）
  if (username === 'admin' && password === 'password') {
    // 生成 token，包含用户信息
    const token = jwt.sign(
      { 
        userId: 1, 
        username: 'admin',
        role: 'admin'
      },
      process.env.JWT_SECRET,
      { expiresIn: '24h' } // token 有效期
    );
    
    return res.json({
      success: true,
      token,
      expiresIn: '24h'
    });
  }
  
  res.status(401).json({
    error: 'Unauthorized',
    message: 'Invalid credentials'
  });
});

// ============================================
// 2. 公开接口 - 无需认证
// ============================================
app.get('/api/public', (req, res) => {
  res.json({
    message: 'This is a public endpoint'
  });
});

// ============================================
// 3. 受保护接口 - 需要 JWT 认证
// ============================================
app.get('/api/protected', jwtAuth, (req, res) => {
  // req.user 包含解码后的 token 信息
  res.json({
    message: 'This is a protected endpoint',
    user: req.user
  });
});

// ============================================
// 4. 批量保护多个路由
// ============================================
app.use('/api/admin', jwtAuth); // 所有 /api/admin/* 路由都需要认证

app.get('/api/admin/users', (req, res) => {
  res.json({
    users: [
      { id: 1, username: 'admin' },
      { id: 2, username: 'user1' }
    ]
  });
});

app.get('/api/admin/settings', (req, res) => {
  res.json({
    settings: { theme: 'dark', language: 'zh-CN' }
  });
});

// ============================================
// 5. 角色权限控制（可选扩展）
// ============================================
function requireRole(role) {
  return (req, res, next) => {
    if (req.user && req.user.role === role) {
      return next();
    }
    res.status(403).json({
      error: 'Forbidden',
      message: 'Insufficient permissions'
    });
  };
}

app.delete('/api/admin/users/:id', jwtAuth, requireRole('admin'), (req, res) => {
  res.json({
    message: `User ${req.params.id} deleted`,
    deletedBy: req.user.username
  });
});

// ============================================
// 启动服务器
// ============================================
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`JWT_SECRET: ${process.env.JWT_SECRET ? '✓ Set' : '✗ Not set'}`);
});
