#!/usr/bin/env python3
"""
智能账单生成 - 根据身份证地址自动生成所有相关字段
"""
import sys
sys.path.insert(0, '/Volumes/KenDisk/Coding/openclaw-runtime/extensions/bill-generator-plugin')

from src.orchestrator import BillGeneratorOrchestrator
from src.generator import FieldChange
from pathlib import Path
from datetime import datetime, timedelta
import random
import re

print("=" * 80)
print("智能PDF账单生成")
print("=" * 80)
print()

# 初始化
orchestrator = BillGeneratorOrchestrator()

# 1. 识别身份证
id_card_path = "/Users/xiaojiujiu2/Downloads/mac_1776351386665.jpg"
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

# 3.1 账单周期（上个月）
today = datetime.now()
last_month = today.replace(day=1) - timedelta(days=1)
period_start = last_month.replace(day=1).strftime('%Y-%m-%d')
period_end = last_month.strftime('%Y-%m-%d')
print(f"  ✓ 账单周期: {period_start} 至 {period_end}")

# 3.2 抄表日期（账单周期结束后1-3天，即本月初）
meter_reading_day = random.randint(1, 3)
meter_date = today.replace(day=meter_reading_day).strftime('%Y-%m-%d')
print(f"  ✓ 抄表日期: {meter_date}")

# 3.3 账单打印日期（抄表后几天）
print_day = meter_reading_day + random.randint(5, 7)
print_date = today.replace(day=print_day).strftime('%Y-%m-%d')
print(f"  ✓ 账单打印日期: {print_date}")

# 3.4 生成户号（根据地区编码）
# 浙江省建德市的区号是330182
area_code = id_info.id_number[:6] if id_info.id_number else "330182"
account_number = area_code + str(random.randint(10000000, 99999999))
print(f"  ✓ 户号: {account_number}")

# 3.5 生成电表编号（根据地区）
# 浙江省编号通常以33开头，总共22位（与模板一致）
# area_code是6位（33开头），再加16位随机数
meter_number = area_code + str(random.randint(1000000000000000, 9999999999999999))
print(f"  ✓ 电表编号: {meter_number}")

# 3.6 地址换行处理
if len(address) > 15:
    # 找合适的换行位置（镇/街道后）
    for sep in ['镇', '街道', '乡']:
        if sep in address:
            idx = address.index(sep) + 1
            address_line1 = address[:idx]
            address_line2 = address[idx:]
            break
    else:
        # 如果没找到，按长度切分
        address_line1 = address[:15]
        address_line2 = address[15:]
else:
    address_line1 = address
    address_line2 = ""

print(f"  ✓ 地址第1行: {address_line1}")
print(f"  ✓ 地址第2行: {address_line2}")

# 3.7 供电公司名称
power_company = f"国网{province.replace('省', '')}{city_short}供电公司"
print(f"  ✓ 供电公司: {power_company}")

# 3.8 省份简称（用于电价）
province_short = province.replace("省", "")
print(f"  ✓ 省份简称: {province_short}")

# 3.9 生成用电数据
print(f"  ✓ 生成用电数据...")
elec_data = orchestrator.data_generator.generate(min_kwh=200, max_kwh=800)
print(f"     - 总用电量: {elec_data.total_kwh} kWh")
print(f"     - 峰段: {elec_data.peak_kwh} kWh")
print(f"     - 平段: {elec_data.normal_kwh} kWh")
print(f"     - 谷段: {elec_data.valley_kwh} kWh")
print(f"     - 总电费: {elec_data.total_fee} 元")
print(f"     - 平均电价: {elec_data.avg_price} 元/kWh")
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

# 5.1 户名
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
        print(f"  ✓ 户名")
        break

# 5.2 户号
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
        print(f"  ✓ 户号")
        break

# 5.3 用电地址（第1行）
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
        print(f"  ✓ 用电地址-第1行")
        break

# 5.4 用电地址（第2行）
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
        print(f"  ✓ 用电地址-第2行")
        break

# 5.5 账单周期开始
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
        print(f"  ✓ 账单周期-开始")
        break

# 5.6 账单周期结束
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
        print(f"  ✓ 账单周期-结束")
        break

# 5.7 账单打印日期
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
        print(f"  ✓ 账单打印日期")
        break

# 5.8 抄表日期
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
        print(f"  ✓ 抄表日期")
        break

# 5.10 供电服务单位
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
        print(f"  ✓ 供电服务单位")
        break

# 5.11 替换所有"四川"为省份名，并替换电能表编号
import re
for span in text_spans:
    if "四川" in span.text:
        new_text = span.text.replace("四川", province_short)
        # 如果包含电能表编号，也替换电表编号
        if "电能表编号" in span.text:
            # 提取原电表编号（22位数字）
            old_meter_match = re.search(r'电能表编号：(\d{22})', span.text)
            if old_meter_match:
                old_meter = old_meter_match.group(1)
                new_text = new_text.replace(old_meter, meter_number)
        changes.append(FieldChange(
            field_name=f"电价地区-{span.text[:15]}",
            original_value=span.text,
            new_value=new_text,
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 电价地区")

# 5.12 本期电量
for span in text_spans:
    if span.text.strip() == "762":
        # 检查是否是本期电量字段（通过位置判断）
        if 180 < span.bbox[0] < 200 and 160 < span.bbox[1] < 170:
            changes.append(FieldChange(
                field_name="本期电量",
                original_value="762",
                new_value=str(elec_data.total_kwh),
                bbox=span.bbox,
                font=span.font,
                font_size=span.font_size,
                color=span.color
            ))
            print(f"  ✓ 本期电量")
            break

# 5.13 本期电费
for span in text_spans:
    if span.text.strip() == "503.69":
        # 检查是否是本期电费字段（通过位置判断）
        if 345 < span.bbox[0] < 375 and 160 < span.bbox[1] < 170:
            changes.append(FieldChange(
                field_name="本期电费",
                original_value="503.69",
                new_value=str(elec_data.total_fee),
                bbox=span.bbox,
                font=span.font,
                font_size=span.font_size,
                color=span.color
            ))
            print(f"  ✓ 本期电费")
            break

# 5.14 电量明细表 - 正向有功(总/平)
for span in text_spans:
    if span.text.strip() == "9343":
        changes.append(FieldChange(
            field_name="上期示数-总",
            original_value="9343",
            new_value=str(elec_data.prev_total_reading),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 上期示数-总")
        break

for span in text_spans:
    if span.text.strip() == "10105":
        changes.append(FieldChange(
            field_name="本期示数-总",
            original_value="10105",
            new_value=str(elec_data.curr_total_reading),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 本期示数-总")
        break

# 5.15 电量明细表 - 正向有功(谷)
for span in text_spans:
    if span.text.strip() == "2215":
        changes.append(FieldChange(
            field_name="上期示数-谷",
            original_value="2215",
            new_value=str(elec_data.prev_valley_reading),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 上期示数-谷")
        break

for span in text_spans:
    if span.text.strip() == "2356":
        changes.append(FieldChange(
            field_name="本期示数-谷",
            original_value="2356",
            new_value=str(elec_data.curr_valley_reading),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 本期示数-谷")
        break

# 5.16 电量明细表 - 正向有功(峰)
for span in text_spans:
    if span.text.strip() == "3325":
        changes.append(FieldChange(
            field_name="上期示数-峰",
            original_value="3325",
            new_value=str(elec_data.prev_peak_reading),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 上期示数-峰")
        break

for span in text_spans:
    if span.text.strip() == "3601":
        changes.append(FieldChange(
            field_name="本期示数-峰",
            original_value="3601",
            new_value=str(elec_data.curr_peak_reading),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 本期示数-峰")
        break

# 5.17 电费明细表 - 峰段
for span in text_spans:
    # 峰段电量 276 (在电费明细表中)
    if span.text.strip() == "276" and 249 < span.bbox[0] < 251 and 377 < span.bbox[1] < 379:
        changes.append(FieldChange(
            field_name="峰段电量",
            original_value="276",
            new_value=str(elec_data.peak_kwh),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 峰段电量")
        break

for span in text_spans:
    # 峰段电费 144.18
    if span.text.strip() == "144.18":
        changes.append(FieldChange(
            field_name="峰段电费",
            original_value="144.18",
            new_value=str(elec_data.peak_fee),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 峰段电费")
        break

# 5.18 电费明细表 - 平段
for span in text_spans:
    # 平段电量 345
    if span.text.strip() == "345":
        changes.append(FieldChange(
            field_name="平段电量",
            original_value="345",
            new_value=str(elec_data.normal_kwh),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 平段电量")
        break

for span in text_spans:
    # 平段电费 180.23
    if span.text.strip() == "180.23":
        changes.append(FieldChange(
            field_name="平段电费",
            original_value="180.23",
            new_value=str(elec_data.normal_fee),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 平段电费")
        break

# 5.19 电费明细表 - 谷段
for span in text_spans:
    # 谷段电量 141 (在电费明细表中)
    if span.text.strip() == "141" and 249 < span.bbox[0] < 251 and 416 < span.bbox[1] < 418:
        changes.append(FieldChange(
            field_name="谷段电量",
            original_value="141",
            new_value=str(elec_data.valley_kwh),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 谷段电量")
        break

for span in text_spans:
    # 谷段电费 24.68
    if span.text.strip() == "24.68":
        changes.append(FieldChange(
            field_name="谷段电费",
            original_value="24.68",
            new_value=str(elec_data.valley_fee),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 谷段电费")
        break

# 5.20 阶梯加价 - 三档
for span in text_spans:
    # 三档加价电量 482
    if span.text.strip() == "482":
        changes.append(FieldChange(
            field_name="三档加价电量",
            original_value="482",
            new_value=str(elec_data.tier3_kwh),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 三档加价电量")
        break

for span in text_spans:
    # 三档加价电费 144.6
    if span.text.strip() == "144.6":
        changes.append(FieldChange(
            field_name="三档加价电费",
            original_value="144.6",
            new_value=str(elec_data.tier3_surcharge),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 三档加价电费")
        break

# 5.21 阶梯加价 - 二档
for span in text_spans:
    # 二档加价电量 100
    if span.text.strip() == "100" and 249 < span.bbox[0] < 251 and 448 < span.bbox[1] < 449:
        changes.append(FieldChange(
            field_name="二档加价电量",
            original_value="100",
            new_value=str(elec_data.tier2_kwh),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 二档加价电量")
        break

for span in text_spans:
    # 二档加价电费 10
    if span.text.strip() == "10" and 366 < span.bbox[0] < 376:
        changes.append(FieldChange(
            field_name="二档加价电费",
            original_value="10",
            new_value=str(elec_data.tier2_surcharge),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 二档加价电费")
        break

# 5.22 合计电费
for span in text_spans:
    if "￥503.69" in span.text:
        changes.append(FieldChange(
            field_name="合计电费",
            original_value="￥503.69",
            new_value=f"￥{elec_data.total_fee}",
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 合计电费")
        break

print(f"  共 {len(changes)} 个字段")
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
