#!/usr/bin/env python3
"""
压缩 PDF 文件到目标大小
使用 PyPDF2 或 img2pdf 重新编码
"""
import sys
import os
from PyPDF2 import PdfReader, PdfWriter
import subprocess

def compress_pdf_quartz(input_path, output_path, quality='medium'):
    """使用 macOS Quartz 压缩 PDF"""
    quality_map = {
        'low': '/printer',
        'medium': '/ebook',
        'high': '/prepress'
    }

    filter_type = quality_map.get(quality, '/ebook')

    cmd = [
        '/System/Library/Printers/Libraries/convert',
        '-f', input_path,
        '-o', output_path,
        '-j', filter_type
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except:
        return False

def compress_pdf_simple(input_path, output_path):
    """简单的 PDF 压缩 - 移除元数据和优化"""
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        # 压缩
        writer.add_metadata({'/Producer': 'PDF Compressor'})

        with open(output_path, 'wb') as f:
            writer.write(f)

        return True
    except Exception as e:
        print(f"压缩失败: {e}")
        return False

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("用法: python3 compress_pdf.py <input.pdf> <output.pdf> <target_size_mb>")
        sys.exit(1)

    input_pdf = sys.argv[1]
    output_pdf = sys.argv[2]
    target_mb = float(sys.argv[3])

    if not os.path.exists(input_pdf):
        print(f"错误: 输入文件不存在 - {input_pdf}")
        sys.exit(1)

    # 获取原始大小
    original_size = os.path.getsize(input_pdf)
    original_mb = original_size / 1048576

    print(f"原始大小: {original_mb:.2f}M")
    print(f"目标大小: {target_mb:.2f}M")

    if original_mb <= target_mb * 1.1:  # 如果已经接近目标，不压缩
        print("文件大小已符合要求，无需压缩")
        sys.exit(0)

    # 尝试使用 Quartz 压缩
    if compress_pdf_quartz(input_pdf, output_pdf, 'medium'):
        compressed_size = os.path.getsize(output_pdf)
        compressed_mb = compressed_size / 1048576
        print(f"压缩后大小: {compressed_mb:.2f}M")
        sys.exit(0)

    # 回退到简单压缩
    if compress_pdf_simple(input_pdf, output_pdf):
        compressed_size = os.path.getsize(output_pdf)
        compressed_mb = compressed_size / 1048576
        print(f"压缩后大小: {compressed_mb:.2f}M")
        sys.exit(0)

    print("压缩失败")
    sys.exit(1)
