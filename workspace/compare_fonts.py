#!/usr/bin/env python3
"""
字体对比测试 - 找出最接近原文的方案
"""
from psd_tools import PSDImage
from PIL import Image, ImageDraw, ImageFont

psd = PSDImage.open("/Users/xiaojiujiu2/Downloads/资本存款.psd")
image = psd.composite()
draw = ImageDraw.Draw(image)

# 测试区域：公司名称下方
test_y = 1400
test_x = 300

# 测试文本
test_text = "HavenVine SARL"

# 方案1: Times New Roman + 轻量伪粗体（3层）
font1 = ImageFont.truetype('/System/Library/Fonts/Supplemental/Times New Roman.ttf', 44)
draw.text((test_x, test_y), "方案1: Regular + 3层伪粗体", font=font1, fill=(0, 0, 0))
y_offset = test_y + 40
for offset in [(0, 0), (0.5, 0), (0, 0.5)]:
    draw.text((test_x + offset[0], y_offset + offset[1]), test_text, font=font1, fill=(35, 35, 35))

# 方案2: Times New Roman Bold（直接用粗体）
test_y += 100
font2 = ImageFont.truetype('/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf', 44)
draw.text((test_x, test_y), "方案2: Bold 字体", font=font2, fill=(0, 0, 0))
draw.text((test_x, test_y + 40), test_text, font=font2, fill=(35, 35, 35))

# 方案3: Times New Roman + 单层（无伪粗体）
test_y += 100
font3 = ImageFont.truetype('/System/Library/Fonts/Supplemental/Times New Roman.ttf', 44)
draw.text((test_x, test_y), "方案3: Regular 无伪粗体", font=font3, fill=(0, 0, 0))
draw.text((test_x, test_y + 40), test_text, font=font3, fill=(35, 35, 35))

# 方案4: Times New Roman + 2层伪粗体
test_y += 100
font4 = ImageFont.truetype('/System/Library/Fonts/Supplemental/Times New Roman.ttf', 44)
draw.text((test_x, test_y), "方案4: Regular + 2层伪粗体", font=font4, fill=(0, 0, 0))
y_offset = test_y + 40
for offset in [(0, 0), (0.5, 0)]:
    draw.text((test_x + offset[0], y_offset + offset[1]), test_text, font=font4, fill=(35, 35, 35))

# 原文参考（裁剪一部分原文）
test_y += 100
draw.text((test_x, test_y), "原文参考: dénomination sociale de", font=font1, fill=(0, 0, 0))

output_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/font_comparison.png"
image.save(output_path)
print(f"字体对比已保存到: {output_path}")
