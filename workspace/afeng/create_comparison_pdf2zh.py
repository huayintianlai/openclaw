#!/usr/bin/env python3
"""
生成PDF对比图 - pdf2zh翻译结果
"""
import fitz
from PIL import Image
import io

def create_comparison(original_pdf, translated_pdf, output_image):
    """
    生成原文和译文的对比图

    Args:
        original_pdf: 原始PDF路径
        translated_pdf: 翻译后的PDF路径
        output_image: 输出图片路径
    """
    # 打开PDF
    doc_original = fitz.open(original_pdf)
    doc_translated = fitz.open(translated_pdf)

    # 渲染第一页为图片
    page_original = doc_original[0]
    page_translated = doc_translated[0]

    # 转换为图片 (300 DPI)
    zoom = 2.0  # 放大倍数，提高清晰度
    mat = fitz.Matrix(zoom, zoom)

    pix_original = page_original.get_pixmap(matrix=mat)
    pix_translated = page_translated.get_pixmap(matrix=mat)

    # 转换为PIL Image
    img_original = Image.open(io.BytesIO(pix_original.tobytes()))
    img_translated = Image.open(io.BytesIO(pix_translated.tobytes()))

    # 创建对比图（左右并排）
    width = img_original.width + img_translated.width + 30  # 中间留30px间隔
    height = max(img_original.height, img_translated.height) + 100  # 顶部留100px标题

    comparison = Image.new('RGB', (width, height), 'white')

    # 粘贴图片
    comparison.paste(img_original, (10, 90))
    comparison.paste(img_translated, (img_original.width + 20, 90))

    # 添加标题
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(comparison)

    try:
        # 尝试使用系统字体
        font_title = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 40)
        font_label = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 30)
    except:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()

    # 绘制标题
    draw.text((width//2 - 200, 20), "PDF翻译对比 - pdf2zh方案", fill='black', font=font_title)
    draw.text((img_original.width//2 - 50, 60), "原文（中文）", fill='blue', font=font_label)
    draw.text((img_original.width + 20 + img_translated.width//2 - 50, 60), "译文（法语）", fill='red', font=font_label)

    # 保存
    comparison.save(output_image, 'PNG', quality=95)

    doc_original.close()
    doc_translated.close()

    print(f"✓ 对比图已生成: {output_image}")
    print(f"  原文尺寸: {img_original.size}")
    print(f"  译文尺寸: {img_translated.size}")


if __name__ == "__main__":
    original = "/Users/xiaojiujiu2/Downloads/电费账单-陈天浩-20260417_100903.pdf"
    translated = "/Users/xiaojiujiu2/Downloads/电费账单-陈天浩-20260417_100903-dual.pdf"
    output = "/Users/xiaojiujiu2/Downloads/电费账单-pdf2zh翻译对比.png"

    create_comparison(original, translated, output)
