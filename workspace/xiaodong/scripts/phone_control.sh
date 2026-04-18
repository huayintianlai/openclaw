#!/bin/bash
# 兼容旧流程的 AutoGLM 包装器。
# 新业务逻辑应优先使用 mobile_* 工具，而不是直接调用此脚本。

AUTOGLM_DIR="/Users/xiaojiujiu2/Documents/coding/AutoGLM"

cd "$AUTOGLM_DIR"
source .venv/bin/activate

./start_phone.sh "$@"
