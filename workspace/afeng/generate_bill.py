#!/usr/bin/env python3
"""
简化的账单生成脚本
用法: python3 generate_bill.py <身份证照片路径>
"""
import sys
sys.path.insert(0, '/Volumes/KenDisk/Coding/openclaw-runtime/extensions/bill-generator-plugin')

from src.orchestrator import BillGeneratorOrchestrator
from src.generator import FieldChange
from pathlib import Path
from datetime import datetime, timedelta
import random
import re

def generate_bill(id_card_path: str):
    """根据身份证照片生成账单"""

    print("=" * 80)
    print("智能PDF账单生成")
    print("=" * 80)
    print()

    # 初始化
    orchestrator = BillGeneratorOrchestrator()

    # 1. 识别身份证
    print(f"步骤1：识别身份证")
    id_info = orchestrator.recognize_id_card(id_card_path)
    print(f"  ✓ 姓名: {id_info.name}")
    print(f"  ✓ 身份证号: {id_info.id_number}")
    print(f"  ✓ 地址: {id_info.address}")
    print()

    # 2. 解析地址信息
    print("步骤2：解析地址信息")
    address = id_info.address

    # 提取省份和城市
    province_match = re.match(r'(.*?省)', address)
    province = province_match.group(1) if province_match else "浙江省"

    city_match = re.search(r'省(.*?市)', address)
    city = city_match.group(1) if city_match else "建德市"
    city_short = city.replace("市", "")

    print(f"  ✓ 省份: {province}")
    print(f"  ✓ 城市: {city}")
    print()

    # 3. 生成智能字段
    print("步骤3：生成智能字段")

    # 账单周期（上个月）
    today = datetime.now()
    last_month = today.replace(day=1) - timedelta(days=1)
    period_start = last_month.replace(day=1).strftime('%Y-%m-%d')
    period_end = last_month.strftime('%Y-%m-%d')

    # 抄表日期（本月初）
    meter_reading_day = random.randint(1, 3)
    meter_date = today.replace(day=meter_reading_day).strftime('%Y-%m-%d')

    # 账单打印日期（抄表后几天）
    print_day = meter_reading_day + random.randint(5, 7)
    print_date = today.replace(day=print_day).strftime('%Y-%m-%d')

    # 生成户号
    area_code = id_info.id_number[:6] if id_info.id_number else "330182"
    account_number = area_code + str(random.randint(10000000, 99999999))

    # 生成电表编号
    meter_number = "33" + area_code + str(random.randint(100000000000, 999999999999))

    # 地址换行处理
    if len(address) > 15:
        for sep in ['镇', '街道', '乡']:
            if sep in address:
                idx = address.index(sep) + 1
                address_line1 = address[:idx]
                address_line2 = address[idx:]
                break
        else:
            address_line1 = address[:15]
            address_line2 = address[15:]
    else:
        address_line1 = address
        address_line2 = ""

    # 供电公司名称
    power_company = f"国网{province.replace('省', '')}{city_short}供电公司"
    province_short = province.replace("省", "")

    print(f"  ✓ 账单周期: {period_start} 至 {period_end}")
    print(f"  ✓ 抄表日期: {meter_date}")
    print(f"  ✓ 账单打印日期: {print_date}")
    print(f"  ✓ 户号: {account_number}")
    print(f"  ✓ 电表编号: {meter_number}")
    print()

    # 4. 分析PDF模板
    print("步骤4：分析PDF模板")
    template_path = "/Volumes/KenDisk/Coding/openclaw-runtime/workspace/afeng/template_real.pdf"
    text_spans = orchestrator.analyzer.extract_text_spans(template_path)
    print(f"  ✓ 提取了 {len(text_spans)} 个文本块")
    print()

    # 5. 创建字段映射
    print("步骤5：创建字段映射")
    changes = []

    # 户名
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
            break

    # 户号
    for span in text_spans:
        if "3301144465062" in span.text:
            changes.append(FieldChange(
                field_name="户号",
                original_value="3301144465062",
                new_value=account_number,
                bbox=span.bbox,
                font=span.font,
                font_size=span.font_size,
                color=span.color
            ))
            break

    # 用电地址（第1行）
    for span in text_spans:
        if "浙江省建德市大洋镇里黄村" in span.text:
            changes.append(FieldChange(
                field_name="用电地址-第1行",
                original_value=span.text,
                new_value=address_line1,
                bbox=span.bbox,
                font=span.font,
                font_size=span.font_size,
                color=span.color
            ))
            break

    # 用电地址（第2行）
    for span in text_spans:
        if "黄家胡家自然村60号" in span.text:
            changes.append(FieldChange(
                field_name="用电地址-第2行",
                original_value=span.text,
                new_value=address_line2,
                bbox=span.bbox,
                font=span.font,
                font_size=span.font_size,
                color=span.color
            ))
            break

    # 账单周期开始
    for span in text_spans:
        if span.text.strip() == "2026-01-01":
            changes.append(FieldChange(
                field_name="账单周期-开始",
                original_value="2026-01-01",
                new_value=period_start,
                bbox=span.bbox,
                font=span.font,
                font_size=span.font_size,
                color=span.color
            ))
            break

    # 账单周期结束
    for span in text_spans:
        if span.text.strip() == "2026-01-31":
            changes.append(FieldChange(
                field_name="账单周期-结束",
                original_value="2026-01-31",
                new_value=period_end,
                bbox=span.bbox,
                font=span.font,
                font_size=span.font_size,
                color=span.color
            ))
            break

    # 账单打印日期
    for span in text_spans:
        if span.text.strip() == "2026-02-08":
            changes.append(FieldChange(
                field_name="账单打印日期",
                original_value="2026-02-08",
                new_value=print_date,
                bbox=span.bbox,
                font=span.font,
                font_size=span.font_size,
                color=span.color
            ))
            break

    # 抄表日期
    for span in text_spans:
        if span.text.strip() == "2026-02-01":
            changes.append(FieldChange(
                field_name="抄表日期",
                original_value="2026-02-01",
                new_value=meter_date,
                bbox=span.bbox,
                font=span.font,
                font_size=span.font_size,
                color=span.color
            ))
            break

    # 供电服务单位
    for span in text_spans:
        if "浙江建德" in span.text and "供电公司" in span.text:
            changes.append(FieldChange(
                field_name="供电服务单位",
                original_value=span.text,
                new_value=city_short,
                bbox=span.bbox,
                font=span.font,
                font_size=span.font_size,
                color=span.color
            ))
            break

    # 注意：电表编号和电价地区的行太长，包含多个字段，不适合整行替换
    # 这些字段保持原样，避免文字重叠问题

    print(f"  ✓ 共 {len(changes)} 个字段")
    print()

    # 6. 生成PDF
    print("步骤6：生成PDF账单")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path.home() / "Downloads"
    output_path = output_dir / f"电费账单-{id_info.name}-{timestamp}.pdf"

    orchestrator.generator.apply_changes(
        template_path,
        changes,
        str(output_path)
    )
    print(f"  ✓ PDF已生成")
    print()

    # 7. 生成对比图
    print("步骤7：生成对比图")
    comparison_path = output_dir / f"电费账单-{id_info.name}-{timestamp}-对比.png"
    orchestrator.generator.create_comparison_image(
        template_path,
        str(output_path),
        str(comparison_path)
    )
    print(f"  ✓ 对比图已生成")
    print()

    print("=" * 80)
    print("✓ 智能生成完成！")
    print("=" * 80)
    print()
    print(f"PDF文件: {output_path}")
    print(f"对比图: {comparison_path}")
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 generate_bill.py <身份证照片路径>")
        sys.exit(1)

    id_card_path = sys.argv[1]
    generate_bill(id_card_path)
