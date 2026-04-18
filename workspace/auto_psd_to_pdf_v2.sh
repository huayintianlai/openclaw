#!/bin/bash
# 完全自动化的 PSD → PDF 转换脚本 v2
# 动态生成 JSX 脚本

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

echo "⏳ 使用 Photoshop 自动转换 PSD → PDF..."
echo "   输入: $PSD_PATH"
echo "   输出: $PDF_PATH"

# 动态生成 JSX 脚本
TEMP_JSX="/tmp/ps_export_$(date +%s).jsx"

cat > "$TEMP_JSX" <<'EOFJS'
#target photoshop

var psdPath = "PSD_PATH_PLACEHOLDER";
var pdfPath = "PDF_PATH_PLACEHOLDER";

try {
    // 打开 PSD 文件
    var psdFile = new File(psdPath);
    if (!psdFile.exists) {
        throw new Error("PSD 文件不存在: " + psdPath);
    }

    var doc = app.open(psdFile);

    // 配置 PDF 保存选项
    var pdfSaveOptions = new PDFSaveOptions();
    pdfSaveOptions.encoding = PDFEncoding.JPEG;
    pdfSaveOptions.jpegQuality = 12;
    pdfSaveOptions.embedColorProfile = true;
    pdfSaveOptions.optimizeForWeb = false;

    // 保存为 PDF
    var pdfFile = new File(pdfPath);
    doc.saveAs(pdfFile, pdfSaveOptions, true, Extension.LOWERCASE);

    // 关闭文档
    doc.close(SaveOptions.DONOTSAVECHANGES);

    // 成功标记
    var successFile = new File("/tmp/ps_export_success.txt");
    successFile.open("w");
    successFile.write(pdfPath);
    successFile.close();

} catch (e) {
    // 错误标记
    var errorFile = new File("/tmp/ps_export_error.txt");
    errorFile.open("w");
    errorFile.write(e.message + " (Line: " + e.line + ")");
    errorFile.close();
}

// 退出 Photoshop
app.quit();
EOFJS

# 替换占位符
sed -i '' "s|PSD_PATH_PLACEHOLDER|$PSD_PATH|g" "$TEMP_JSX"
sed -i '' "s|PDF_PATH_PLACEHOLDER|$PDF_PATH|g" "$TEMP_JSX"

# 清理之前的状态文件
rm -f /tmp/ps_export_success.txt /tmp/ps_export_error.txt

# 调用 Photoshop 执行脚本
"/Applications/Adobe Photoshop 2026/Adobe Photoshop 2026.app/Contents/MacOS/Adobe Photoshop 2026" "$TEMP_JSX" > /dev/null 2>&1 &
PS_PID=$!

# 等待完成
TIMEOUT=60
ELAPSED=0

while [ $ELAPSED -lt $TIMEOUT ]; do
    if [ -f /tmp/ps_export_success.txt ]; then
        OUTPUT_PATH=$(cat /tmp/ps_export_success.txt)
        echo "✅ PDF 转换成功: $OUTPUT_PATH"
        rm -f /tmp/ps_export_success.txt "$TEMP_JSX"
        exit 0
    fi

    if [ -f /tmp/ps_export_error.txt ]; then
        ERROR_MSG=$(cat /tmp/ps_export_error.txt)
        echo "❌ PDF 转换失败: $ERROR_MSG"
        rm -f /tmp/ps_export_error.txt "$TEMP_JSX"
        exit 1
    fi

    if ! kill -0 $PS_PID 2>/dev/null; then
        sleep 2
        if [ -f /tmp/ps_export_success.txt ]; then
            OUTPUT_PATH=$(cat /tmp/ps_export_success.txt)
            echo "✅ PDF 转换成功: $OUTPUT_PATH"
            rm -f /tmp/ps_export_success.txt "$TEMP_JSX"
            exit 0
        elif [ -f /tmp/ps_export_error.txt ]; then
            ERROR_MSG=$(cat /tmp/ps_export_error.txt)
            echo "❌ PDF 转换失败: $ERROR_MSG"
            rm -f /tmp/ps_export_error.txt "$TEMP_JSX"
            exit 1
        else
            echo "❌ Photoshop 进程意外退出"
            rm -f "$TEMP_JSX"
            exit 1
        fi
    fi

    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

echo "❌ 转换超时（60秒）"
kill $PS_PID 2>/dev/null
rm -f "$TEMP_JSX"
exit 1
