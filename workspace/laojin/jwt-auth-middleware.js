/**
 * JWT Authentication Middleware for Express
 * 
 * Usage:
 *   const jwtAuth = require('./jwt-auth-middleware');
 *   app.use('/api/protected', jwtAuth);
 */

const jwt = require('jsonwebtoken');

/**
 * JWT 验证中间件
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next middleware function
 */
function jwtAuthMiddleware(req, res, next) {
  // 从 Authorization header 获取 token
  const authHeader = req.headers.authorization;
  
  if (!authHeader) {
    return res.status(401).json({
      error: 'Unauthorized',
      message: 'No authorization header provided'
    });
  }

  // 验证格式: "Bearer <token>"
  const parts = authHeader.split(' ');
  if (parts.length !== 2 || parts[0] !== 'Bearer') {
    return res.status(401).json({
      error: 'Unauthorized',
      message: 'Invalid authorization header format. Expected: Bearer <token>'
    });
  }

  const token = parts[1];

  try {
    // 验证 token（需要设置环境变量 JWT_SECRET）
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    
    // 将解码后的用户信息附加到 req 对象
    req.user = decoded;
    
    next();
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({
        error: 'Unauthorized',
        message: 'Token has expired'
      });
    }
    
    if (error.name === 'JsonWebTokenError') {
      return res.status(401).json({
        error: 'Unauthorized',
        message: 'Invalid token'
      });
    }
    
    // 其他错误
    return res.status(500).json({
      error: 'Internal Server Error',
      message: 'Token verification failed'
    });
  }
}

module.exports = jwtAuthMiddleware;
