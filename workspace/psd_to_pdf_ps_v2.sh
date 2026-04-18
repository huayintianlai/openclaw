#!/bin/bash
# 使用 Photoshop 将 PSD 转换为 PDF (改进版)

PSD_PATH="$1"
PDF_PATH="$2"

if [ -z "$PSD_PATH" ] || [ -z "$PDF_PATH" ]; then
    echo "用法: $0 <psd文件> <pdf输出路径>"
    exit 1
fi

if [ ! -f "$PSD_PATH" ]; then
    echo "❌ 错误: PSD 文件不存在 - $PSD_PATH"
    exit 1
fi

echo "⏳ 使用 Photoshop 转换 PSD → PDF..."
echo "   输入: $PSD_PATH"
echo "   输出: $PDF_PATH"

# 使用 AppleScript，增加超时时间
osascript -l JavaScript <<EOF
var app = Application('Adobe Photoshop 2026');
app.includeStandardAdditions = true;

try {
    // 打开 PSD 文件
    var psdPath = Path('$PSD_PATH');
    var psdFile = app.open(psdPath);

    // 等待文件打开
    delay(2);

    // 保存为 PDF
    var pdfPath = Path('$PDF_PATH');
    var pdfOptions = {
        class: 'Photoshop PDF save options',
        embedColorProfile: true,
        JPEGQuality: 12
    };

    psdFile.saveAs(pdfPath, {as: 'Photoshop PDF', in: pdfOptions});

    // 关闭文档
    psdFile.close({saving: 'no'});

    console.log('✅ PDF 转换成功');

} catch (e) {
    console.log('❌ 错误: ' + e.message);
    throw e;
}
EOF

if [ $? -eq 0 ]; then
    echo "✅ PDF 已保存: $PDF_PATH"
    exit 0
else
    echo "❌ PDF 转换失败"
    exit 1
fi
