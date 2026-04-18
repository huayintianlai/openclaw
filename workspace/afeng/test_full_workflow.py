#!/usr/bin/env python3
"""
完整测试账单生成流程
"""
import sys
sys.path.insert(0, '/Volumes/KenDisk/Coding/openclaw-runtime/extensions/bill-generator-plugin')

from src.orchestrator import BillGeneratorOrchestrator
from pathlib import Path

print("=" * 60)
print("阿峰 - 账单生成完整测试")
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
try:
    id_info = orchestrator.recognize_id_card(id_card_path)
    print(f"   ✓ 识别成功")
    print(f"   姓名: {id_info.name}")
    print(f"   身份证号: {id_info.id_number}")
    print(f"   地址: {id_info.address}")
    print(f"   出生日期: {id_info.birth_date}")
    print(f"   置信度: {id_info.confidence}")
    print()
except Exception as e:
    print(f"   ✗ 识别失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 检查模板
template_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng/test_template.pdf"
print(f"3. 检查PDF模板: {template_path}")
if not Path(template_path).exists():
    print(f"   ⚠ 模板不存在")
    print(f"   请将PDF模板放置到: {template_path}")
    print()
    print("=" * 60)
    print("部分测试完成")
    print("=" * 60)
    print()
    print("✓ OCR识别功能正常")
    print("⚠ 需要PDF模板才能完成完整测试")
    sys.exit(0)

print(f"   ✓ 模板存在")
print()

# 生成账单
print("4. 生成账单...")
try:
    result = orchestrator.generate_bill(
        template_path=template_path,
        identity={
            "name": id_info.name,
            "address": id_info.address,
            "id_number": id_info.id_number
        },
        custom_fields=None
    )

    if result.success:
        print(f"   ✓ 生成成功")
        print()
        print(f"   输出文件: {result.output_path}")
        print(f"   对比图: {result.comparison_image}")
        print()
        print(f"   修改了 {len(result.changes)} 个字段:")
        for change in result.changes:
            print(f"     - {change.field_name}: {change.original_value} → {change.new_value}")
        print()
        print("=" * 60)
        print("✓ 完整测试通过")
        print("=" * 60)
    else:
        print(f"   ✗ 生成失败: {result.error}")
        sys.exit(1)

except Exception as e:
    print(f"   ✗ 生成失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
