#!/bin/bash
# Memory System Test - Quick Check Script
# 用于快速验证 OpenClaw 系统状态

echo "=========================================="
echo "OpenClaw Memory System - Pre-Test Check"
echo "=========================================="
echo ""

# 1. 检查 Docker 容器状态
echo "1. 检查 Docker 容器状态..."
docker ps --filter "name=kentclaw" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# 2. 检查环境变量
echo "2. 检查关键环境变量..."
if [ -f "/Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/.env" ]; then
    echo "✅ .env 文件存在"

    # 检查 Mem0 相关配置
    grep -q "QDRANT_URL" /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/.env && echo "✅ QDRANT_URL 已配置" || echo "❌ QDRANT_URL 未配置"
    grep -q "QDRANT_API_KEY" /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/.env && echo "✅ QDRANT_API_KEY 已配置" || echo "❌ QDRANT_API_KEY 未配置"
    grep -q "MEM0_BASE_USER_ID" /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/.env && echo "✅ MEM0_BASE_USER_ID 已配置" || echo "❌ MEM0_BASE_USER_ID 未配置"

    # 检查飞书配置
    grep -q "FEISHU_XIAODONG_APP_ID" /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/.env && echo "✅ 小东飞书配置存在" || echo "❌ 小东飞书配置缺失"
    grep -q "FEISHU_XIAOGUAN_APP_ID" /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/.env && echo "✅ 小冠飞书配置存在" || echo "❌ 小冠飞书配置缺失"
    grep -q "FEISHU_FINANCE_APP_ID" /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/.env && echo "✅ Finance 飞书配置存在" || echo "❌ Finance 飞书配置缺失"
else
    echo "❌ .env 文件不存在"
fi
echo ""

# 3. 检查 openclaw.json 配置
echo "3. 检查 openclaw.json 配置..."
if [ -f "/Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/openclaw.json" ]; then
    echo "✅ openclaw.json 存在"

    # 检查 Mem0 插件配置
    grep -q '"openclaw-mem0"' /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/openclaw.json && echo "✅ Mem0 插件已配置" || echo "❌ Mem0 插件未配置"

    # 检查 agent 配置
    grep -q '"id": "xiaodong"' /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/openclaw.json && echo "✅ xiaodong agent 已配置" || echo "❌ xiaodong agent 未配置"
    grep -q '"id": "xiaoguan"' /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/openclaw.json && echo "✅ xiaoguan agent 已配置" || echo "❌ xiaoguan agent 未配置"
    grep -q '"id": "finance"' /Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/openclaw.json && echo "✅ finance agent 已配置" || echo "❌ finance agent 未配置"
else
    echo "❌ openclaw.json 不存在"
fi
echo ""

# 4. 检查 workspace 目录
echo "4. 检查 workspace 目录..."
for agent in xiaodong xiaoguan finance xiaodong_crossborder_scout echo; do
    if [ -d "/Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/workspace/$agent" ]; then
        echo "✅ $agent workspace 存在"
        if [ -f "/Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/workspace/$agent/AGENTS.md" ]; then
            echo "   ✅ AGENTS.md 存在"
        else
            echo "   ⚠️  AGENTS.md 不存在"
        fi
    else
        echo "❌ $agent workspace 不存在"
    fi
done
echo ""

# 5. 检查插件目录
echo "5. 检查插件状态..."
if [ -d "/Users/xiaojiujiu2/Documents/openclaw-docker/plugins" ]; then
    echo "✅ plugins 目录存在"
    ls -la /Users/xiaojiujiu2/Documents/openclaw-docker/plugins/ | grep -E "knowledge-search-plugin|tavily-search-plugin" && echo "✅ 当前仓库插件目录存在" || echo "⚠️  当前仓库插件目录可能缺失"
else
    echo "⚠️  plugins 目录不存在（可能在容器内）"
fi
echo ""

# 6. 检查测试文件
echo "6. 检查测试文件..."
test -f "/Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/workspace/test_memory_system.md" && echo "✅ test_memory_system.md 已创建" || echo "❌ test_memory_system.md 未创建"
test -f "/Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/workspace/test_execution_log.md" && echo "✅ test_execution_log.md 已创建" || echo "❌ test_execution_log.md 未创建"
test -f "/Users/xiaojiujiu2/Documents/openclaw-docker/instances/kentclaw/data/workspace/test_guide.md" && echo "✅ test_guide.md 已创建" || echo "❌ test_guide.md 未创建"
echo ""

# 7. 网络连接测试
echo "7. 测试网络连接..."
curl -s -o /dev/null -w "Qdrant: %{http_code}\n" https://qdrant.99uwen.com || echo "❌ Qdrant 连接失败"
echo ""

echo "=========================================="
echo "预检查完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 如果所有检查都通过，可以开始测试"
echo "2. 打开飞书，找到对应的机器人"
echo "3. 按照 test_guide.md 中的步骤执行测试"
echo "4. 在 test_execution_log.md 中记录结果"
echo ""
