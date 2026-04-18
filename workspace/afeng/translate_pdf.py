#!/usr/bin/env python3
"""
PDF翻译主程序 - 整合解析、翻译、重建
"""
from pdf_parser import PDFParser
from pdf_rebuilder import PDFRebuilder
from translator import BillTranslator
import re


def translate_pdf(input_pdf, output_pdf):
    """
    翻译PDF文件

    Args:
        input_pdf: 输入PDF路径
        output_pdf: 输出PDF路径
    """
    print("=" * 80)
    print("PDF翻译系统 - ReportLab重建方案")
    print("=" * 80)

    # 1. 解析PDF结构
    print("\n步骤1：解析PDF结构")
    parser = PDFParser()
    structure = parser.parse(input_pdf)
    print(f"  ✓ 页面尺寸: {structure['page_size']}")
    print(f"  ✓ 元素总数: {len(structure['elements'])}")

    # 统计元素类型
    text_count = sum(1 for e in structure['elements'] if e['type'] == 'text')
    rect_count = sum(1 for e in structure['elements'] if e['type'] == 'rect')
    line_count = sum(1 for e in structure['elements'] if e['type'] == 'line')
    image_count = sum(1 for e in structure['elements'] if e['type'] == 'image')
    print(f"  ✓ 文本: {text_count}, 矩形: {rect_count}, 线条: {line_count}, 图像: {image_count}")

    # 2. 翻译文本
    print("\n步骤2：翻译文本")
    translator = BillTranslator()
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]+')

    translated_count = 0
    skipped_count = 0
    page_height = structure['page_size'][1]

    for element in structure['elements']:
        if element['type'] == 'text':
            original = element['content']

            # 跳过logo区域的文本（顶部50px内的文本）
            y_pos = element['bbox'][1]
            if y_pos < 50:
                skipped_count += 1
                continue

            # 只翻译包含中文的文本
            if chinese_pattern.search(original):
                translated = translator.translate_field(original)
                element['content'] = translated
                if translated != original:
                    translated_count += 1

    print(f"  ✓ 已翻译 {translated_count} 个文本块")
    print(f"  ✓ 跳过logo区域 {skipped_count} 个文本块")

    # 3. 重建PDF
    print("\n步骤3：使用ReportLab重建PDF")
    rebuilder = PDFRebuilder()
    rebuilder.rebuild(structure, output_pdf)
    print(f"  ✓ PDF已生成: {output_pdf}")

    print("\n" + "=" * 80)
    print("✓ 翻译完成！")
    print("=" * 80)

    return {
        "total_elements": len(structure['elements']),
        "text_elements": text_count,
        "translated_count": translated_count
    }


if __name__ == "__main__":
    # 翻译测试文件
    input_pdf = "/Users/xiaojiujiu2/Downloads/电费账单-陈天浩-20260417_100903.pdf"
    output_pdf = "/Users/xiaojiujiu2/Downloads/电费账单-陈天浩-ReportLab翻译.pdf"

    result = translate_pdf(input_pdf, output_pdf)

    print(f"\n统计信息:")
    print(f"  总元素数: {result['total_elements']}")
    print(f"  文本元素: {result['text_elements']}")
    print(f"  已翻译: {result['translated_count']}")
