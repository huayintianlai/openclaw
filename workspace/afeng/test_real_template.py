#!/usr/bin/env python3
"""
使用真实PDF模板测试完整流程
"""
import sys
sys.path.insert(0, '/Volumes/KenDisk/Coding/openclaw-runtime/extensions/bill-generator-plugin')

from src.orchestrator import BillGeneratorOrchestrator
from src.generator import FieldChange
from pathlib import Path

print("=" * 80)
print("真实PDF账单生成测试")
print("=" * 80)
print()

# 初始化
orchestrator = BillGeneratorOrchestrator()

# 1. 识别身份证
id_card_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng/test_id_card.png"
print(f"1. 识别身份证: {id_card_path}")
id_info = orchestrator.recognize_id_card(id_card_path)
print(f"   ✓ 姓名: {id_info.name}")
print(f"   ✓ 地址: {id_info.address}")
print()

# 2. 分析真实PDF
template_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng/template_real.pdf"
print(f"2. 分析真实PDF: {template_path}")
text_spans = orchestrator.analyzer.extract_text_spans(template_path)
print(f"   ✓ 提取了 {len(text_spans)} 个文本块")
print()

# 3. 手动创建字段映射
print("3. 创建字段映射...")
changes = []

# 查找户名：胡月军
for span in text_spans:
    if "胡月军" in span.text:
        changes.append(FieldChange(
            field_name="户名",
            original_value="胡月军",
            new_value=id_info.name,
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"   ✓ 找到户名: 胡月军 → {id_info.name}")
        print(f"     位置: {span.bbox}")
        print(f"     字体: {span.font} {span.font_size}pt")
        break

# 查找地址（分两行）
address_line1 = "浙江省建德市大洋镇里黄村"
address_line2 = "黄家胡家自然村60号"

# 第一行地址
for span in text_spans:
    if address_line1 in span.text:
        changes.append(FieldChange(
            field_name="用电地址-第1行",
            original_value=span.text,
            new_value=id_info.address,
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"   ✓ 找到地址第1行: {span.text} → {id_info.address}")
        print(f"     位置: {span.bbox}")
        break

# 第二行地址（清空）
for span in text_spans:
    if address_line2 in span.text:
        changes.append(FieldChange(
            field_name="用电地址-第2行",
            original_value=span.text,
            new_value="",  # 清空第二行
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"   ✓ 找到地址第2行: {span.text} → (清空)")
        print(f"     位置: {span.bbox}")
        break

print(f"   共创建 {len(changes)} 个字段映射")
print()

if not changes:
    print("   ⚠ 未找到可替换的字段")
    sys.exit(1)

# 4. 生成PDF
print("4. 生成账单...")
output_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng/bills/real_output.pdf"
Path(output_path).parent.mkdir(parents=True, exist_ok=True)

orchestrator.generator.apply_changes(
    template_path,
    changes,
    output_path
)
print(f"   ✓ 生成成功: {output_path}")
print()

# 5. 生成对比图
print("5. 生成对比图...")
comparison_path = output_path.replace('.pdf', '_comparison.png')
orchestrator.generator.create_comparison_image(
    template_path,
    output_path,
    comparison_path
)
print(f"   ✓ 对比图: {comparison_path}")
print()

print("=" * 80)
print("✓ 测试完成")
print("=" * 80)
print()
print(f"输出文件: {output_path}")
print(f"对比图: {comparison_path}")
