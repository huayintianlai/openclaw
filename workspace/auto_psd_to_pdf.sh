#!/bin/bash
# 完全自动化的 PSD → PDF 转换脚本
# 使用 Photoshop 命令行 + ExtendScript

PSD_PATH="$1"
PDF_PATH="$2"

if [ -z "$PSD_PATH" ] || [ -z "$PDF_PATH" ]; then
    echo "❌ 用法: $0 <psd文件> <pdf输出路径>"
    exit 1
fi

if [ ! -f "$PSD_PATH" ]; then
    echo "❌ 错误: PSD 文件不存在 - $PSD_PATH"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JSX_SCRIPT="$SCRIPT_DIR/auto_export_pdf.jsx"

# 清理之前的状态文件
rm -f /tmp/ps_export_success.txt /tmp/ps_export_error.txt

echo "⏳ 使用 Photoshop 自动转换 PSD → PDF..."
echo "   输入: $PSD_PATH"
echo "   输出: $PDF_PATH"

# 设置环境变量
export PSD_PATH="$PSD_PATH"
export PDF_PATH="$PDF_PATH"

# 调用 Photoshop 执行脚本（后台运行）
"/Applications/Adobe Photoshop 2026/Adobe Photoshop 2026.app/Contents/MacOS/Adobe Photoshop 2026" "$JSX_SCRIPT" > /dev/null 2>&1 &
PS_PID=$!

# 等待 Photoshop 完成（最多等待 60 秒）
TIMEOUT=60
ELAPSED=0

while [ $ELAPSED -lt $TIMEOUT ]; do
    # 检查成功标记
    if [ -f /tmp/ps_export_success.txt ]; then
        OUTPUT_PATH=$(cat /tmp/ps_export_success.txt)
        echo "✅ PDF 转换成功: $OUTPUT_PATH"
        rm -f /tmp/ps_export_success.txt
        exit 0
    fi

    # 检查错误标记
    if [ -f /tmp/ps_export_error.txt ]; then
        ERROR_MSG=$(cat /tmp/ps_export_error.txt)
        echo "❌ PDF 转换失败: $ERROR_MSG"
        rm -f /tmp/ps_export_error.txt
        exit 1
    fi

    # 检查 Photoshop 进程是否还在运行
    if ! kill -0 $PS_PID 2>/dev/null; then
        # 进程已结束，再等待 2 秒看是否有结果文件
        sleep 2
        if [ -f /tmp/ps_export_success.txt ]; then
            OUTPUT_PATH=$(cat /tmp/ps_export_success.txt)
            echo "✅ PDF 转换成功: $OUTPUT_PATH"
            rm -f /tmp/ps_export_success.txt
            exit 0
        elif [ -f /tmp/ps_export_error.txt ]; then
            ERROR_MSG=$(cat /tmp/ps_export_error.txt)
            echo "❌ PDF 转换失败: $ERROR_MSG"
            rm -f /tmp/ps_export_error.txt
            exit 1
        else
            echo "❌ Photoshop 进程意外退出"
            exit 1
        fi
    fi

    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

echo "❌ 转换超时（60秒）"
kill $PS_PID 2>/dev/null
exit 1
