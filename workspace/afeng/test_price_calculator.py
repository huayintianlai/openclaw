#!/usr/bin/env python3
"""
测试电量和电费计算
"""
from price_calculator import ElectricityCalculator

# 测试浙江省电价
print("=" * 80)
print("测试电量和电费计算")
print("=" * 80)
print()

calculator = ElectricityCalculator(province="浙江")
print(f"省份: 浙江")
print(f"电价: 峰{calculator.price_peak}, 平{calculator.price_flat}, 谷{calculator.price_valley}")
print()

# 生成3组随机数据
for i in range(3):
    print(f"--- 测试 {i+1} ---")
    data = calculator.generate_random_data()

    print(f"总电量: {data.total_kwh} kWh")
    print(f"  峰: {data.peak_kwh} kWh ({data.peak_percent}%)")
    print(f"  平: {data.flat_kwh} kWh")
    print(f"  谷: {data.valley_kwh} kWh ({data.valley_percent}%)")
    print()

    print(f"电表示数:")
    print(f"  峰: {data.last_peak} → {data.curr_peak}")
    print(f"  平: {data.last_flat} → {data.curr_flat}")
    print(f"  谷: {data.last_valley} → {data.curr_valley}")
    print()

    print(f"电费明细:")
    print(f"  峰段: {data.peak_kwh} × {calculator.price_peak} = {data.fee_peak} 元")
    print(f"  平段: {data.flat_kwh} × {calculator.price_flat} = {data.fee_flat} 元")
    print(f"  谷段: {data.valley_kwh} × {calculator.price_valley} = {data.fee_valley} 元")
    print(f"  基金: {data.fund_kwh} × {calculator.fund_rate} = {data.fund_fee} 元")
    print(f"  附加: {data.addon_kwh} × {calculator.addon_rate} = {data.addon_fee} 元")
    print(f"  合计: {data.total_fee} 元")
    print()

    print(f"统计数据:")
    print(f"  平均电价: {data.avg_price} 元/kWh")
    print(f"  环比增长: {data.growth_rate}%")
    print()

    # 验证逻辑
    calc_total = data.peak_kwh + data.flat_kwh + data.valley_kwh
    calc_fee = data.fee_peak + data.fee_flat + data.fee_valley + data.fund_fee + data.addon_fee

    print(f"验证:")
    print(f"  电量总和: {calc_total} (应该等于 {data.total_kwh}) {'✓' if calc_total == data.total_kwh else '✗'}")
    print(f"  电费总和: {round(calc_fee, 2)} (应该等于 {data.total_fee}) {'✓' if abs(calc_fee - data.total_fee) < 0.01 else '✗'}")
    print()
