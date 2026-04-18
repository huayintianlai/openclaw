#!/usr/bin/env python3
"""
创建WPS翻译版和我们的法语版的对比图
左边：WPS参考版
右边：我们的翻译版
"""
from PIL import Image
import fitz

def pdf_to_image(pdf_path, dpi=150):
    """将PDF转为图片"""
    doc = fitz.open(pdf_path)
    page = doc[0]
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    doc.close()

    from io import BytesIO
    return Image.open(BytesIO(img_data))

# 转换两个PDF为图片
print("正在转换PDF为图片...")
print("左边：WPS参考版")
wps_img = pdf_to_image("/Users/xiaojiujiu2/Downloads/ChenTianhao-power-fr.pdf")
print("右边：我们的翻译版（ReportLab）")
our_img = pdf_to_image("/Users/xiaojiujiu2/Downloads/电费账单-陈天浩-ReportLab翻译.pdf")

print(f"WPS版尺寸: {wps_img.size}")
print(f"我们的版本尺寸: {our_img.size}")

# 创建左右对比图
width = max(wps_img.width, our_img.width)
height = max(wps_img.height, our_img.height)

# 调整图片大小使其一致
if wps_img.size != our_img.size:
    wps_img = wps_img.resize((width, height), Image.Resampling.LANCZOS)
    our_img = our_img.resize((width, height), Image.Resampling.LANCZOS)

# 创建对比图（左右拼接，中间留20px空白）
comparison = Image.new('RGB', (width * 2 + 20, height), (255, 255, 255))
comparison.paste(wps_img, (0, 0))
comparison.paste(our_img, (width + 20, 0))

# 保存
output_path = "/Users/xiaojiujiu2/Downloads/法语翻译对比-WPS参考_vs_ReportLab翻译.png"
comparison.save(output_path, 'PNG')
print(f"\n✓ 对比图已生成: {output_path}")
print("左边：WPS参考版 | 右边：ReportLab翻译版")

