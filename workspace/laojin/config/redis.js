const Redis = require('ioredis');

/**
 * Redis 连接配置
 * 使用 ioredis 库提供企业级 Redis 连接管理
 */

// 从环境变量读取配置
const config = {
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379', 10),
  password: process.env.REDIS_PASSWORD || undefined,
  db: parseInt(process.env.REDIS_DB || '0', 10),
  
  // 连接池配置
  maxRetriesPerRequest: 3,
  enableReadyCheck: true,
  enableOfflineQueue: true,
  
  // 重连策略
  retryStrategy(times) {
    const delay = Math.min(times * 50, 2000);
    return delay;
  },
  
  // 连接超时
  connectTimeout: 10000,
  
  // 保持连接
  keepAlive: 30000,
  
  // 自动重连
  autoResubscribe: true,
  autoResendUnfulfilledCommands: true,
};

// 创建 Redis 客户端实例
const redis = new Redis(config);

// 错误处理
redis.on('error', (err) => {
  console.error('Redis 连接错误:', err);
});

redis.on('connect', () => {
  console.log('Redis 连接成功');
});

redis.on('ready', () => {
  console.log('Redis 准备就绪');
});

redis.on('close', () => {
  console.log('Redis 连接关闭');
});

redis.on('reconnecting', () => {
  console.log('Redis 正在重连...');
});

module.exports = redis;
