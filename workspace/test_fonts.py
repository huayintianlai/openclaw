#!/usr/bin/env python3
"""
改进版 PSD 编辑器 - 精确匹配原始字体样式
"""
from psd_tools import PSDImage
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sys

def create_faux_bold_text(draw, text, position, font, color, tracking=0):
    """
    创建伪粗体效果（模拟 Photoshop 的 FauxBold）
    通过多次绘制文本并轻微偏移来实现
    """
    x, y = position

    # 绘制多层文本来模拟粗体
    offsets = [(0, 0), (1, 0), (0, 1), (1, 1), (0.5, 0), (0, 0.5)]

    for offset_x, offset_y in offsets:
        draw.text((x + offset_x, y + offset_y), text, font=font, fill=color)

def test_fonts():
    """测试不同字体的效果"""
    psd_path = "/Users/xiaojiujiu2/Downloads/资本存款.psd"

    print("正在加载 PSD...")
    psd = PSDImage.open(psd_path)
    image = psd.composite()
    draw = ImageDraw.Draw(image)

    # 测试字体列表
    test_fonts_list = [
        ('/System/Library/Fonts/Supplemental/Times New Roman.ttf', 'Times New Roman'),
        ('/System/Library/Fonts/Supplemental/Georgia.ttf', 'Georgia'),
        ('/Library/Fonts/Arial Unicode.ttf', 'Arial Unicode'),
        ('/System/Library/Fonts/Supplemental/Arial.ttf', 'Arial'),
    ]

    # 公司名称区域
    test_text = "HavenVine"
    x, y = 774, 1351
    width, height = 347, 33

    y_offset = 0
    for font_path, font_name in test_fonts_list:
        try:
            font = ImageFont.truetype(font_path, 44)

            # 清除区域
            draw.rectangle([x, y + y_offset, x + width, y + y_offset + height], fill='white')

            # 绘制伪粗体文本
            create_faux_bold_text(draw, f"{test_text} ({font_name})", (x, y + y_offset), font, (36, 36, 36))

            y_offset += 50
        except Exception as e:
            print(f"无法加载 {font_name}: {e}")

    output_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/font_test.png"
    image.save(output_path)
    print(f"字体测试已保存到: {output_path}")

if __name__ == "__main__":
    test_fonts()
