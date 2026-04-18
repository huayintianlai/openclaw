#!/bin/bash
# TrendRadar 快速部署脚本

set -e

echo "🚀 开始部署 TrendRadar 资讯监控系统..."

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 创建项目目录
PROJECT_DIR="/Users/xiaojiujiu2/.openclaw/workspace/xiaodong/trendradar"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

echo "📁 项目目录: $PROJECT_DIR"

# 克隆或更新仓库
if [ -d "TrendRadar" ]; then
    echo "📦 更新现有仓库..."
    cd TrendRadar
    git pull origin master
else
    echo "📦 克隆 TrendRadar 仓库..."
    git clone https://github.com/sansan0/TrendRadar.git
    cd TrendRadar
fi

# 创建基础配置文件
echo "⚙️ 创建配置文件..."

# 检查配置文件是否存在
if [ ! -f "config/config.yaml" ]; then
    echo "📝 创建默认配置文件..."
    cp config/config.example.yaml config/config.yaml
    
    # 提示用户配置
    echo ""
    echo "⚠️  请编辑以下配置文件："
    echo "1. config/config.yaml - 主要配置"
    echo "2. frequency_words.txt - 关键词配置"
    echo ""
    echo "📋 关键配置项："
    echo "- push.feishu.webhook: 飞书机器人 webhook"
    echo "- ai.api_key: AI 模型 API 密钥"
    echo "- schedule.preset: 推送时间预设"
else
    echo "✅ 配置文件已存在"
fi

# 创建 Docker Compose 文件
if [ ! -f "docker-compose.yml" ]; then
    echo "🐳 创建 Docker Compose 配置..."
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  trendradar:
    image: wantcat/trendradar:latest
    container_name: trendradar
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
      - ./output:/app/output
      - ./data:/app/data
    environment:
      - TZ=Asia/Shanghai
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  mcp_server:
    build: ./mcp_server
    container_name: trendradar-mcp
    restart: unless-stopped
    ports:
      - "8001:8000"
    volumes:
      - ./config:/app/config
      - ./output:/app/output
      - ./data:/app/data
    depends_on:
      - trendradar
    environment:
      - TRENDRADAR_URL=http://trendradar:8000
EOF
fi

# 启动服务
echo "🚀 启动 TrendRadar 服务..."
docker-compose up -d

echo ""
echo "✅ 部署完成！"
echo ""
echo "📊 服务状态："
docker-compose ps
echo ""
echo "🌐 访问地址："
echo "- Web 界面: http://localhost:8000"
echo "- MCP 服务器: http://localhost:8001"
echo ""
echo "📋 后续操作："
echo "1. 编辑 config/config.yaml 配置推送渠道"
echo "2. 编辑 frequency_words.txt 设置监控关键词"
echo "3. 查看日志: docker-compose logs -f"
echo "4. 重启服务: docker-compose restart"
echo ""
echo "🔧 常用命令："
echo "  docker-compose logs -f trendradar    # 查看日志"
echo "  docker-compose restart trendradar    # 重启服务"
echo "  docker-compose down                  # 停止服务"
echo "  docker-compose up -d --build         # 重建并启动"