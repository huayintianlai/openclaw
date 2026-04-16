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
from price_calculator import ElectricityCalculator

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
# 浙江省编号通常以33开头
meter_number = "33" + area_code + str(random.randint(100000000000, 999999999999))
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

# 3.9 生成电量和电费数据
calculator = ElectricityCalculator(province=province_short)
elec_data = calculator.generate_random_data()
print(f"  ✓ 总电量: {elec_data.total_kwh} kWh")
print(f"  ✓ 应缴电费: {elec_data.total_fee} 元")
print(f"  ✓ 平均电价: {elec_data.avg_price} 元/kWh")
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

# 5.10.1 电能表编号行（左侧橙色框）
for span in text_spans:
    if "电能表编号：" in span.text and "电价：" in span.text:
        # 提取原始的电表编号和电价信息
        original_text = span.text
        # 构建新文本：电能表编号 + 电价地区
        new_text = f"电能表编号：{meter_number},电价：{province_short}-用电户-220至380伏-居民"
        changes.append(FieldChange(
            field_name="电能表编号行",
            original_value=original_text,
            new_value=new_text,
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 电能表编号行")
        break

# 5.11 右上角本期电量
for span in text_spans:
    if span.text.strip() == "762":
        # 检查位置是否在右上角（y坐标小于200）
        if span.bbox[1] < 200:
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

# 5.12 右上角应缴电费
for span in text_spans:
    if span.text.strip() == "503.69":
        # 检查位置是否在右上角
        if span.bbox[1] < 200:
            changes.append(FieldChange(
                field_name="应缴电费",
                original_value="503.69",
                new_value=str(elec_data.total_fee),
                bbox=span.bbox,
                font=span.font,
                font_size=span.font_size,
                color=span.color
            ))
            print(f"  ✓ 应缴电费")
            break

# 5.13 电表示数 - 峰段上期
for span in text_spans:
    if span.text.strip() == "9343":
        changes.append(FieldChange(
            field_name="电表示数-峰段上期",
            original_value="9343",
            new_value=str(elec_data.last_peak),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 电表示数-峰段上期")
        break

# 5.14 电表示数 - 峰段本期
for span in text_spans:
    if span.text.strip() == "10105":
        changes.append(FieldChange(
            field_name="电表示数-峰段本期",
            original_value="10105",
            new_value=str(elec_data.curr_peak),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 电表示数-峰段本期")
        break

# 5.15 电表示数 - 平段上期
for span in text_spans:
    if span.text.strip() == "2215":
        changes.append(FieldChange(
            field_name="电表示数-平段上期",
            original_value="2215",
            new_value=str(elec_data.last_flat),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 电表示数-平段上期")
        break

# 5.16 电表示数 - 平段本期
for span in text_spans:
    if span.text.strip() == "2356":
        changes.append(FieldChange(
            field_name="电表示数-平段本期",
            original_value="2356",
            new_value=str(elec_data.curr_flat),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 电表示数-平段本期")
        break

# 5.17 电表示数 - 谷段上期
for span in text_spans:
    if span.text.strip() == "3325":
        changes.append(FieldChange(
            field_name="电表示数-谷段上期",
            original_value="3325",
            new_value=str(elec_data.last_valley),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 电表示数-谷段上期")
        break

# 5.18 电表示数 - 谷段本期
for span in text_spans:
    if span.text.strip() == "3601":
        changes.append(FieldChange(
            field_name="电表示数-谷段本期",
            original_value="3601",
            new_value=str(elec_data.curr_valley),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 电表示数-谷段本期")
        break

# 5.19 峰段电量 (表格中有多个762，需要精确定位)
count_762 = 0
for span in text_spans:
    if span.text.strip() == "762":
        count_762 += 1
        # 第2个762是峰段电量（在表格中）
        if count_762 == 2:
            changes.append(FieldChange(
                field_name="峰段电量",
                original_value="762",
                new_value=str(elec_data.peak_kwh),
                bbox=span.bbox,
                font=span.font,
                font_size=span.font_size,
                color=span.color
            ))
            print(f"  ✓ 峰段电量")
            break

# 5.20 平段电量
for span in text_spans:
    if span.text.strip() == "141":
        changes.append(FieldChange(
            field_name="平段电量",
            original_value="141",
            new_value=str(elec_data.flat_kwh),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 平段电量")
        break

# 5.21 谷段电量
for span in text_spans:
    if span.text.strip() == "276":
        changes.append(FieldChange(
            field_name="谷段电量",
            original_value="276",
            new_value=str(elec_data.valley_kwh),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 谷段电量")
        break

# 5.22 峰段电费金额 (电费明细表中)
for span in text_spans:
    if span.text.strip() == "144.18":
        changes.append(FieldChange(
            field_name="峰段电费金额",
            original_value="144.18",
            new_value=str(elec_data.fee_peak),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 峰段电费金额")
        break

# 5.23 平段电费金额
for span in text_spans:
    if span.text.strip() == "180.23":
        changes.append(FieldChange(
            field_name="平段电费金额",
            original_value="180.23",
            new_value=str(elec_data.fee_flat),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 平段电费金额")
        break

# 5.24 谷段电费金额
for span in text_spans:
    if span.text.strip() == "24.68":
        changes.append(FieldChange(
            field_name="谷段电费金额",
            original_value="24.68",
            new_value=str(elec_data.fee_valley),
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 谷段电费金额")
        break

# 5.25 电费合计 (底部的￥503.69)
for span in text_spans:
    if span.text.strip() == "￥503.69":
        changes.append(FieldChange(
            field_name="电费合计",
            original_value="￥503.69",
            new_value=f"￥{elec_data.total_fee}",
            bbox=span.bbox,
            font=span.font,
            font_size=span.font_size,
            color=span.color
        ))
        print(f"  ✓ 电费合计")
        break

# 5.26 替换所有"四川"为省份名（只替换"四川"两个字）
for span in text_spans:
    if "四川" in span.text:
        new_text = span.text.replace("四川", province_short)
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

# 5.27 翻译表格标题和列标题
from translator import BillTranslator
temp_translator = BillTranslator()

label_mappings = [
    "账单详情",
    "用能分析",
    "电费明细",
    "上期示数",
    "本期示数",
    "倍率抄见电量加减变损",
    "计费电量",
    "计费标准",
    "合计",
    "费用组成",
]

for label in label_mappings:
    found = False
    for span in text_spans:
        if span.text.strip() == label and not found:
            changes.append(FieldChange(
                field_name=f"标签-{label}",
                original_value=label,
                new_value=label,  # 保持中文，翻译时会转换
                bbox=span.bbox,
                font=span.font,
                font_size=span.font_size,
                color=span.color
            ))
            print(f"  ✓ 标签-{label}")
            found = True
            break

# 5.28 翻译费用项目行
fee_items = [
    "电-居民生活-居民丰水期谷段0.175(峰)",
    "电-居民生活-居民丰水期谷段0.175(平)",
    "电-居民生活-居民丰水期谷段0.175(谷)",
]
for item in fee_items:
    for span in text_spans:
        if item in span.text:
            changes.append(FieldChange(
                field_name=f"费用项目-{item[:10]}",
                original_value=span.text,
                new_value=span.text,  # 保持原文，翻译时处理
                bbox=span.bbox,
                font=span.font,
                font_size=span.font_size,
                color=span.color
            ))
            print(f"  ✓ 费用项目-{item[:10]}")
            break

# 5.29 翻译说明文字
description_texts = [
    ("1.本期电量", "1.本期电量"),
    ("2.峰谷阶梯", "2.峰谷阶梯"),
    ("3.平均电价", "3.平均电价"),
]
for original, label in description_texts:
    for span in text_spans:
        if span.text.strip() == original:
            changes.append(FieldChange(
                field_name=f"说明-{label}",
                original_value=original,
                new_value=original,
                bbox=span.bbox,
                font=span.font,
                font_size=span.font_size,
                color=span.color
            ))
            print(f"  ✓ 说明-{label}")
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
print()

# 8. 询问是否生成法语版
print("=" * 80)
user_input = input("是否生成法语翻译版？(y/n): ").strip().lower()
if user_input == 'y':
    from translator import BillTranslator

    print()
    print("步骤8：生成法语翻译版")
    print("=" * 80)

    # 8.1 创建翻译器
    translator = BillTranslator()

    # 8.2 翻译所有字段
    print("  正在翻译字段...")
    french_changes = []
    for change in changes:
        translated_value = translator.translate_field(change.new_value)
        french_changes.append(FieldChange(
            field_name=change.field_name,
            original_value=change.original_value,
            new_value=translated_value,
            bbox=change.bbox,
            font=change.font,
            font_size=change.font_size,
            color=change.color
        ))
    print(f"  ✓ 已翻译 {len(french_changes)} 个字段")

    # 8.3 生成法语PDF
    print("  正在生成法语PDF...")
    french_output_path = output_dir / f"电费账单-{id_info.name}-{timestamp}-FR.pdf"
    orchestrator.generator.apply_changes(
        template_path,
        french_changes,
        str(french_output_path)
    )
    print(f"  ✓ 法语PDF已生成")

    # 8.4 生成法语对比图
    print("  正在生成对比图...")
    french_comparison_path = output_dir / f"电费账单-{id_info.name}-{timestamp}-FR-对比.png"
    orchestrator.generator.create_comparison_image(
        template_path,
        str(french_output_path),
        str(french_comparison_path)
    )
    print(f"  ✓ 法语对比图已生成")
    print()

    print("=" * 80)
    print("✓ 法语版生成完成！")
    print("=" * 80)
    print()
    print(f"中文版: {output_path}")
    print(f"法语版: {french_output_path}")
    print(f"法语对比图: {french_comparison_path}")
else:
    print("跳过法语翻译")
