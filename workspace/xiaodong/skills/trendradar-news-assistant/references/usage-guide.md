# TrendRadar 资讯助手使用指南

## 🎯 快速开始

### 1. 一键部署
```bash
# 运行部署脚本
bash /Users/xiaojiujiu2/.openclaw/workspace/xiaodong/skills/trendradar-news-assistant/scripts/deploy.sh
```

### 2. 基础配置
部署完成后，编辑以下文件：

**config/config.yaml** - 主要配置
```yaml
# 飞书推送配置
push:
  feishu:
    enabled: true
    webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
    
# AI 分析配置
ai:
  enabled: true
  api_key: "sk-xxx"
  model: "deepseek-chat"
  
# 调度配置
schedule:
  preset: "morning_evening"  # 早晚各推送一次
```

**frequency_words.txt** - 关键词配置
```txt
# 监控 AI 相关动态
AI 人工智能 大模型
+发布 +突破

# 监控自动化趋势
OpenClaw RPA 自动化
+开源 +更新
```

### 3. 重启服务
```bash
cd /Users/xiaojiujiu2/.openclaw/workspace/xiaodong/trendradar/TrendRadar
docker-compose restart
```

## 📱 使用场景

### 场景1：每日资讯简报
**指令**："给我今天的AI行业动态"

**我会**：
1. 查询 TrendRadar 最新数据
2. 过滤 AI 相关热点
3. 生成结构化摘要
4. 通过飞书推送给你

**示例输出**：
```
📊 AI 行业动态简报 (2026-03-11)

🔥 今日热点：
1. 【DeepSeek】发布新版大模型，性能提升30%
   - 平台：知乎、微博、B站
   - 热度：🔥🔥🔥🔥
   - 趋势：持续上升

2. 【OpenAI】GPT-5 传闻再起，预计Q2发布
   - 平台：华尔街见闻、财联社
   - 热度：🔥🔥🔥
   - 情感：积极

📈 趋势分析：
- AI 模型竞赛加剧，多家公司发布新品
- 开源 AI 工具受开发者欢迎
- 企业级 AI 应用需求增长
```

### 场景2：特定话题监控
**指令**："监控 OpenClaw 相关讨论"

**我会**：
1. 添加 OpenClaw 到监控关键词
2. 设置实时推送
3. 定期汇总分析

**配置更新**：
```txt
# 在 frequency_words.txt 中添加
OpenClaw 自动化助手
+讨论 +教程 +案例
```

### 场景3：竞品分析
**指令**："对比一下主流自动化平台"

**我会**：
1. 监控多个竞品关键词
2. 分析舆论趋势
3. 生成对比报告

**关键词配置**：
```txt
OpenClaw n8n Zapier Make
+评测 +对比 +优缺点
```

## 🔧 高级功能

### 1. MCP 集成查询
通过 MCP 协议深度查询数据：

```python
# 搜索最近3天AI相关新闻
search_news(keywords="AI", days=3, limit=20)

# 获取趋势话题排名
get_trending_topics(platform="zhihu", limit=10)

# AI 分析热点情感
analyze_sentiment(topic="大模型价格战")
```

### 2. 自定义推送规则
**按时间推送**：
```yaml
# config.yaml
schedule:
  preset: "custom"
  monday:
    - time: "08:30"
      mode: "daily"
    - time: "18:00"  
      mode: "incremental"
```

**按重要性过滤**：
```yaml
filter:
  min_rank: 20      # 只推送前20名
  min_appearances: 3 # 至少出现3次
  platforms: ["zhihu", "weibo"] # 只监控特定平台
```

### 3. 数据导出与分析
```bash
# 导出今日数据
curl http://localhost:8000/api/export?format=json

# 生成周报
python scripts/weekly_report.py

# 数据可视化
python scripts/visualize.py --period=7d
```

## 📊 监控指标

### 1. 热度指标
- **排名变化**：话题在榜单的位置变化
- **出现频次**：在监控期间出现的次数
- **持续时间**：从首次出现到最后出现的时间
- **平台覆盖**：在多少个平台同时出现

### 2. 情感分析
- **正面情绪**：积极评价和期待
- **负面情绪**：批评和担忧
- **中性情绪**：事实陈述
- **情绪变化**：随时间的情感走向

### 3. 影响力评估
- **传播速度**：话题扩散的速度
- **参与度**：评论、转发、点赞数量
- **权威性**：信息来源的可信度
- **持续性**：话题的生命周期

## 🚨 告警规则

### 1. 突发热点告警
```yaml
alerts:
  sudden_spike:
    enabled: true
    threshold: 50    # 热度增长50%
    timeframe: "1h"  # 1小时内
    channels: ["feishu", "sms"]
```

### 2. 负面舆情告警
```yaml
  negative_sentiment:
    enabled: true  
    threshold: -0.7  # 情感值低于-0.7
    keywords: ["故障", "投诉", "bug"]
```

### 3. 机会发现告警
```yaml
  opportunity:
    enabled: true
    keywords: ["融资", "合作", "新功能"]
    min_rank: 10
```

## 🔄 工作流集成

### 1. 与现有系统集成
```python
# 飞书机器人回调
@app.route("/feishu/callback", methods=["POST"])
def feishu_callback():
    data = request.json
    # 处理用户查询
    if "查询热点" in data["text"]:
        return get_trending_summary()
```

### 2. 定时任务
```bash
# 每日8:30推送简报
0 8 * * * /usr/local/bin/trendradar daily-report

# 每小时检查突发热点  
0 * * * * /usr/local/bin/trendradar check-alerts

# 每周一生成周报
0 9 * * 1 /usr/local/bin/trendradar weekly-report
```

### 3. API 接口
```bash
# 获取今日热点
curl -X GET "http://localhost:8000/api/trending?date=2026-03-11"

# 搜索历史数据
curl -X POST "http://localhost:8000/api/search" \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["AI", "自动化"], "days": 7}'
```

## 🛠️ 故障排除

### 常见问题

**Q1: 服务启动失败**
```bash
# 查看日志
docker-compose logs trendradar

# 常见原因
- 端口冲突（修改 docker-compose.yml 中的端口）
- 配置文件错误（检查 config.yaml 语法）
- 权限问题（检查文件权限）
```

**Q2: 数据抓取为空**
```bash
# 测试网络连接
docker exec trendradar curl https://www.zhihu.com

# 检查平台配置
cat config/config.yaml | grep -A5 "platforms:"

# 调整抓取频率
# 避免触发反爬机制
```

**Q3: 推送失败**
```bash
# 测试 webhook
curl -X POST "飞书webhook" \
  -H "Content-Type: application/json" \
  -d '{"msg_type":"text","content":{"text":"测试消息"}}'

# 检查推送配置
cat config/config.yaml | grep -A10 "push:"
```

### 性能优化

**内存优化**：
```yaml
# docker-compose.yml
services:
  trendradar:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.3'
```

**数据库优化**：
```bash
# 定期清理旧数据
docker exec trendradar python scripts/cleanup.py --days=30

# 优化索引
docker exec trendradar sqlite3 data.db "CREATE INDEX IF NOT EXISTS idx_date ON news(date);"
```

**网络优化**：
```yaml
# config.yaml
network:
  timeout: 30
  retries: 3
  proxy: "http://proxy:8080"  # 如有需要
```

## 📈 最佳实践

### 1. 关键词策略
- **精准定位**：使用具体的关键词组合
- **排除干扰**：设置排除词过滤无关内容
- **定期更新**：根据热点变化调整关键词
- **分组管理**：按主题分组关键词，便于分析

### 2. 推送策略
- **分时段推送**：工作时间推送详细版，非工作时间推送精简版
- **重要性分级**：重要热点实时推送，普通热点汇总推送
- **个性化定制**：根据不同角色推送不同内容
- **反馈优化**：根据用户反馈调整推送内容

### 3. 数据分析
- **趋势追踪**：关注话题的长期发展趋势
- **对比分析**：对比不同平台、不同时间段的数据
- **关联挖掘**：发现话题间的隐藏关联
- **预测预警**：基于历史数据预测未来趋势

## 🔮 未来扩展

### 1. 多语言支持
- 英文热点监控
- 多语言翻译
- 国际化平台支持

### 2. 垂直领域深化
- 科技金融专项监控
- 医疗健康热点追踪
- 教育政策变化监测

### 3. 智能分析增强
- 自动生成分析报告
- 预测模型优化
- 可视化仪表板

---

**最后更新**：2026-03-11  
**维护状态**：🟢 活跃  
**支持渠道**：飞书联系老金