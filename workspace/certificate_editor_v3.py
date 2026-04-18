#!/usr/bin/env python3
"""
公证文件编辑器 v3.0 - 精确匹配原始样式
- 轻量级伪粗体（只用2-3层）
- 支持 Tracking（字间距）
- 精确的颜色匹配
"""
import sys
import os
from datetime import datetime
from psd_tools import PSDImage
from PIL import Image, ImageDraw, ImageFont
try:
    import img2pdf
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

class PreciseCertificateEditor:
    def __init__(self):
        self.workspace = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace"
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

    def draw_text_with_tracking(self, draw, text, position, font, color, tracking=0):
        """
        绘制带字间距的文本
        tracking: 字间距（单位：千分之一em）
        """
        x, y = position

        if tracking == 0:
            # 无字间距，使用轻量伪粗体
            self.draw_light_faux_bold(draw, text, (x, y), font, color)
        else:
            # 有字间距，逐字符绘制
            current_x = x
            for char in text:
                self.draw_light_faux_bold(draw, char, (current_x, y), font, color)
                # 计算字符宽度 + tracking
                bbox = font.getbbox(char)
                char_width = bbox[2] - bbox[0]
                # tracking 是千分之一em，需要转换
                tracking_px = (tracking / 1000.0) * font.size
                current_x += char_width + tracking_px

    def draw_light_faux_bold(self, draw, text, position, font, color):
        """
        轻量级伪粗体 - 只用2-3层，更接近原始效果
        """
        x, y = position

        # 只使用3个偏移，避免太黑
        offsets = [
            (0, 0),
            (0.5, 0),
            (0, 0.5)
        ]

        for offset_x, offset_y in offsets:
            draw.text((x + offset_x, y + offset_y), text, font=font, fill=color)

    def get_text_width_with_tracking(self, text, font, tracking=0):
        """计算带字间距的文本宽度"""
        if tracking == 0:
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0]

        total_width = 0
        for char in text:
            bbox = font.getbbox(char)
            char_width = bbox[2] - bbox[0]
            tracking_px = (tracking / 1000.0) * font.size
            total_width += char_width + tracking_px

        return total_width - (tracking / 1000.0) * font.size  # 最后一个字符不加tracking

    def auto_fit_font(self, text, font_path, original_size, max_width, tracking=0):
        """自动调整字体大小"""
        font = ImageFont.truetype(font_path, original_size)
        text_width = self.get_text_width_with_tracking(text, font, tracking)

        if text_width <= max_width:
            return font, original_size

        scale = max_width / text_width
        new_size = int(original_size * scale * 0.95)
        print(f"      ⚠️  文本过长，字号从 {original_size} 调整为 {new_size}")
        return ImageFont.truetype(font_path, new_size), new_size

    def edit_certificate(self, psd_path, company_name, address, date, output_path=None, output_format='png'):
        """编辑公证文件"""
        print(f"\n{'='*60}")
        print(f"  公证文件编辑工具 v3.0 (精确版)")
        print(f"{'='*60}")
        print(f"📄 源文件: {os.path.basename(psd_path)}")
        print(f"🏢 公司名称: {company_name}")
        print(f"📍 公司地址: {address}")
        print(f"📅 日期: {date} → {self.format_date(date)}")
        print(f"{'='*60}\n")

        print("⏳ 正在加载 PSD 文件...")
        psd = PSDImage.open(psd_path)

        print("⏳ 正在渲染图层...")
        image = psd.composite()
        draw = ImageDraw.Draw(image)

        # 定义需要修改的图层（根据实际分析结果）
        layers_to_edit = [
            {
                'name': '公司名称',
                'bbox': (774, 1351, 774 + 347, 1351 + 33),
                'new_text': company_name,
                'font_size': 44,
                'color': (35, 35, 35),  # 精确颜色
                'tracking': 0,
                'auto_fit': True,
                'max_width': 347
            },
            {
                'name': '公司地址',
                'bbox': (611, 1507, 611 + 610, 1507 + 35),
                'new_text': address,
                'font_size': 47,
                'color': (25, 25, 25),  # 更深的颜色
                'tracking': 33,  # 重要：地址有字间距
                'auto_fit': True,
                'max_width': 610
            },
            {
                'name': '资本存款时间',
                'bbox': (605, 2563, 605 + 267, 2563 + 33),
                'new_text': self.format_date(date),
                'font_size': 44,
                'color': (35, 35, 35),
                'tracking': 45,  # 重要：日期有字间距
                'auto_fit': True,
                'max_width': 267
            },
            {
                'name': '落款时间',
                'bbox': (315, 2876, 315 + 321, 2876 + 33),
                'new_text': f"Le {self.format_date(date)}.",
                'font_size': 44,
                'color': (35, 35, 35),
                'tracking': 0,
                'auto_fit': True,
                'max_width': 321
            }
        ]

        print("✏️  正在修改文本图层...")

        for layer_info in layers_to_edit:
            print(f"   • {layer_info['name']}: {layer_info['new_text']}")

            # 加载字体
            font_size = layer_info['font_size']
            tracking = layer_info['tracking']

            if layer_info.get('auto_fit', False):
                font, font_size = self.auto_fit_font(
                    layer_info['new_text'],
                    self.font_path,
                    layer_info['font_size'],
                    layer_info['max_width'],
                    tracking
                )
            else:
                font = ImageFont.truetype(self.font_path, font_size)

            # 清除原文本区域
            x1, y1, x2, y2 = layer_info['bbox']
            padding = 5
            draw.rectangle(
                [x1 - padding, y1 - padding, x2 + padding, y2 + padding],
                fill='white'
            )

            # 绘制新文本（带字间距）
            self.draw_text_with_tracking(
                draw,
                layer_info['new_text'],
                (x1, y1),
                font,
                layer_info['color'],
                tracking
            )

        # 保存结果
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(psd_path))[0]
            safe_company_name = company_name.replace(' ', '_').replace('/', '_')
            ext = 'pdf' if output_format.lower() == 'pdf' else 'png'
            output_path = os.path.join(self.workspace, f"{base_name}_{safe_company_name}_v3.{ext}")

        print(f"\n💾 正在保存文件...")

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
    editor = PreciseCertificateEditor()

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
        print("用法: python3 certificate_editor_v3.py <psd文件> <公司名> <地址> <日期> [格式] [输出路径]")
        sys.exit(1)

if __name__ == "__main__":
    main()
