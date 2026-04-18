#!/usr/bin/env python3
"""
检查PDF中特定字段的字体信息
"""
import sys
sys.path.insert(0, '/Volumes/KenDisk/Coding/openclaw-runtime/extensions/bill-generator-plugin')

from src.orchestrator import BillGeneratorOrchestrator

orchestrator = BillGeneratorOrchestrator()
template_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng/template_real.pdf"

text_spans = orchestrator.analyzer.extract_text_spans(template_path)

# 重点检查的字段
target_texts = [
    "3301144465062",  # 户号
    "2026-01-01",     # 账单周期开始
    "2026-01-31",     # 账单周期结束
    "2026-02-08",     # 账单打印日期
    "2026-02-01",     # 抄表日期
    "5130001000000361446389",  # 电表编号
]

print("=" * 80)
print("关键字段的字体信息")
print("=" * 80)
print()

for target in target_texts:
    for span in text_spans:
        if target in span.text:
            print(f"文本: {span.text}")
            print(f"  字体: {span.font}")
            print(f"  字号: {span.font_size}pt")
            print(f"  颜色: {span.color}")
            print(f"  位置: {span.bbox}")
            print()
            break
