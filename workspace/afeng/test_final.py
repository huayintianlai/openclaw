#!/usr/bin/env python3
"""
完整测试 - 使用新身份证照片，输出到下载目录
"""
import sys
sys.path.insert(0, '/Volumes/KenDisk/Coding/openclaw-runtime/extensions/bill-generator-plugin')

from src.orchestrator import BillGeneratorOrchestrator
from src.generator import FieldChange
from pathlib import Path
from datetime import datetime

print("=" * 80)
print("PDF账单生成 - 完整测试")
print("=" * 80)
print()

# 初始化
orchestrator = BillGeneratorOrchestrator()

# 1. 识别身份证
id_card_path = "/Users/xiaojiujiu2/Downloads/mac_1776351386665.jpg"
print(f"步骤1：识别身份证")
print(f"  图片: {id_card_path}")
id_info = orchestrator.recognize_id_card(id_card_path)
print(f"  ✓ 姓名: {id_info.name}")
print(f"  ✓ 身份证号: {id_info.id_number}")
print(f"  ✓ 地址: {id_info.address}")
print(f"  ✓ 出生日期: {id_info.birth_date}")
print()

# 2. 分析PDF模板
template_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng/template_real.pdf"
print(f"步骤2：分析PDF模板")
print(f"  模板: {template_path}")
text_spans = orchestrator.analyzer.extract_text_spans(template_path)
print(f"  ✓ 提取了 {len(text_spans)} 个文本块")
print()

# 3. 创建字段映射
print("步骤3：创建字段映射")
changes = []

# 查找户名
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
        print(f"  ✓ 户名: 胡月军 → {id_info.name}")
        break

# 查找地址第1行
for span in text_spans:
    if "浙江省建德市大洋镇里黄村" in span.text:
        changes.append(FieldChange(
            field_name="用电地址-第1行",
            original_value=span.text,
            new_value=id_info.address,
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 地址第1行: {span.text} → {id_info.address}")
        break

# 查找地址第2行（清空）
for span in text_spans:
    if "黄家胡家自然村60号" in span.text:
        changes.append(FieldChange(
            field_name="用电地址-第2行",
            original_value=span.text,
            new_value="",
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 地址第2行: 清空")
        break

print(f"  共 {len(changes)} 个字段")
print()

# 4. 生成PDF
print("步骤4：生成PDF账单")
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_dir = Path.home() / "Downloads"
output_path = output_dir / f"电费账单-{id_info.name}-{timestamp}.pdf"

orchestrator.generator.apply_changes(
    template_path,
    changes,
    str(output_path)
)
print(f"  ✓ PDF已生成: {output_path}")
print()

# 5. 生成对比图
print("步骤5：生成对比图")
comparison_path = output_dir / f"电费账单-{id_info.name}-{timestamp}-对比.png"
orchestrator.generator.create_comparison_image(
    template_path,
    str(output_path),
    str(comparison_path)
)
print(f"  ✓ 对比图: {comparison_path}")
print()

print("=" * 80)
print("✓ 测试完成！")
print("=" * 80)
print()
print(f"户名: {id_info.name}")
print(f"地址: {id_info.address}")
print(f"身份证号: {id_info.id_number}")
print()
print(f"PDF文件: {output_path}")
print(f"对比图: {comparison_path}")
