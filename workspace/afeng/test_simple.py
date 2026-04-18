#!/usr/bin/env python3
"""
简化版测试 - 不依赖AI字段检测
"""
import sys
sys.path.insert(0, '/Volumes/KenDisk/Coding/openclaw-runtime/extensions/bill-generator-plugin')

from src.orchestrator import BillGeneratorOrchestrator
from src.generator import FieldChange
from pathlib import Path

print("=" * 60)
print("阿峰 - 账单生成简化测试")
print("=" * 60)
print()

# 初始化
print("1. 初始化orchestrator...")
orchestrator = BillGeneratorOrchestrator()
print("   ✓ 初始化成功")
print()

# 测试OCR
id_card_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng/test_id_card.png"
print(f"2. 识别身份证: {id_card_path}")
id_info = orchestrator.recognize_id_card(id_card_path)
print(f"   ✓ 识别成功")
print(f"   姓名: {id_info.name}")
print(f"   身份证号: {id_info.id_number}")
print(f"   地址: {id_info.address}")
print(f"   出生日期: {id_info.birth_date}")
print()

# 分析PDF
template_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng/test_template.pdf"
print(f"3. 分析PDF模板: {template_path}")
text_spans = orchestrator.analyzer.extract_text_spans(template_path)
print(f"   ✓ 提取了 {len(text_spans)} 个文本块")
for i, span in enumerate(text_spans[:10]):
    print(f"     {i+1}. {span.text[:30]}")
print()

# 手动创建字段映射
print("4. 创建字段映射...")
changes = []

# 查找并替换"张三"
for span in text_spans:
    if "张三" in span.text:
        changes.append(FieldChange(
            field_name="户名",
            original_value="张三",
            new_value=id_info.name,
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"   ✓ 找到户名字段: 张三 → {id_info.name}")
        break

# 查找并替换地址
for span in text_spans:
    if "北京市朝阳区" in span.text:
        changes.append(FieldChange(
            field_name="地址",
            original_value="北京市朝阳区XX街道XX号",
            new_value=id_info.address,
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"   ✓ 找到地址字段")
        break

print(f"   共创建 {len(changes)} 个字段映射")
print()

if not changes:
    print("   ⚠ 未找到可替换的字段")
    sys.exit(0)

# 生成PDF
print("5. 生成账单...")
output_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng/bills/test_output.pdf"
Path(output_path).parent.mkdir(parents=True, exist_ok=True)

orchestrator.generator.apply_changes(
    template_path,
    changes,
    output_path
)
print(f"   ✓ 生成成功: {output_path}")
print()

# 生成对比图
print("6. 生成对比图...")
comparison_path = output_path.replace('.pdf', '_comparison.png')
orchestrator.generator.create_comparison_image(
    template_path,
    output_path,
    comparison_path
)
print(f"   ✓ 对比图: {comparison_path}")
print()

print("=" * 60)
print("✓ 完整测试通过")
print("=" * 60)
print()
print(f"输出文件: {output_path}")
print(f"对比图: {comparison_path}")
