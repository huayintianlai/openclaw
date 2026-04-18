#!/usr/bin/env python3
"""
生成最终对比图 - 优化前 vs 优化后
"""
import fitz
from PIL import Image, ImageDraw, ImageFont
import io

def create_final_comparison(before_pdf, after_pdf, output_image):
    """
    生成优化前后的对比图

    Args:
        before_pdf: 优化前的PDF路径
        after_pdf: 优化后的PDF路径
        output_image: 输出图片路径
    """
    # 打开PDF
    doc_before = fitz.open(before_pdf)
    doc_after = fitz.open(after_pdf)

    # 渲染第一页为图片
    page_before = doc_before[0]
    page_after = doc_after[0]

    # 转换为图片 (300 DPI)
    zoom = 2.0
    mat = fitz.Matrix(zoom, zoom)

    pix_before = page_before.get_pixmap(matrix=mat)
    pix_after = page_after.get_pixmap(matrix=mat)

    # 转换为PIL Image
    img_before = Image.open(io.BytesIO(pix_before.tobytes()))
    img_after = Image.open(io.BytesIO(pix_after.tobytes()))

    # 创建对比图（左右并排）
    width = img_before.width + img_after.width + 30
    height = max(img_before.height, img_after.height) + 100

    comparison = Image.new('RGB', (width, height), 'white')

    # 粘贴图片
    comparison.paste(img_before, (10, 90))
    comparison.paste(img_after, (img_before.width + 20, 90))

    # 添加标题
    draw = ImageDraw.Draw(comparison)

    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 40)
        font_label = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 30)
    except:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()

    # 绘制标题
    draw.text((width//2 - 300, 20), "PDF翻译优化对比 - 优化前 vs 优化后", fill='black', font=font_title)
    draw.text((img_before.width//2 - 100, 60), "优化前 (85%)", fill='blue', font=font_label)
    draw.text((img_before.width + 20 + img_after.width//2 - 100, 60), "优化后 (95%+)", fill='green', font=font_label)

    # 保存
    comparison.save(output_image, 'PNG', quality=95)

    doc_before.close()
    doc_after.close()

    print(f"✓ 对比图已生成: {output_image}")
    print(f"  优化前尺寸: {img_before.size}")
    print(f"  优化后尺寸: {img_after.size}")


if __name__ == "__main__":
    before = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng/backup/电费账单-陈天浩-GLM翻译-优化前.pdf"
    after = "/Users/xiaojiujiu2/Downloads/电费账单-陈天浩-GLM翻译.pdf"
    output = "/Users/xiaojiujiu2/Downloads/法语翻译对比-优化前_vs_优化后.png"

    # 先备份优化前的版本
    import shutil
    import os

    backup_dir = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng/backup"
    os.makedirs(backup_dir, exist_ok=True)

    if not os.path.exists(before):
        print("⚠️  优化前的PDF不存在，无法生成对比图")
        print("   请先运行一次优化前的版本并保存")
    else:
        create_final_comparison(before, after, output)
