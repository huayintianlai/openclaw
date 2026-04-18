#!/usr/bin/env python3
"""
PDF重建器 - 使用ReportLab重新生成PDF
"""
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color
import os


class PDFRebuilder:
    """使用ReportLab重建PDF"""

    def __init__(self):
        self.font_mapping = {}
        self._register_fonts()

    def _register_fonts(self):
        """注册中文和法语字体"""
        # macOS系统字体路径
        font_paths = {
            "STSong": "/System/Library/Fonts/Supplemental/Songti.ttc",
            "STHeiti": "/System/Library/Fonts/STHeiti Light.ttc",
            "PingFang": "/System/Library/Fonts/PingFang.ttc",
            "SimSun": "/System/Library/Fonts/Supplemental/Songti.ttc",
        }

        for font_name, font_path in font_paths.items():
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    self.font_mapping[font_name] = font_name
                    print(f"  ✓ 已注册字体: {font_name}")
                except Exception as e:
                    print(f"  警告: 无法注册字体 {font_name}: {e}")

        # 为常见中文字体名称创建映射
        chinese_fonts = ["SimSun", "STSong", "STHeiti", "MicrosoftYaHei", "NSimSun"]
        for cf in chinese_fonts:
            if cf not in self.font_mapping:
                # 使用已注册的字体作为后备
                if "STSong" in self.font_mapping:
                    self.font_mapping[cf] = "STSong"
                elif "STHeiti" in self.font_mapping:
                    self.font_mapping[cf] = "STHeiti"
                else:
                    self.font_mapping[cf] = "Helvetica"

    def rebuild(self, structure, output_path):
        """
        根据结构重建PDF

        Args:
            structure: 从PDFParser获取的结构数据
            output_path: 输出PDF路径
        """
        page_size = structure["page_size"]
        c = canvas.Canvas(output_path, pagesize=page_size)

        page_height = page_size[1]

        # 按照Z-order排序：先绘制背景元素，再绘制前景元素
        # 顺序：矩形（背景） -> 图像 -> 线条 -> 文本（前景）
        rects = [e for e in structure["elements"] if e["type"] == "rect"]
        images = [e for e in structure["elements"] if e["type"] == "image"]
        lines = [e for e in structure["elements"] if e["type"] == "line"]
        texts = [e for e in structure["elements"] if e["type"] == "text"]

        # 1. 绘制矩形（背景色块）
        for rect in rects:
            self._draw_rect(c, rect, page_height)

        # 2. 绘制图像
        for image in images:
            self._draw_image(c, image, page_height)

        # 3. 绘制线条
        for line in lines:
            self._draw_line(c, line, page_height)

        # 4. 绘制文本（最上层）
        for text in texts:
            self._draw_text(c, text, page_height)

        c.save()

    def _draw_text(self, c, element, page_height):
        """绘制文本元素"""
        # 使用PyMuPDF提供的origin（基线位置）
        origin = element.get("origin")

        if origin:
            # origin是(x, y)，其中y是基线位置
            x = origin[0]
            y = page_height - origin[1]  # 坐标系转换
        else:
            # 如果没有origin，使用bbox计算
            x0, y0, x1, y1 = element["bbox"]
            x = x0
            font_size = element["font_size"]
            y = page_height - y1

        # 字体处理
        font_name = element["font"]
        font_size = element["font_size"]

        # 检测文本内容，选择合适的字体
        content = element["content"]
        has_chinese = any('\u4e00' <= c <= '\u9fff' for c in content)
        has_french = any(c in 'àâäæçéèêëïîôùûüÿœÀÂÄÆÇÉÈÊËÏÎÔÙÛÜŸŒ' for c in content)

        # 优先使用原字体
        if font_name in self.font_mapping:
            font_name = self.font_mapping[font_name]
        else:
            # 根据内容选择字体
            if has_chinese:
                # 中文使用中文字体
                font_name = self.font_mapping.get("SimSun", "STSong")
            elif has_french or not has_chinese:
                # 法语或英文使用Helvetica（支持法语特殊字符）
                font_name = "Helvetica"
            else:
                font_name = "Helvetica"

        try:
            c.setFont(font_name, font_size)
        except Exception as e:
            # 字体设置失败，使用默认字体
            c.setFont("Helvetica", font_size)

        # 颜色处理
        color = element["color"]
        if color:
            c.setFillColorRGB(*color)

        # 绘制文本
        # 注意：PyMuPDF的origin已经是正确的位置，直接使用
        try:
            c.drawString(x, y, content)
        except Exception as e:
            print(f"  警告: 无法绘制文本 '{content[:20]}...': {e}")

    def _draw_rect(self, c, element, page_height):
        """绘制矩形元素"""
        x0, y0, x1, y1 = element["bbox"]
        # 坐标转换
        x = x0
        y = page_height - y1
        width = x1 - x0
        height = y1 - y0

        # 填充颜色
        fill_color = element.get("fill_color")
        if fill_color:
            c.setFillColorRGB(*fill_color)

        # 边框颜色
        stroke_color = element.get("stroke_color")
        if stroke_color:
            c.setStrokeColorRGB(*stroke_color)

        stroke_width = element.get("stroke_width", 1)
        c.setLineWidth(stroke_width)

        # 绘制矩形
        fill = 1 if fill_color else 0
        stroke = 1 if stroke_color else 0

        c.rect(x, y, width, height, fill=fill, stroke=stroke)

    def _draw_line(self, c, element, page_height):
        """绘制线条元素"""
        start = element["start"]
        end = element["end"]

        # 坐标转换
        x1 = start[0]
        y1 = page_height - start[1]
        x2 = end[0]
        y2 = page_height - end[1]

        # 颜色
        color = element.get("color")
        if color:
            c.setStrokeColorRGB(*color)

        width = element.get("width", 1)
        c.setLineWidth(width)

        c.line(x1, y1, x2, y2)

    def _draw_image(self, c, element, page_height):
        """绘制图像元素"""
        from io import BytesIO
        from PIL import Image

        x0, y0, x1, y1 = element["bbox"]
        # 坐标转换
        x = x0
        y = page_height - y1
        width = x1 - x0
        height = y1 - y0

        try:
            # 从字节数据创建图像
            image_data = element["image_data"]
            image_stream = BytesIO(image_data)

            # 使用PIL处理图像
            pil_img = Image.open(image_stream)

            # 转换为RGB模式（去除透明通道，避免ReportLab问题）
            if pil_img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                rgb_img = Image.new('RGB', pil_img.size, (255, 255, 255))
                if pil_img.mode == 'RGBA':
                    rgb_img.paste(pil_img, mask=pil_img.split()[3])  # 使用alpha通道作为mask
                else:
                    rgb_img.paste(pil_img)
                pil_img = rgb_img

            # 保存为JPEG（更兼容）
            output_stream = BytesIO()
            pil_img.save(output_stream, format='JPEG', quality=95)
            output_stream.seek(0)

            from reportlab.lib.utils import ImageReader
            img = ImageReader(output_stream)

            # 绘制图像
            c.drawImage(img, x, y, width=width, height=height)
        except Exception as e:
            print(f"  警告: 无法绘制图像 @ {element['bbox']}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    # 测试重建
    from pdf_parser import PDFParser

    parser = PDFParser()
    test_pdf = "/Users/xiaojiujiu2/Downloads/电费账单-陈天浩-20260417_100903.pdf"

    print("正在解析PDF...")
    structure = parser.parse(test_pdf)

    print("正在重建PDF...")
    rebuilder = PDFRebuilder()
    output_pdf = "/Users/xiaojiujiu2/Downloads/测试-ReportLab重建.pdf"
    rebuilder.rebuild(structure, output_pdf)

    print(f"✓ PDF重建完成: {output_pdf}")
