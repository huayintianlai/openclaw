#!/bin/bash
# 使用 Photoshop 将 PSD 转换为 PDF

PSD_PATH="$1"
PDF_PATH="$2"

if [ -z "$PSD_PATH" ] || [ -z "$PDF_PATH" ]; then
    echo "用法: $0 <psd文件> <pdf输出路径>"
    exit 1
fi

# 检查 PSD 文件是否存在
if [ ! -f "$PSD_PATH" ]; then
    echo "❌ 错误: PSD 文件不存在 - $PSD_PATH"
    exit 1
fi

echo "⏳ 使用 Photoshop 转换 PSD → PDF..."
echo "   输入: $PSD_PATH"
echo "   输出: $PDF_PATH"

# 使用 AppleScript 调用 Photoshop
osascript <<EOF
tell application "Adobe Photoshop 2026"
    activate

    -- 打开 PSD 文件
    set psdFile to POSIX file "$PSD_PATH"
    open psdFile

    -- 获取当前文档
    set currentDoc to current document

    -- 保存为 PDF
    set pdfFile to POSIX file "$PDF_PATH"
    save currentDoc in pdfFile as Photoshop PDF with options {embed color profile:true, JPEG quality:12}

    -- 关闭文档（不保存）
    close currentDoc saving no

    -- 退出 Photoshop
    quit
end tell
EOF

if [ $? -eq 0 ]; then
    echo "✅ PDF 转换成功: $PDF_PATH"
    exit 0
else
    echo "❌ PDF 转换失败"
    exit 1
fi
