#!/bin/bash
# TrendRadar MCP 服务器测试脚本

echo "🔍 测试 TrendRadar MCP 服务器连接..."

# 检查 MCP 服务器是否运行
if ! curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "❌ MCP 服务器未运行，请先启动服务"
    echo "运行: docker-compose up -d mcp_server"
    exit 1
fi

echo "✅ MCP 服务器运行正常"

# 测试 MCP 工具列表
echo ""
echo "🛠️  获取可用工具列表..."
curl -s -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list",
    "params": {}
  }' | python3 -m json.tool

# 测试搜索新闻
echo ""
echo "🔎 测试搜索新闻功能..."
curl -s -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "tool": "search_news",
      "arguments": {
        "keywords": "AI",
        "days": 1,
        "limit": 3
      }
    }
  }' | python3 -m json.tool

# 测试获取趋势话题
echo ""
echo "📈 测试获取趋势话题..."
curl -s -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "tool": "get_trending_topics",
      "arguments": {
        "platform": "zhihu",
        "limit": 5
      }
    }
  }' | python3 -m json.tool

echo ""
echo "✅ 测试完成！"
echo ""
echo "📋 后续步骤："
echo "1. 配置飞书 webhook 接收推送"
echo "2. 编辑 frequency_words.txt 设置监控关键词"
echo "3. 设置定时任务自动运行"
echo ""
echo "💡 提示：如果返回数据为空，请确保："
echo "- TrendRadar 主服务已运行"
"- 已有抓取到的数据"
"- 网络连接正常"