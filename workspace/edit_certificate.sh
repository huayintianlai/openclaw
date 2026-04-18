#!/bin/bash
# 公证文件编辑工具 - 便捷启动脚本
# 自动激活虚拟环境并运行 PhotoshopAPI 编辑器

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/photoshop_env"
PYTHON_SCRIPT="$SCRIPT_DIR/certificate_editor_complete.py"

# 检查虚拟环境
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ 错误: 虚拟环境不存在"
    echo "请先运行: python3.13 -m venv photoshop_env"
    echo "然后安装: source photoshop_env/bin/activate && pip install PhotoshopAPI"
    exit 1
fi

# 检查 Python 脚本
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ 错误: 找不到 $PYTHON_SCRIPT"
    exit 1
fi

# 激活虚拟环境并运行
source "$VENV_DIR/bin/activate"
python "$PYTHON_SCRIPT" "$@"
