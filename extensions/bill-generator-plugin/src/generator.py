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

        # Step 1: Redact old text - use redaction to completely remove text
        for change in changes:
            rect = fitz.Rect(change.bbox)
            # 扩大redaction区域，确保完全删除原文本
            rect.x0 -= 0.5
            rect.y0 -= 0.5
            rect.x1 += 0.5
            rect.y1 += 0.5
            # 使用 redaction 标记要删除的区域
            page.add_redact_annot(rect)

        # 应用所有 redaction（彻底删除文本，保留背景色）
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

        # Step 2: Register fonts AFTER redaction
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

        # Step 2: Insert new text with correct fonts
        for change in changes:
            # 判断内容类型
            text = change.new_value
            is_pure_number_or_date = all(c.isdigit() or c in '-./' for c in text)
            # 检查是否包含货币符号的金额（如￥503.69）
            is_currency_amount = '￥' in text and any(c.isdigit() for c in text)
            # 检查是否是电表编号字段（检查文本内容而不是字段名）
            is_meter_number = '电能表编号' in text

            # 账单周期字段的字体大小增加1.5个点
            font_size = change.font_size
            if any(keyword in change.field_name for keyword in ['账单周期']):
                font_size += 1.5

            # 户名、用电地址使用微软雅黑
            if '户名' in change.field_name or '用电地址' in change.field_name:
                fontname = 'msyh' if msyh_registered else 'china-s'
            # 账单周期、账单打印日期使用华文仿宋（排除电价地区和抄表日期）
            elif any(keyword in change.field_name for keyword in ['账单周期', '账单打印日期']):
                fontname = 'fangsong' if fangsong_registered else 'china-s'
            # 纯数字、日期使用helv（数字间距正常）
            elif is_pure_number_or_date:
                fontname = 'helv'
            # 其他中文内容使用china-s（包括电价地区）
            else:
                fontname = 'china-s'

            # 计算插入位置
            x_pos = change.bbox[0]
            y_pos = change.bbox[3]

            # 电表编号需要特殊处理：数字部分用helv，其他用china-s
            if is_meter_number:
                import re
                # 匹配格式："电能表编号：[22位数字]，电价：..." (支持半角和全角逗号)
                match = re.match(r'(电能表编号：)(\d{22})([,，]电价：.+)', text)
                if match:
                    prefix = match.group(1)
                    number = match.group(2)
                    suffix = match.group(3)

                    # 计算原始文本的总宽度
                    original_width = change.bbox[2] - change.bbox[0]

                    # 计算前缀理论宽度
                    prefix_theoretical = fitz.get_text_length(prefix, fontname='china-s', fontsize=font_size)
                    # 计算数字理论宽度
                    number_theoretical = fitz.get_text_length(number, fontname='helv', fontsize=font_size)

                    # 计算后缀各段的理论宽度
                    suffix_segments = re.split(r'(\d+)', suffix)
                    suffix_theoretical = sum(
                        fitz.get_text_length(seg, fontname='helv' if seg.isdigit() else 'china-s', fontsize=font_size)
                        for seg in suffix_segments if seg
                    )

                    # 计算总理论宽度和缩放比例
                    total_theoretical = prefix_theoretical + number_theoretical + suffix_theoretical
                    scale = original_width / total_theoretical if total_theoretical > 0 else 1.0

                    # 插入前缀
                    page.insert_text((x_pos, y_pos), prefix, fontname='china-s', fontsize=font_size, color=change.color)
                    current_x = x_pos + prefix_theoretical * scale

                    # 插入数字
                    page.insert_text((current_x, y_pos), number, fontname='helv', fontsize=font_size, color=change.color)
                    current_x += number_theoretical * scale

                    # 插入后缀各段
                    for segment in suffix_segments:
                        if not segment:
                            continue
                        fontname_seg = 'helv' if segment.isdigit() else 'china-s'
                        page.insert_text((current_x, y_pos), segment, fontname=fontname_seg, fontsize=font_size, color=change.color)
                        seg_width = fitz.get_text_length(segment, fontname=fontname_seg, fontsize=font_size)
                        current_x += seg_width * scale
                else:
                    # 如果格式不匹配，直接插入
                    page.insert_text((x_pos, y_pos), text, fontname='china-s', fontsize=font_size, color=change.color)
            # 电价地区字段包含数字时，需要分段渲染
            elif '电价地区' in change.field_name and any(c.isdigit() for c in text):
                import re
                # 将文本分段：中文、数字、中文...
                segments = re.split(r'(\d+)', text)

                # 计算原始文本的总宽度
                original_width = change.bbox[2] - change.bbox[0]
                # 计算所有段的理论宽度总和
                total_theoretical_width = sum(
                    fitz.get_text_length(seg, fontname='helv' if seg.isdigit() else 'china-s', fontsize=font_size)
                    for seg in segments if seg
                )
                # 计算缩放比例，使新文本适应原始宽度
                scale = original_width / total_theoretical_width if total_theoretical_width > 0 else 1.0

                current_x = x_pos
                for segment in segments:
                    if not segment:
                        continue
                    if segment.isdigit():
                        fontname_seg = 'helv'
                    else:
                        fontname_seg = 'china-s'

                    page.insert_text(
                        (current_x, y_pos),
                        segment,
                        fontname=fontname_seg,
                        fontsize=font_size,
                        color=change.color
                    )
                    # 使用缩放后的宽度
                    text_width = fitz.get_text_length(segment, fontname=fontname_seg, fontsize=font_size)
                    current_x += text_width * scale
            # 货币金额需要特殊处理：分开插入￥和数字
            elif is_currency_amount:
                # 提取￥符号和数字部分
                amount_text = text.replace('￥', '')

                # 合计金额需要居中对齐
                if '合计' in change.field_name:
                    # 计算列的中心位置
                    column_center = (change.bbox[0] + change.bbox[2]) / 2
                    # 估算文本宽度（￥用china-s约5.2点，数字用helv约4.5点/字符）
                    yuan_width = 5.2
                    number_width = len(amount_text) * 4.5
                    total_width = yuan_width + number_width
                    # 居中起始位置
                    x_pos = column_center - total_width / 2

                # 先插入￥符号（使用china-s）
                page.insert_text(
                    (x_pos, y_pos),
                    '￥',
                    fontname='china-s',
                    fontsize=font_size,
                    color=change.color
                )

                # 再插入数字（使用helv，留半个字符的间距）
                page.insert_text(
                    (x_pos + 7.5, y_pos),  # ￥符号宽度约5.2点，加2.3点间距（半个字符）
                    amount_text,
                    fontname='helv',
                    fontsize=font_size,
                    color=change.color
                )
            else:
                # 普通文本直接插入
                page.insert_text(
                    (x_pos, y_pos),
                    change.new_value,
                    fontname=fontname,
                    fontsize=font_size,
                    color=change.color
                )

        # 应用字体子集化（只保留实际使用的字符）
        doc.subset_fonts(verbose=False, fallback=False)

        # 保存时启用压缩和优化
        doc.save(output_path, garbage=4, deflate=True, clean=True)
        doc.close()

        # 报告文件大小
        file_size = os.path.getsize(output_path)
        file_size_mb = file_size / (1024 * 1024)
        print(f"  ✓ PDF已生成: {file_size_mb:.2f} MB")

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
