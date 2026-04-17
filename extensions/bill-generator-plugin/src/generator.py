"""PDF Generator - Direct text overlay without white rectangles"""
from dataclasses import dataclass
from typing import Tuple
import fitz
import os

@dataclass
class FieldChange:
    field_name: str
    original_value: str
    new_value: str
    bbox: Tuple[float, float, float, float]
    font: str
    font_size: float
    color: Tuple[float, float, float]

class PDFGenerator:
    def __init__(self):
        # Extract fonts from the 36MB correct version
        self.font_path_msyh = '/tmp/MicrosoftYaHei.ttf'
        self.font_path_simsun = '/tmp/SimSun.ttf'
        self.font_path_heiti = '/tmp/HeitiTC.ttf'
        self.font_path_fangsong = '/Users/xiaojiujiu2/Library/Fonts/华文仿宋.ttf'
        self._ensure_fonts_extracted()

    def _ensure_fonts_extracted(self):
        """Extract fonts from 36MB PDF if not already done"""
        source_pdf = '/Users/xiaojiujiu2/Downloads/电费账单-陈天浩-20260416_234818.pdf'

        if not os.path.exists(source_pdf):
            return

        try:
            doc = fitz.open(source_pdf)
            fonts = doc.get_page_fonts(0)

            for font in fonts:
                font_name = font[3]
                font_buffer = doc.extract_font(font[0])

                if not font_buffer:
                    continue

                # Extract Microsoft YaHei
                if 'Microsoft' in font_name and not os.path.exists(self.font_path_msyh):
                    with open(self.font_path_msyh, 'wb') as f:
                        f.write(font_buffer[3])

                # Extract SimSun
                if 'SimSun' in font_name and not os.path.exists(self.font_path_simsun):
                    with open(self.font_path_simsun, 'wb') as f:
                        f.write(font_buffer[3])

                # Extract Heiti TC
                if 'Heiti' in font_name and not os.path.exists(self.font_path_heiti):
                    with open(self.font_path_heiti, 'wb') as f:
                        f.write(font_buffer[3])

            doc.close()
        except:
            pass

    def apply_changes(self, template_path: str, changes: list, output_path: str):
        """Apply changes - use redaction to remove old text, then add new text"""
        doc = fitz.open(template_path)
        page = doc[0]

        # Register Microsoft YaHei font
        msyh_registered = False
        if os.path.exists(self.font_path_msyh):
            try:
                fontbuffer = open(self.font_path_msyh, 'rb').read()
                page.insert_font(fontbuffer=fontbuffer, fontname='msyh')
                msyh_registered = True
            except:
                pass

        # Register Heiti TC font
        heiti_registered = False
        if os.path.exists(self.font_path_heiti):
            try:
                fontbuffer = open(self.font_path_heiti, 'rb').read()
                page.insert_font(fontbuffer=fontbuffer, fontname='heiti')
                heiti_registered = True
            except:
                pass

        # Register STFangsong font
        fangsong_registered = False
        if os.path.exists(self.font_path_fangsong):
            try:
                fontbuffer = open(self.font_path_fangsong, 'rb').read()
                page.insert_font(fontbuffer=fontbuffer, fontname='fangsong')
                fangsong_registered = True
            except:
                pass

        # Step 1: Redact old text - use transparent background
        for change in changes:
            rect = fitz.Rect(change.bbox)
            page.add_redact_annot(rect)
        page.apply_redactions()

        # Step 2: Re-register Microsoft YaHei after redaction
        if msyh_registered:
            try:
                fontbuffer = open(self.font_path_msyh, 'rb').read()
                page.insert_font(fontbuffer=fontbuffer, fontname='msyh')
            except:
                msyh_registered = False

        # Re-register Heiti TC after redaction
        if heiti_registered:
            try:
                fontbuffer = open(self.font_path_heiti, 'rb').read()
                page.insert_font(fontbuffer=fontbuffer, fontname='heiti')
            except:
                heiti_registered = False

        # Re-register STFangsong after redaction
        if fangsong_registered:
            try:
                fontbuffer = open(self.font_path_fangsong, 'rb').read()
                page.insert_font(fontbuffer=fontbuffer, fontname='fangsong')
            except:
                fangsong_registered = False

        # Step 3: Insert new text with correct fonts
        for change in changes:
            # 判断内容类型
            text = change.new_value
            is_pure_number_or_date = all(c.isdigit() or c in '-./' for c in text)

            # 户名、用电地址使用微软雅黑
            if '户名' in change.field_name or '用电地址' in change.field_name:
                fontname = 'msyh' if msyh_registered else 'china-s'
            # 电价地区、账单周期、账单打印日期、抄表日期使用华文仿宋
            elif any(keyword in change.field_name for keyword in ['电价地区', '电价', '账单周期', '账单打印日期', '抄表日期', '抄表时间']):
                fontname = 'fangsong' if fangsong_registered else 'china-s'
            # 纯数字和日期使用helv（数字间距正常）
            elif is_pure_number_or_date:
                fontname = 'helv'
            # 其他中文内容使用china-s
            else:
                fontname = 'china-s'

            page.insert_text(
                (change.bbox[0], change.bbox[3]),
                change.new_value,
                fontname=fontname,
                fontsize=change.font_size,
                color=change.color
            )

        # Save without optimization
        doc.save(output_path)
        doc.close()

    def create_comparison_image(self, template_path: str, output_path: str, comparison_path: str):
        from PIL import Image
        doc1 = fitz.open(template_path)
        doc2 = fitz.open(output_path)
        pix1 = doc1[0].get_pixmap(dpi=150)
        pix2 = doc2[0].get_pixmap(dpi=150)
        img1 = Image.frombytes("RGB", [pix1.width, pix1.height], pix1.samples)
        img2 = Image.frombytes("RGB", [pix2.width, pix2.height], pix2.samples)
        width = img1.width + img2.width + 20
        height = max(img1.height, img2.height)
        comparison = Image.new('RGB', (width, height), 'white')
        comparison.paste(img1, (0, 0))
        comparison.paste(img2, (img1.width + 20, 0))
        comparison.save(comparison_path, 'PNG', optimize=True)
        doc1.close()
        doc2.close()
