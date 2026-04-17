#!/bin/bash
# 完美公证文件编辑器 - 100% 不可检测方案
# 使用 Photoshop ExtendScript 直接操作文本属性

set -e

# 参数
COMPANY_NAME="$1"
COMPANY_ADDRESS="$2"
DEPOSIT_DATE="$3"  # YYYY-MM-DD 格式
SIGN_DATE="$4"     # YYYY-MM-DD 格式

if [ -z "$COMPANY_NAME" ] || [ -z "$COMPANY_ADDRESS" ] || [ -z "$DEPOSIT_DATE" ] || [ -z "$SIGN_DATE" ]; then
    echo "❌ 用法: $0 <公司名称> <公司地址> <资本存款日期YYYY-MM-DD> <落款日期YYYY-MM-DD>"
    echo "示例: $0 'FinalTest SARL' '123 Rue de Paris, 75001 Paris' '2026-03-10' '2026-03-15'"
    exit 1
fi

# 日期转换函数：YYYY-MM-DD → "10 mars 2026"（不带Le）
convert_to_french_date() {
    local date_str="$1"
    local year=$(echo "$date_str" | cut -d'-' -f1)
    local month=$(echo "$date_str" | cut -d'-' -f2)
    local day=$(echo "$date_str" | cut -d'-' -f3)

    # 去掉前导零
    day=$((10#$day))

    # 法语月份
    case $month in
        01) month_fr="janvier" ;;
        02) month_fr="février" ;;
        03) month_fr="mars" ;;
        04) month_fr="avril" ;;
        05) month_fr="mai" ;;
        06) month_fr="juin" ;;
        07) month_fr="juillet" ;;
        08) month_fr="août" ;;
        09) month_fr="septembre" ;;
        10) month_fr="octobre" ;;
        11) month_fr="novembre" ;;
        12) month_fr="décembre" ;;
        *) echo "❌ 无效月份: $month"; exit 1 ;;
    esac

    echo "$day $month_fr $year"
}

# 日期转换函数：YYYY-MM-DD → "Le 10 mars 2026"（带Le）
convert_to_french_date_with_le() {
    local date_str="$1"
    local base_date=$(convert_to_french_date "$date_str")
    echo "Le $base_date"
}

# 转换日期
DEPOSIT_DATE_FR=$(convert_to_french_date "$DEPOSIT_DATE")  # 资本存款时间：模板已有"le"
SIGN_DATE_FR=$(convert_to_french_date_with_le "$SIGN_DATE")  # 落款时间：需要"Le"

echo "📝 公证文件编辑参数："
echo "   公司名称: $COMPANY_NAME"
echo "   公司地址: $COMPANY_ADDRESS"
echo "   资本存款时间: $DEPOSIT_DATE_FR"
echo "   落款时间: $SIGN_DATE_FR"
echo ""

# 文件路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_PSD="/Users/xiaojiujiu2/Downloads/资本存款.psd"
OUTPUT_PDF="/Users/xiaojiujiu2/Downloads/资本存款_${COMPANY_NAME// /_}_$(date +%Y%m%d_%H%M%S).pdf"
TEMP_JSX="/tmp/ps_perfect_$(date +%s).jsx"

if [ ! -f "$TEMPLATE_PSD" ]; then
    echo "❌ 错误: 模板 PSD 文件不存在 - $TEMPLATE_PSD"
    exit 1
fi

echo "⏳ 生成 Photoshop 脚本..."

# 复制 JSX 模板并替换占位符
cp "$SCRIPT_DIR/perfect_certificate_editor.jsx" "$TEMP_JSX"

# 使用 sed 替换占位符（macOS 需要 -i ''）
sed -i '' "s|PSD_PATH_PLACEHOLDER|$TEMPLATE_PSD|g" "$TEMP_JSX"
sed -i '' "s|PDF_PATH_PLACEHOLDER|$OUTPUT_PDF|g" "$TEMP_JSX"
sed -i '' "s|COMPANY_NAME_PLACEHOLDER|$COMPANY_NAME|g" "$TEMP_JSX"
sed -i '' "s|COMPANY_ADDRESS_PLACEHOLDER|$COMPANY_ADDRESS|g" "$TEMP_JSX"
sed -i '' "s|DEPOSIT_DATE_PLACEHOLDER|$DEPOSIT_DATE_FR|g" "$TEMP_JSX"
sed -i '' "s|SIGN_DATE_PLACEHOLDER|$SIGN_DATE_FR|g" "$TEMP_JSX"

# 清理之前的状态文件
rm -f /tmp/ps_perfect_export_success.txt /tmp/ps_perfect_export_error.txt

echo "⏳ 启动 Photoshop 执行编辑..."

# 调用 Photoshop 执行脚本
"/Applications/Adobe Photoshop 2026/Adobe Photoshop 2026.app/Contents/MacOS/Adobe Photoshop 2026" "$TEMP_JSX" > /dev/null 2>&1 &
PS_PID=$!

# 等待完成
TIMEOUT=90
ELAPSED=0

while [ $ELAPSED -lt $TIMEOUT ]; do
    if [ -f /tmp/ps_perfect_export_success.txt ]; then
        OUTPUT_PATH=$(cat /tmp/ps_perfect_export_success.txt)
        echo "✅ PDF 生成成功: $OUTPUT_PATH"

        # 等待 Photoshop 完全退出
        sleep 2
        pkill -9 "Adobe Photoshop 2026" 2>/dev/null

        rm -f /tmp/ps_perfect_export_success.txt "$TEMP_JSX"

        # 显示文件大小
        FILE_SIZE=$(stat -f%z "$OUTPUT_PATH" 2>/dev/null || stat -c%s "$OUTPUT_PATH" 2>/dev/null)
        FILE_SIZE_MB=$(echo "scale=2; $FILE_SIZE / 1048576" | bc)
        echo "📊 文件大小: ${FILE_SIZE_MB}M"

        echo ""
        echo "📄 文件已保存到: $OUTPUT_PATH"
        exit 0
    fi

    if [ -f /tmp/ps_perfect_export_error.txt ]; then
        ERROR_MSG=$(cat /tmp/ps_perfect_export_error.txt)
        echo "❌ 编辑失败: $ERROR_MSG"
        pkill -9 "Adobe Photoshop 2026" 2>/dev/null
        rm -f /tmp/ps_perfect_export_error.txt "$TEMP_JSX"
        exit 1
    fi

    if ! kill -0 $PS_PID 2>/dev/null; then
        sleep 2
        if [ -f /tmp/ps_perfect_export_success.txt ]; then
            OUTPUT_PATH=$(cat /tmp/ps_perfect_export_success.txt)
            echo "✅ PDF 生成成功: $OUTPUT_PATH"
            pkill -9 "Adobe Photoshop 2026" 2>/dev/null
            rm -f /tmp/ps_perfect_export_success.txt "$TEMP_JSX"
            echo ""
            echo "📄 文件已保存到: $OUTPUT_PATH"
            exit 0
        elif [ -f /tmp/ps_perfect_export_error.txt ]; then
            ERROR_MSG=$(cat /tmp/ps_perfect_export_error.txt)
            echo "❌ 编辑失败: $ERROR_MSG"
            pkill -9 "Adobe Photoshop 2026" 2>/dev/null
            rm -f /tmp/ps_perfect_export_error.txt "$TEMP_JSX"
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

echo "❌ 处理超时（90秒）"
pkill -9 "Adobe Photoshop 2026" 2>/dev/null
rm -f "$TEMP_JSX"
exit 1
