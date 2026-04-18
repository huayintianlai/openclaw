#!/usr/bin/env python3
"""
PSD 文件编辑器 - 修改法国公证文件中的公司信息
"""
import sys
import os
from psd_tools import PSDImage
from PIL import Image, ImageDraw, ImageFont

def edit_certificate(psd_path, company_name, address, date, output_path=None):
    """
    编辑公证文件

    Args:
        psd_path: PSD 文件路径
        company_name: 公司名称
        address: 公司地址
        date: 日期（格式：YYYY-MM-DD）
    """
    print(f"正在处理: {psd_path}")
    print(f"公司名称: {company_name}")
    print(f"公司地址: {address}")
    print(f"日期: {date}\n")

    # 打开 PSD 文件
    psd = PSDImage.open(psd_path)

    # 转换为 PIL Image
    print("正在渲染 PSD 文件...")
    image = psd.composite()

    # 创建绘图对象
    draw = ImageDraw.Draw(image)

    # 加载字体 - 使用系统字体
    font_regular = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', 44)
    font_address = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Unicode.ttf', 47)

    # 定义需要修改的图层信息（从分析结果获取）
    layers_to_edit = {
        '公司名称': {
            'position': (774, 1351),
            'old_text': 'VelvetVineEstates',
            'new_text': company_name,
            'font': font_regular,
            'color': (36, 36, 36)  # RGB from 0.14117
        },
        '公司地址': {
            'position': (611, 1507),
            'old_text': '47 rue Vivienne 75002 Paris',
            'new_text': address,
            'font': font_address,
            'color': (26, 26, 26)  # RGB from 0.10001
        },
        '资本存款时间': {
            'position': (605, 2563),
            'old_text': '17 avril 2026',
            'new_text': format_date(date),
            'font': font_regular,
            'color': (36, 36, 36)
        },
        '落款时间': {
            'position': (315, 2876),
            'old_text': 'Le 17 avril 2026.',
            'new_text': f"Le {format_date(date)}.",
            'font': font_regular,
            'color': (36, 36, 36)
        }
    }

    print("正在修改文本图层...")

    # 遍历所有图层，找到文本图层并覆盖
    for layer_name, info in layers_to_edit.items():
        print(f"  - 修改 {layer_name}: {info['old_text']} -> {info['new_text']}")

        # 查找对应的图层
        for layer in psd.descendants():
            if layer.kind == 'type' and hasattr(layer, 'text'):
                if info['old_text'] in layer.text:
                    # 获取图层位置和尺寸
                    x, y = layer.left, layer.top
                    width, height = layer.width, layer.height

                    # 用白色矩形覆盖原文本
                    draw.rectangle([x, y, x + width, y + height], fill='white')

                    # 绘制新文本
                    draw.text((x, y), info['new_text'], font=info['font'], fill=info['color'])
                    break

    # 保存结果
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(psd_path))[0]
        output_path = f"/Volumes/KenDisk/Coding/openclaw-runtime/workspace/{base_name}_{company_name.replace(' ', '_')}.png"

    print(f"\n正在保存到: {output_path}")
    image.save(output_path, 'PNG', dpi=(300, 300))

    print(f"✓ 完成！文件已保存")
    return output_path

def format_date(date_str):
    """
    将日期从 YYYY-MM-DD 格式转换为法文格式
    例如: 2026-03-10 -> 10 mars 2026
    """
    from datetime import datetime

    months_fr = {
        1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril',
        5: 'mai', 6: 'juin', 7: 'juillet', 8: 'août',
        9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'
    }

    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    return f"{date_obj.day} {months_fr[date_obj.month]} {date_obj.year}"

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("用法: python3 psd_editor.py <psd文件> <公司名> <地址> <日期YYYY-MM-DD>")
        print("示例: python3 psd_editor.py 资本存款.psd 'HavenVine' '60 rue Francois 1er 75008 Paris' '2026-03-10'")
        sys.exit(1)

    psd_path = sys.argv[1]
    company_name = sys.argv[2]
    address = sys.argv[3]
    date = sys.argv[4]

    edit_certificate(psd_path, company_name, address, date)
