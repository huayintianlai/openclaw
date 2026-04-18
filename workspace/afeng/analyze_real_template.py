#!/usr/bin/env python3
"""
分析真实PDF模板，提取所有文本内容
"""
import sys
sys.path.insert(0, '/Volumes/KenDisk/Coding/openclaw-runtime/extensions/bill-generator-plugin')

from src.orchestrator import BillGeneratorOrchestrator

print("=" * 80)
print("分析真实PDF模板")
print("=" * 80)
print()

orchestrator = BillGeneratorOrchestrator()
template_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng/template_real.pdf"

print(f"模板路径: {template_path}")
print()

# 提取文本
text_spans = orchestrator.analyzer.extract_text_spans(template_path)
print(f"共提取 {len(text_spans)} 个文本块")
print()

# 显示所有文本内容
print("=" * 80)
print("所有文本内容:")
print("=" * 80)
for i, span in enumerate(text_spans):
    print(f"{i+1:3d}. [{span.font:20s}] {span.font_size:5.1f}pt | {span.text}")
print()

# 转换为图片查看
print("=" * 80)
print("转换PDF为图片...")
print("=" * 80)
img_bytes = orchestrator.analyzer.convert_page_to_image(template_path, dpi=150)
img_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng/template_real_preview.png"
with open(img_path, 'wb') as f:
    f.write(img_bytes)
print(f"✓ 预览图: {img_path}")
