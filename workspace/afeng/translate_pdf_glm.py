#!/usr/bin/env python3
"""
PDF翻译 - GLM视觉识别方案
使用GLM-4V识别PDF结构，GLM-4翻译文本
"""
import fitz
from zhipuai import ZhipuAI
import json
import base64
from io import BytesIO
from PIL import Image


class GLMPDFTranslator:
    """使用GLM进行PDF翻译"""

    def __init__(self, api_key=None):
        """初始化GLM客户端"""
        # 如果没有提供api_key，尝试从环境变量读取
        self.client = ZhipuAI(api_key=api_key)

    def pdf_to_image_base64(self, pdf_path, page_num=0):
        """将PDF页面转换为base64图像"""
        doc = fitz.open(pdf_path)
        page = doc[page_num]

        # 获取页面尺寸
        page_size = (page.rect.width, page.rect.height)

        # 渲染为图像（高分辨率）
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        # 转换为PIL Image
        img = Image.open(BytesIO(pix.tobytes()))

        # 转换为base64
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        doc.close()

        return img_base64, page_size

    def analyze_pdf_structure(self, pdf_path):
        """使用GLM-4V分析PDF结构"""
        print("步骤1：使用GLM-4V分析PDF结构...")
        print("  ⚠️  GLM-4V返回的JSON可能不完整，改用PyMuPDF直接解析...")

        # 直接使用PyMuPDF解析（更可靠）
        from pdf_parser import PDFParser
        parser = PDFParser()
        structure = parser.parse(pdf_path)

        print(f"  ✓ 解析完成：{len(structure['elements'])} 个元素")

        return structure, structure["page_size"]

    def translate_with_glm(self, text):
        """使用GLM-4翻译文本"""
        if not text.strip():
            return text

        # 检查是否包含中文
        if not any('\u4e00' <= c <= '\u9fff' for c in text):
            return text

        response = self.client.chat.completions.create(
            model="glm-4-plus",
            messages=[
                {
                    "role": "system",
                    "content": "你是一个专业的电费账单翻译专家。请将中文翻译成法语，保持专业术语的准确性。只返回翻译结果，不要有任何解释。"
                },
                {
                    "role": "user",
                    "content": f"翻译成法语：{text}"
                }
            ],
            temperature=0.1,
        )

        return response.choices[0].message.content.strip()

    def translate_pdf(self, input_pdf, output_pdf):
        """翻译PDF"""
        print("=" * 80)
        print("PDF翻译系统 - GLM翻译方案")
        print("=" * 80)

        # 1. 分析PDF结构（使用PyMuPDF）
        structure, page_size = self.analyze_pdf_structure(input_pdf)

        # 2. 翻译所有文本
        print("\n步骤2：使用GLM-4翻译文本...")
        translated_count = 0
        skipped_count = 0

        for element in structure["elements"]:
            if element["type"] == "text":
                original = element["content"]

                # 跳过logo区域（顶部50px）
                if element["bbox"][1] < 50:
                    skipped_count += 1
                    continue

                # 翻译中文文本
                translated = self.translate_with_glm(original)
                element["content"] = translated

                if translated != original:
                    translated_count += 1
                    print(f"  ✓ {original[:30]} → {translated[:30]}")

        print(f"  ✓ 已翻译 {translated_count} 个文本块")
        print(f"  ⊘ 跳过logo区域 {skipped_count} 个")

        # 3. 重建PDF
        print("\n步骤3：使用ReportLab重建PDF...")
        from pdf_rebuilder import PDFRebuilder
        rebuilder = PDFRebuilder()
        rebuilder.rebuild(structure, output_pdf)
        print(f"  ✓ PDF已生成: {output_pdf}")

        print("\n" + "=" * 80)
        print("✓ 翻译完成！")
        print("=" * 80)

        return structure


if __name__ == "__main__":
    # 测试
    api_key = "8d743ac0257e4c699130d2d0e816a100.5J0Cs3W7CkEJFvwH"
    translator = GLMPDFTranslator(api_key=api_key)

    input_pdf = "/Users/xiaojiujiu2/Downloads/电费账单-陈天浩-20260417_100903.pdf"
    output_pdf = "/Users/xiaojiujiu2/Downloads/电费账单-陈天浩-GLM翻译.pdf"

    structure = translator.translate_pdf(input_pdf, output_pdf)

    # 保存结构分析结果（排除图像数据）
    structure_copy = {
        "page_size": structure["page_size"],
        "elements": []
    }
    for elem in structure["elements"]:
        elem_copy = elem.copy()
        if elem_copy.get("type") == "image":
            elem_copy["image_data"] = f"<{len(elem_copy.get('image_data', b''))} bytes>"
        structure_copy["elements"].append(elem_copy)

    with open("/tmp/glm_structure.json", "w", encoding="utf-8") as f:
        json.dump(structure_copy, f, ensure_ascii=False, indent=2)

    print(f"\n结构分析结果已保存到: /tmp/glm_structure.json")
