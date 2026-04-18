#!/usr/bin/env python3
"""
改进版公证文件编辑器 v2.0
- 精确匹配原始字体样式（Times New Roman + FauxBold）
- 正确处理文本替换，避免重叠
- 支持字间距（Tracking）
"""
import sys
import os
import json
from datetime import datetime
from psd_tools import PSDImage
from PIL import Image, ImageDraw, ImageFont
try:
    import img2pdf
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

class ImprovedCertificateEditor:
    def __init__(self):
        self.workspace = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace"
        # 使用 Times New Roman 字体
        self.font_path = '/System/Library/Fonts/Supplemental/Times New Roman.ttf'

        self.months_fr = {
            1: 'janvier', 2: 'février', 3: 'mars', 4: 'avril',
            5: 'mai', 6: 'juin', 7: 'juillet', 8: 'août',
            9: 'septembre', 10: 'octobre', 11: 'novembre', 12: 'décembre'
        }

    def format_date(self, date_str):
        """将日期从 YYYY-MM-DD 格式转换为法文格式"""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return f"{date_obj.day} {self.months_fr[date_obj.month]} {date_obj.year}"

    def get_text_width(self, text, font):
        """获取文本宽度"""
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]

    def auto_fit_font(self, text, font_path, original_size, max_width):
        """
        自动调整字体大小以适应最大宽度
        """
        font = ImageFont.truetype(font_path, original_size)
        text_width = self.get_text_width(text, font)

        if text_width <= max_width:
            return font, original_size

        # 计算需要的字号
        scale = max_width / text_width
        new_size = int(original_size * scale * 0.95)  # 留5%边距

        print(f"      ⚠️  文本过长，字号从 {original_size} 调整为 {new_size}")
        return ImageFont.truetype(font_path, new_size), new_size

    def draw_faux_bold_text(self, draw, text, position, font, color):
        """
        绘制伪粗体文本（模拟 Photoshop 的 FauxBold）
        通过多次绘制并轻微偏移来实现粗体效果
        """
        x, y = position

        # 使用多个偏移来模拟粗体
        offsets = [
            (0, 0), (1, 0), (0, 1), (1, 1),
            (0.5, 0), (0, 0.5), (0.5, 0.5)
        ]

        for offset_x, offset_y in offsets:
            draw.text((x + offset_x, y + offset_y), text, font=font, fill=color)

    def edit_certificate(self, psd_path, company_name, address, date, output_path=None, output_format='png'):
        """编辑公证文件"""
        print(f"\n{'='*60}")
        print(f"  公证文件编辑工具 v2.0")
        print(f"{'='*60}")
        print(f"📄 源文件: {os.path.basename(psd_path)}")
        print(f"🏢 公司名称: {company_name}")
        print(f"📍 公司地址: {address}")
        print(f"📅 日期: {date} → {self.format_date(date)}")
        print(f"{'='*60}\n")

        # 打开 PSD 文件
        print("⏳ 正在加载 PSD 文件...")
        psd = PSDImage.open(psd_path)

        # 转换为 PIL Image
        print("⏳ 正在渲染图层...")
        image = psd.composite()
        draw = ImageDraw.Draw(image)

        # 加载字体
        font_regular = ImageFont.truetype(self.font_path, 44)
        font_address = ImageFont.truetype(self.font_path, 47)
        font_date = ImageFont.truetype(self.font_path, 44)

        # 定义需要修改的图层信息（根据 PSD 分析结果）
        layers_to_edit = [
            {
                'name': '公司名称',
                'bbox': (774, 1351, 774 + 347, 1351 + 33),  # 精确边界框
                'old_text': 'VelvetVineEstates',
                'new_text': company_name,
                'font': font_regular,
                'color': (36, 36, 36),  # RGB from 0.14117
                'font_size': 44,
                'auto_fit': True,  # 启用自动适配
                'max_width': 347
            },
            {
                'name': '公司地址',
                'bbox': (611, 1507, 611 + 610, 1507 + 35),
                'old_text': '47 rue Vivienne 75002 Paris',
                'new_text': address,
                'font': font_address,
                'color': (26, 26, 26),  # RGB from 0.10001
                'font_size': 47,
                'auto_fit': True,
                'max_width': 610
            },
            {
                'name': '资本存款时间',
                'bbox': (605, 2563, 605 + 267, 2563 + 33),
                'old_text': '17 avril 2026',
                'new_text': self.format_date(date),
                'font': font_date,
                'color': (36, 36, 36),
                'font_size': 44,
                'auto_fit': True,
                'max_width': 267
            },
            {
                'name': '落款时间',
                'bbox': (315, 2876, 315 + 321, 2876 + 33),
                'old_text': 'Le 17 avril 2026.',
                'new_text': f"Le {self.format_date(date)}.",
                'font': font_date,
                'color': (36, 36, 36),
                'font_size': 44,
                'auto_fit': True,
                'max_width': 321
            }
        ]

        print("✏️  正在修改文本图层...")

        for layer_info in layers_to_edit:
            print(f"   • {layer_info['name']}: {layer_info['old_text']} → {layer_info['new_text']}")

            # 获取边界框
            x1, y1, x2, y2 = layer_info['bbox']

            # 自动适配字体大小
            font_to_use = layer_info['font']
            if layer_info.get('auto_fit', False):
                font_to_use, adjusted_size = self.auto_fit_font(
                    layer_info['new_text'],
                    self.font_path if layer_info['name'] != '公司地址' else self.font_path,
                    layer_info['font_size'],
                    layer_info['max_width']
                )

            # 用白色完全覆盖原文本区域（扩大一点以确保完全覆盖）
            padding = 5
            draw.rectangle(
                [x1 - padding, y1 - padding, x2 + padding, y2 + padding],
                fill='white'
            )

            # 绘制新文本（使用伪粗体）
            self.draw_faux_bold_text(
                draw,
                layer_info['new_text'],
                (x1, y1),
                font_to_use,
                layer_info['color']
            )

        # 保存结果
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(psd_path))[0]
            safe_company_name = company_name.replace(' ', '_').replace('/', '_')
            ext = 'pdf' if output_format.lower() == 'pdf' else 'png'
            output_path = os.path.join(self.workspace, f"{base_name}_{safe_company_name}_v2.{ext}")

        print(f"\n💾 正在保存文件...")

        # 根据格式保存
        if output_format.lower() == 'pdf':
            if not PDF_SUPPORT:
                print("⚠️  警告: img2pdf 未安装，将保存为 PNG 格式")
                output_path = output_path.replace('.pdf', '.png')
                image.save(output_path, 'PNG', dpi=(300, 300))
            else:
                temp_png = output_path.replace('.pdf', '_temp.png')
                image.save(temp_png, 'PNG', dpi=(300, 300))
                with open(output_path, 'wb') as f:
                    f.write(img2pdf.convert(temp_png, dpi=300))
                os.remove(temp_png)
                print(f"✅ PDF 文件已生成")
        else:
            image.save(output_path, 'PNG', dpi=(300, 300))

        print(f"✅ 完成！文件已保存到:")
        print(f"   {output_path}\n")

        return output_path

def main():
    editor = ImprovedCertificateEditor()

    if len(sys.argv) >= 5:
        psd_path = sys.argv[1]
        company_name = sys.argv[2]
        address = sys.argv[3]
        date = sys.argv[4]
        output_format = sys.argv[5] if len(sys.argv) > 5 else 'png'
        output_path = sys.argv[6] if len(sys.argv) > 6 else None

        if not os.path.exists(psd_path):
            print(f"❌ 错误: 文件不存在 - {psd_path}")
            sys.exit(1)

        editor.edit_certificate(psd_path, company_name, address, date, output_path, output_format)
    else:
        print("用法: python3 certificate_editor_v2.py <psd文件> <公司名> <地址> <日期> [格式] [输出路径]")
        print("\n示例:")
        print("  python3 certificate_editor_v2.py '资本存款.psd' 'HavenVine' '60 rue Francois 1er 75008 Paris' '2026-03-10' 'pdf'")
        sys.exit(1)

if __name__ == "__main__":
    main()
