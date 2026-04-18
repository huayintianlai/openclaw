#!/usr/bin/env python3
"""
PDF结构解析器 - 提取PDF中的所有元素
"""
import fitz
import re


class PDFParser:
    """解析PDF结构，提取文本、图形等元素"""

    def __init__(self):
        self.chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')

    def parse(self, pdf_path):
        """
        解析PDF，返回结构化数据

        Args:
            pdf_path: PDF文件路径

        Returns:
            dict: {
                "page_size": (width, height),
                "elements": [element1, element2, ...]
            }
        """
        doc = fitz.open(pdf_path)
        page = doc[0]  # 只处理第一页

        elements = []

        # 1. 提取文本元素
        text_elements = self._extract_text_elements(page)
        elements.extend(text_elements)

        # 2. 提取图形元素（矩形、线条）
        drawing_elements = self._extract_drawing_elements(page)
        elements.extend(drawing_elements)

        # 3. 提取图像元素
        image_elements = self._extract_image_elements(page, doc)
        elements.extend(image_elements)

        page_size = (page.rect.width, page.rect.height)

        doc.close()

        return {
            "page_size": page_size,
            "elements": elements
        }

    def _extract_text_elements(self, page):
        """提取文本元素"""
        elements = []
        blocks = page.get_text("dict")["blocks"]

        for block in blocks:
            if "lines" not in block:
                continue

            for line in block["lines"]:
                for span in line["spans"]:
                    # 跳过空白文本
                    if span["text"].strip():
                        # 获取origin（基线位置）
                        origin = span.get("origin", None)
                        elements.append({
                            "type": "text",
                            "content": span["text"],
                            "bbox": tuple(span["bbox"]),
                            "origin": origin,  # 添加基线位置
                            "font": span["font"],
                            "font_size": span["size"],
                            "color": self._parse_color(span["color"]),
                            "flags": span.get("flags", 0)
                        })

        return elements

    def _extract_drawing_elements(self, page):
        """提取图形元素（矩形、线条）"""
        elements = []

        try:
            drawings = page.get_drawings()

            for drawing in drawings:
                dtype = drawing["type"]

                if dtype == "f":  # 填充路径（矩形、多边形等）
                    rect = drawing.get("rect")
                    fill_color = drawing.get("fill")

                    if rect and fill_color:
                        # 过滤掉整页大小的白色背景矩形
                        is_full_page = (rect.width >= page.rect.width * 0.95 and
                                       rect.height >= page.rect.height * 0.95)
                        is_white = (fill_color == (1.0, 1.0, 1.0) or
                                   fill_color == [1.0, 1.0, 1.0])

                        if not (is_full_page and is_white):
                            elements.append({
                                "type": "rect",
                                "bbox": tuple(rect),
                                "fill_color": self._parse_color(fill_color),
                                "stroke_color": None,
                                "stroke_width": 0
                            })

                elif dtype == "re":  # 矩形
                    elements.append({
                        "type": "rect",
                        "bbox": tuple(drawing["rect"]),
                        "fill_color": self._parse_color(drawing.get("fill")),
                        "stroke_color": self._parse_color(drawing.get("color")),
                        "stroke_width": drawing.get("width", 1)
                    })

                elif dtype == "s":  # 描边路径（线条）
                    rect = drawing.get("rect")
                    color = drawing.get("color")
                    width = drawing.get("width", 0.75)

                    if rect and color:
                        # 判断是水平线还是垂直线
                        if rect.width > 1 and rect.height < 1:  # 水平线
                            elements.append({
                                "type": "line",
                                "start": (rect.x0, rect.y0),
                                "end": (rect.x1, rect.y0),
                                "color": self._parse_color(color),
                                "width": width
                            })
                        elif rect.height > 1 and rect.width < 1:  # 垂直线
                            elements.append({
                                "type": "line",
                                "start": (rect.x0, rect.y0),
                                "end": (rect.x0, rect.y1),
                                "color": self._parse_color(color),
                                "width": width
                            })

                elif dtype == "l":  # 线条
                    items = drawing.get("items", [])
                    if items:
                        for item in items:
                            if item[0] == "l":  # line
                                elements.append({
                                    "type": "line",
                                    "start": tuple(item[1]),
                                    "end": tuple(item[2]),
                                    "color": self._parse_color(drawing.get("color")),
                                    "width": drawing.get("width", 1)
                                })

        except Exception as e:
            print(f"  警告: 提取图形元素时出错: {e}")

        return elements

    def _extract_image_elements(self, page, doc):
        """提取图像元素"""
        elements = []

        try:
            images = page.get_images()

            for img_index, img in enumerate(images):
                xref = img[0]

                # 获取图像的位置
                img_rects = page.get_image_rects(xref)

                if img_rects:
                    # 提取图像数据
                    try:
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]

                        # 对于每个图像位置（一个图像可能在多个位置使用）
                        for rect in img_rects:
                            elements.append({
                                "type": "image",
                                "bbox": tuple(rect),
                                "image_data": image_bytes,
                                "image_ext": image_ext,
                                "xref": xref
                            })
                    except Exception as e:
                        print(f"  警告: 无法提取图像 xref={xref}: {e}")

        except Exception as e:
            print(f"  警告: 提取图像元素时出错: {e}")

        return elements

    def _parse_color(self, color):
        """
        解析颜色格式

        Args:
            color: 可能是整数、元组或None

        Returns:
            tuple: (r, g, b) 范围0-1
        """
        if color is None:
            return None

        if isinstance(color, int):
            # 从整数提取RGB分量（格式：0xRRGGBB）
            r = ((color >> 16) & 0xFF) / 255.0
            g = ((color >> 8) & 0xFF) / 255.0
            b = (color & 0xFF) / 255.0
            return (r, g, b)

        elif isinstance(color, (list, tuple)):
            # 已经是RGB格式，确保范围在0-1
            if len(color) >= 3:
                return tuple(c / 255.0 if c > 1 else c for c in color[:3])
            return (0, 0, 0)

        # 默认黑色
        return (0, 0, 0)


if __name__ == "__main__":
    # 测试解析
    parser = PDFParser()

    test_pdf = "/Users/xiaojiujiu2/Downloads/电费账单-陈天浩-20260417_100903.pdf"
    structure = parser.parse(test_pdf)

    print(f"页面尺寸: {structure['page_size']}")
    print(f"元素总数: {len(structure['elements'])}")

    # 统计元素类型
    text_count = sum(1 for e in structure['elements'] if e['type'] == 'text')
    rect_count = sum(1 for e in structure['elements'] if e['type'] == 'rect')
    line_count = sum(1 for e in structure['elements'] if e['type'] == 'line')
    image_count = sum(1 for e in structure['elements'] if e['type'] == 'image')

    print(f"文本元素: {text_count}")
    print(f"矩形元素: {rect_count}")
    print(f"线条元素: {line_count}")
    print(f"图像元素: {image_count}")

    # 显示前5个文本元素
    print("\n前5个文本元素:")
    for i, element in enumerate(structure['elements'][:5]):
        if element['type'] == 'text':
            print(f"  {i+1}. {element['content'][:30]}... @ {element['bbox']}")
