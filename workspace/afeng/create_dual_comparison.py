#!/usr/bin/env python3
"""
生成PDF对比图 - pdf2zh翻译结果（双语版）
"""
import fitz
from PIL import Image, ImageDraw, ImageFont
import io

def create_dual_comparison(original_pdf, dual_pdf, output_image):
    """
    生成原文和双语版的对比图

    Args:
        original_pdf: 原始PDF路径
        dual_pdf: 双语PDF路径
        output_image: 输出图片路径
    """
    # 打开PDF
    doc_original = fitz.open(original_pdf)
    doc_dual = fitz.open(dual_pdf)

    # 渲染第一页为图片
    page_original = doc_original[0]
    page_dual = doc_dual[0]

    # 转换为图片 (300 DPI)
    zoom = 2.0
    mat = fitz.Matrix(zoom, zoom)

    pix_original = page_original.get_pixmap(matrix=mat)
    pix_dual = page_dual.get_pixmap(matrix=mat)

    # 转换为PIL Image
    img_original = Image.open(io.BytesIO(pix_original.tobytes()))
    img_dual = Image.open(io.BytesIO(pix_dual.tobytes()))

    # 创建对比图（左右并排）
    width = img_original.width + img_dual.width + 30
    height = max(img_original.height, img_dual.height) + 100

    comparison = Image.new('RGB', (width, height), 'white')

    # 粘贴图片
    comparison.paste(img_original, (10, 90))
    comparison.paste(img_dual, (img_original.width + 20, 90))

    # 添加标题
    draw = ImageDraw.Draw(comparison)

    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 40)
        font_label = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 30)
    except:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()

    # 绘制标题
    draw.text((width//2 - 250, 20), "PDF翻译对比 - pdf2zh双语版", fill='black', font=font_title)
    draw.text((img_original.width//2 - 50, 60), "原文（中文）", fill='blue', font=font_label)
    draw.text((img_original.width + 20 + img_dual.width//2 - 80, 60), "双语版（中+法）", fill='red', font=font_label)

    # 保存
    comparison.save(output_image, 'PNG', quality=95)

    doc_original.close()
    doc_dual.close()

    print(f"✓ 对比图已生成: {output_image}")
    print(f"  原文尺寸: {img_original.size}")
    print(f"  双语版尺寸: {img_dual.size}")


if __name__ == "__main__":
    original = "/Users/xiaojiujiu2/Downloads/电费账单-陈天浩-20260417_100903.pdf"
    dual = "/Users/xiaojiujiu2/Downloads/电费账单-陈天浩-20260417_100903-dual.pdf"
    output = "/Users/xiaojiujiu2/Downloads/电费账单-pdf2zh双语对比.png"

    create_dual_comparison(original, dual, output)
