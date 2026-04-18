---
name: trendradar-news-assistant
---

# TrendRadar 资讯助手技能

## 描述
基于 TrendRadar 热点监控系统的资讯助手技能。当用户提到热点监控、资讯聚合、行业动态、AI趋势时激活。

TrendRadar 是一个 AI 驱动的多平台热点舆情监控与分析工具，聚合抖音、知乎、B站、华尔街见闻、财联社等 35+ 平台的热门资讯，支持智能筛选、自动推送和 AI 对话分析。

## 核心功能
1. **热点监控** - 监控 AI、自动化、OpenClaw 等相关关键词
2. **趋势分析** - AI 分析热点趋势、情感、影响力
3. **智能推送** - 通过飞书等渠道推送重要资讯
4. **MCP 集成** - 通过 MCP 协议与 AI 客户端深度交互

## 工具依赖
- `exec` - 运行 Docker 命令和脚本
- `browser` - 访问 TrendRadar Web 界面
- `feishu_update_doc` - 推送资讯到飞书文档
- `feishu_wiki_space_node` - 创建资讯归档节点
- `tavily_search` - 补充搜索最新信息

## 快速开始

### 1. 部署 TrendRadar
```bash
# 克隆仓库
git clone https://github.com/sansan0/TrendRadar.git
cd TrendRadar

# Docker 部署（推荐）
docker-compose up -d

# 或本地部署
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 基础配置
编辑 `config/config.yaml`：
```yaml
# 推送配置
push:
  feishu:
    enabled: true
    webhook: "你的飞书机器人webhook"
    
# AI 分析配置  
ai:
  enabled: true
  api_key: "你的AI API密钥"
  model: "deepseek-chat"  # 或 gpt-4, gemini-pro 等
  
# 调度配置
schedule:
  preset: "morning_evening"  # 早晚推送
```

### 3. 关键词配置
编辑 `frequency_words.txt`：
```
# AI 与自动化相关
AI 人工智能 大模型
+发布 +突破

OpenClaw 自动化 Agent
+开源 +更新

RPA 流程自动化
+企业 +应用

# 排除干扰
!娱乐 !明星 !八卦
```

## 使用场景

### 场景1：部署 TrendRadar 服务
当用户说"部署 TrendRadar"或"设置热点监控"时：
1. 检查 Docker 环境
2. 拉取 TrendRadar 镜像
3. 创建基础配置文件
4. 启动服务并验证

### 场景2：配置监控关键词  
当用户说"监控AI动态"或"关注自动化趋势"时：
1. 读取当前关键词配置
2. 建议添加相关关键词
3. 更新配置文件
4. 重启服务应用配置

### 场景3：查看今日热点
当用户说"今天有什么热点"或"AI行业动态"时：
1. 调用 TrendRadar MCP 接口查询最新数据
2. 按关键词过滤和排序
3. 生成结构化摘要
4. 推送或显示结果

### 场景4：定期资讯推送
当用户说"设置每日简报"时：
1. 配置定时任务（cron 或 GitHub Actions）
2. 设置推送时间（如 8:30, 18:00）
3. 定义推送格式和内容深度
4. 测试推送流程

## MCP 集成指南

TrendRadar 支持 MCP 协议，可通过以下方式集成：

### 1. 启动 MCP 服务器
```bash
cd TrendRadar/mcp_server
python server.py
```

### 2. 可用工具
- `search_news` - 按关键词搜索新闻
- `get_trending_topics` - 获取趋势话题
- `analyze_sentiment` - 情感分析
- `summarize_news` - 新闻摘要

### 3. 示例查询
```python
# 搜索 AI 相关新闻
search_news(keywords="AI 人工智能", days=1, limit=10)

# 获取今日趋势
get_trending_topics(platform="all", limit=5)

# AI 分析热点
analyze_sentiment(topic="大模型发布", depth="deep")
```

## 飞书集成配置

### 1. 创建飞书机器人
1. 打开飞书开放平台
2. 创建自定义机器人
3. 获取 webhook URL
4. 添加到 TrendRadar 配置

### 2. 推送格式定制
```yaml
# config.yaml
push:
  feishu:
    format: "rich"  # rich/markdown/text
    include_images: true
    max_items: 10
```

### 3. 归档到知识库
重要资讯自动归档到飞书知识库：
- `01.1_专属认知库/01.1.1_AI资讯/` - AI 相关动态
- `01.1_专属认知库/01.1.2_行业趋势/` - 行业分析
- `01.1_专属认知库/01.1.3_技术突破/` - 技术更新

## 进阶功能

### 1. 多源聚合
- 热榜平台：知乎、抖音、B站、微博等
- RSS 订阅：技术博客、行业媒体
- 自定义源：特定网站监控

### 2. 智能分析
- 趋势预测：基于历史数据预测热点走向
- 情感分析：舆论正负面情绪识别
- 关联分析：发现话题间的隐藏关联

### 3. 预警系统
- 突发热点：实时检测新出现的热点
- 负面舆情：监控品牌或产品负面信息
- 机会发现：识别潜在的投资或内容机会

## 故障排除

### 常见问题
1. **Docker 启动失败**
   - 检查端口冲突（默认 8000）
   - 验证网络连接
   - 查看日志：`docker logs trendradar`

2. **推送失败**
   - 验证 webhook URL
   - 检查飞书机器人权限
   - 查看推送日志

3. **数据抓取异常**
   - 检查网络代理设置
   - 验证平台访问权限
   - 调整抓取频率避免封禁

### 日志查看
```bash
# Docker 日志
docker logs -f trendradar

# 应用日志
tail -f output/trendradar.log

# MCP 服务器日志
tail -f mcp_server/server.log
```

## 性能优化

### 1. 资源限制
```yaml
# Docker 资源限制
services:
  trendradar:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```

### 2. 缓存策略
- 热点数据缓存 1 小时
- 分析结果缓存 6 小时
- 定期清理旧数据

### 3. 异步处理
- 使用消息队列处理大量数据
- 异步推送避免阻塞
- 分批处理提升效率

## 安全注意事项

### 1. API 密钥保护
- 使用环境变量存储敏感信息
- 定期轮换 API 密钥
- 限制密钥权限范围

### 2. 数据隐私
- 不存储个人身份信息
- 匿名化处理用户数据
- 遵守数据保护法规

### 3. 访问控制
- 限制服务访问 IP
- 启用身份验证
- 定期审计访问日志

## 更新维护

### 1. 版本升级
```bash
# 拉取最新代码
git pull origin master

# 重建 Docker 镜像
docker-compose build --no-cache

# 重启服务
docker-compose up -d
```

### 2. 数据备份
```bash
# 备份数据库
docker exec trendradar sqlite3 data.db .dump > backup.sql

# 备份配置文件
tar czf config_backup.tar.gz config/
```

### 3. 监控告警
- 设置服务健康检查
- 监控资源使用情况
- 配置异常告警通知

---

**技能维护者**：老金 (Laojin)  
**最后更新**：2026-03-11  
**相关链接**：[TrendRadar GitHub](https://github.com/sansan0/TrendRadar)  
**技能状态**：🟢 活跃维护
