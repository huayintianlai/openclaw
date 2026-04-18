#!/usr/bin/env python3
"""
电量和电费计算模块
"""
import random
from dataclasses import dataclass
from typing import Tuple


@dataclass
class ElectricityData:
    """电量和电费数据"""
    # 总电量
    total_kwh: int

    # 峰谷平电量
    peak_kwh: int
    flat_kwh: int
    valley_kwh: int

    # 电表示数
    last_peak: int
    last_flat: int
    last_valley: int
    curr_peak: int
    curr_flat: int
    curr_valley: int

    # 电费
    fee_peak: float
    fee_flat: float
    fee_valley: float
    fund_kwh: int
    fund_fee: float
    addon_kwh: int
    addon_fee: float
    total_fee: float

    # 统计数据
    avg_price: float
    growth_rate: float
    peak_percent: float
    valley_percent: float


class ElectricityCalculator:
    """电量和电费计算器"""

    def __init__(self, province: str = "浙江"):
        """
        初始化计算器

        Args:
            province: 省份名称，用于选择电价
        """
        self.province = province
        self._load_prices()

    def _load_prices(self):
        """加载电价数据"""
        # 各省电价数据库
        price_db = {
            "浙江": {
                "peak": 0.5683,
                "flat": 0.5683,
                "valley": 0.2883
            },
            "四川": {
                "peak": 0.5224,
                "flat": 0.5224,
                "valley": 0.175
            },
            "北京": {
                "peak": 0.5583,
                "flat": 0.4883,
                "valley": 0.2883
            },
            "上海": {
                "peak": 0.617,
                "flat": 0.617,
                "valley": 0.307
            },
            "广东": {
                "peak": 0.6983,
                "flat": 0.5983,
                "valley": 0.2983
            }
        }

        # 获取电价，默认使用浙江
        prices = price_db.get(self.province, price_db["浙江"])
        self.price_peak = prices["peak"]
        self.price_flat = prices["flat"]
        self.price_valley = prices["valley"]

        # 基金和附加费率（全国统一）
        self.fund_rate = 0.3
        self.addon_rate = 0.1

    def generate_random_data(self, min_kwh: int = 600, max_kwh: int = 1200) -> ElectricityData:
        """
        生成随机电量和电费数据

        Args:
            min_kwh: 最小电量
            max_kwh: 最大电量

        Returns:
            ElectricityData对象
        """
        # 1. 生成总电量
        total_kwh = random.randint(min_kwh, max_kwh)

        # 2. 峰谷平分配（参考比例: 峰45%, 平36%, 谷19%）
        peak_ratio = random.uniform(0.40, 0.50)
        flat_ratio = random.uniform(0.30, 0.40)
        valley_ratio = 1 - peak_ratio - flat_ratio

        peak_kwh = int(total_kwh * peak_ratio)
        flat_kwh = int(total_kwh * flat_ratio)
        valley_kwh = total_kwh - peak_kwh - flat_kwh

        # 3. 生成电表示数
        last_total = random.randint(10000, 50000)
        last_peak = int(last_total * 0.6)
        last_flat = int(last_total * 0.15)
        last_valley = int(last_total * 0.25)

        curr_peak = last_peak + peak_kwh
        curr_flat = last_flat + flat_kwh
        curr_valley = last_valley + valley_kwh

        # 4. 计算电费
        fee_peak = round(peak_kwh * self.price_peak, 2)
        fee_flat = round(flat_kwh * self.price_flat, 2)
        fee_valley = round(valley_kwh * self.price_valley, 2)

        # 基金和附加（按总电量比例）
        fund_kwh = int(total_kwh * 0.63)
        fund_fee = round(fund_kwh * self.fund_rate, 2)

        addon_kwh = int(total_kwh * 0.13)
        addon_fee = round(addon_kwh * self.addon_rate, 2)

        # 总电费
        total_fee = round(fee_peak + fee_flat + fee_valley + fund_fee + addon_fee, 2)

        # 5. 计算统计数据
        avg_price = round(total_fee / total_kwh, 3)
        growth_rate = round(random.uniform(-20, 30), 2)
        peak_percent = round((peak_kwh / total_kwh) * 100, 2)
        valley_percent = round((valley_kwh / total_kwh) * 100, 2)

        return ElectricityData(
            total_kwh=total_kwh,
            peak_kwh=peak_kwh,
            flat_kwh=flat_kwh,
            valley_kwh=valley_kwh,
            last_peak=last_peak,
            last_flat=last_flat,
            last_valley=last_valley,
            curr_peak=curr_peak,
            curr_flat=curr_flat,
            curr_valley=curr_valley,
            fee_peak=fee_peak,
            fee_flat=fee_flat,
            fee_valley=fee_valley,
            fund_kwh=fund_kwh,
            fund_fee=fund_fee,
            addon_kwh=addon_kwh,
            addon_fee=addon_fee,
            total_fee=total_fee,
            avg_price=avg_price,
            growth_rate=growth_rate,
            peak_percent=peak_percent,
            valley_percent=valley_percent
        )
