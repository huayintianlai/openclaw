# OpenStoryline Docker 部署总结

## 部署状态

✅ **成功部署** - 2026-04-04

## 服务信息

### 容器信息
- **容器名称**: `openstoryline`
- **镜像**: `openstoryline-src-openstoryline:latest`
- **状态**: Running

### 端口映射
- **Web UI**: http://localhost:7860
- **MCP Server**: http://localhost:8002 (容器内部 8001)

### 数据卷
- `openstoryline-outputs`: 存储视频输出文件

## 项目架构

### 核心组件

1. **MCP Server** (Model Context Protocol)
   - 端口: 8001 (内部)
   - 功能: 提供视频编辑工具的 MCP 接口
   - 可用节点: LoadMediaNode, SearchMediaNode, SplitShotsNode, GenerateScriptNode, RenderVideoNode 等

2. **FastAPI Web Server**
   - 端口: 7860
   - 功能: Web UI 和 Agent API
   - 文件: `agent_fastapi.py`

3. **LangChain Agent**
   - 使用 LangGraph 构建
   - 支持自然语言视频编辑指令
   - 集成 OpenAI/其他 LLM

### 技术栈

```
Python 3.11
├── FastAPI 0.128.0
├── LangChain 1.2.10
├── LangGraph 1.0.8
├── MCP 1.26.0
├── MoviePy 2.2.1
├── FFmpeg
├── Sentence Transformers 5.2.2
└── FunASR 1.3.1
```

## 关键文件

### 配置文件
- `config.toml`: 主配置文件（LLM、VLM、路径、工具参数）
- `docker-compose.yml`: Docker 编排配置
- `requirements.txt`: Python 依赖

### 核心代码
- `agent_fastapi.py`: FastAPI 应用入口
- `src/open_storyline/agent.py`: Agent 构建逻辑
- `src/open_storyline/mcp/server.py`: MCP Server 实现
- `src/open_storyline/nodes/`: 视频编辑节点实现

## 使用方式

### 1. 启动服务

```bash
cd /Volumes/KenDisk/Coding/openclaw-runtime/workspace/echo/openstoryline-src
docker-compose up -d
```

### 2. 查看日志

```bash
docker logs openstoryline -f
```

### 3. 停止服务

```bash
docker-compose down
```

### 4. 重新构建

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

## 配置说明

### LLM 配置 (config.toml)

需要配置以下参数才能使用：

```toml
[llm]
model = "gpt-4"  # 或其他模型
base_url = "https://api.openai.com/v1"
api_key = "your-api-key"

[vlm]
model = "gpt-4-vision"
base_url = "https://api.openai.com/v1"
api_key = "your-api-key"
```

### 可选配置

- **Pexels API**: 在线素材搜索
- **TTS 服务**: 配音生成（302/ByteDance/MiniMax）
- **AI 转场**: 视频转场生成（DashScope/MiniMax）

## 调用方式

### 方式 1: Web UI

访问 http://localhost:7860，通过界面进行视频编辑。

### 方式 2: MCP 客户端

通过 MCP 协议调用工具：

```python
from mcp import ClientSession

async with ClientSession("http://localhost:8002/mcp") as session:
    # 调用工具
    result = await session.call_tool("load_media", {
        "media_path": "/path/to/video.mp4"
    })
```

### 方式 3: OpenClaw 集成

在 OpenClaw 中通过 MCP 工具调用：

```javascript
// 配置 MCP 服务器
{
  "mcpServers": {
    "openstoryline": {
      "url": "http://localhost:8002/mcp",
      "transport": "http"
    }
  }
}
```

## 已解决的问题

### 1. Debian 镜像源网络问题
- **问题**: 502 Bad Gateway
- **解决**: 使用阿里云镜像源

### 2. LangChain 依赖冲突
- **问题**: `ImportError: cannot import name 'ExecutionInfo' from 'langgraph.runtime'`
- **解决**: 使用兼容版本组合（langchain 1.2.10 + langgraph 1.0.8）

### 3. Docker 挂载路径问题
- **问题**: `/host_mnt/Volumes/KenDisk: file exists`
- **解决**: 使用 Docker volume 而非直接挂载

### 4. 端口冲突
- **问题**: 8001 端口被占用
- **解决**: 映射到 8002 端口

## 下一步

### 1. 配置 LLM API Key
编辑容器内的 `/app/config.toml` 或重新构建镜像时注入环境变量。

### 2. 测试视频编辑功能
通过 Web UI 或 API 测试完整的视频编辑流程。

### 3. 集成到 OpenClaw
将 OpenStoryline 作为 MCP 工具集成到 OpenClaw 工作流中。

### 4. 自定义 Skills
参考 `.storyline/skills` 目录，创建自定义视频编辑 Skills。

## 参考资料

- **GitHub**: https://github.com/FireRedTeam/FireRed-OpenStoryline
- **文档**: https://fireredteam.github.io/demos/firered_openstoryline/
- **HuggingFace Demo**: https://fireredteam-firered-openstoryline.hf.space/

## 维护命令

```bash
# 查看容器状态
docker ps | grep openstoryline

# 进入容器
docker exec -it openstoryline bash

# 查看资源使用
docker stats openstoryline

# 清理未使用的镜像
docker image prune -a

# 备份配置
docker cp openstoryline:/app/config.toml ./config.toml.backup
```
