#!/usr/bin/env python3
"""
生成PDF对比图 - GLM翻译版 vs ReportLab翻译版
"""
import fitz
from PIL import Image, ImageDraw, ImageFont
import io

def create_glm_comparison(reportlab_pdf, glm_pdf, output_image):
    """
    生成ReportLab版和GLM版的对比图

    Args:
        reportlab_pdf: ReportLab翻译的PDF路径
        glm_pdf: GLM翻译的PDF路径
        output_image: 输出图片路径
    """
    # 打开PDF
    doc_reportlab = fitz.open(reportlab_pdf)
    doc_glm = fitz.open(glm_pdf)

    # 渲染第一页为图片
    page_reportlab = doc_reportlab[0]
    page_glm = doc_glm[0]

    # 转换为图片 (300 DPI)
    zoom = 2.0
    mat = fitz.Matrix(zoom, zoom)

    pix_reportlab = page_reportlab.get_pixmap(matrix=mat)
    pix_glm = page_glm.get_pixmap(matrix=mat)

    # 转换为PIL Image
    img_reportlab = Image.open(io.BytesIO(pix_reportlab.tobytes()))
    img_glm = Image.open(io.BytesIO(pix_glm.tobytes()))

    # 创建对比图（左右并排）
    width = img_reportlab.width + img_glm.width + 30
    height = max(img_reportlab.height, img_glm.height) + 100

    comparison = Image.new('RGB', (width, height), 'white')

    # 粘贴图片
    comparison.paste(img_reportlab, (10, 90))
    comparison.paste(img_glm, (img_reportlab.width + 20, 90))

    # 添加标题
    draw = ImageDraw.Draw(comparison)

    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 40)
        font_label = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 30)
    except:
        font_title = ImageFont.load_default()
        font_label = ImageFont.load_default()

    # 绘制标题
    draw.text((width//2 - 300, 20), "PDF翻译对比 - ReportLab vs GLM", fill='black', font=font_title)
    draw.text((img_reportlab.width//2 - 100, 60), "ReportLab翻译", fill='blue', font=font_label)
    draw.text((img_reportlab.width + 20 + img_glm.width//2 - 80, 60), "GLM翻译", fill='red', font=font_label)

    # 保存
    comparison.save(output_image, 'PNG', quality=95)

    doc_reportlab.close()
    doc_glm.close()

    print(f"✓ 对比图已生成: {output_image}")
    print(f"  ReportLab版尺寸: {img_reportlab.size}")
    print(f"  GLM版尺寸: {img_glm.size}")


if __name__ == "__main__":
    reportlab = "/Users/xiaojiujiu2/Downloads/电费账单-陈天浩-ReportLab翻译.pdf"
    glm = "/Users/xiaojiujiu2/Downloads/电费账单-陈天浩-GLM翻译.pdf"
    output = "/Users/xiaojiujiu2/Downloads/法语翻译对比-ReportLab_vs_GLM.png"

    create_glm_comparison(reportlab, glm, output)
