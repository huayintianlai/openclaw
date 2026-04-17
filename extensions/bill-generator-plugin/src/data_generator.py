"""Electricity Data Generator - Generate realistic electricity usage and billing data"""
import random
from dataclasses import dataclass
from typing import Tuple

@dataclass
class ElectricityData:
    """Generated electricity usage and billing data"""
    # Total usage
    total_kwh: int

    # Peak/Normal/Valley breakdown
    peak_kwh: int
    normal_kwh: int
    valley_kwh: int

    # Meter readings
    prev_total_reading: int
    curr_total_reading: int
    prev_valley_reading: int
    curr_valley_reading: int
    prev_peak_reading: int
    curr_peak_reading: int

    # Fees
    peak_fee: float
    normal_fee: float
    valley_fee: float
    tier2_surcharge: float
    tier3_surcharge: float
    total_fee: float
    avg_price: float

    # Tier breakdown
    tier2_kwh: int
    tier3_kwh: int

class ElectricityDataGenerator:
    """Generate realistic electricity usage data following Zhejiang Province rules"""

    # Zhejiang Province peak/valley pricing (Tier 1 base prices)
    PEAK_PRICE = 0.568      # Peak hours
    NORMAL_PRICE = 0.568    # Normal hours
    VALLEY_PRICE = 0.288    # Valley hours

    # Tier surcharge prices
    TIER2_SURCHARGE = 0.05  # Tier 2: 230-400 kWh
    TIER3_SURCHARGE = 0.30  # Tier 3: >400 kWh

    def generate(self, min_kwh: int = 200, max_kwh: int = 800) -> ElectricityData:
        """
        Generate electricity usage data

        Args:
            min_kwh: Minimum monthly usage (default 200)
            max_kwh: Maximum monthly usage (default 800)

        Returns:
            ElectricityData object with all calculated fields
        """
        # 1. Generate total usage
        total_kwh = random.randint(min_kwh, max_kwh)

        # 2. Generate peak/normal/valley ratios
        peak_ratio = random.uniform(0.35, 0.40)
        valley_ratio = random.uniform(0.20, 0.25)
        normal_ratio = 1.0 - peak_ratio - valley_ratio

        # 3. Calculate peak/normal/valley usage
        peak_kwh = round(total_kwh * peak_ratio)
        valley_kwh = round(total_kwh * valley_ratio)
        normal_kwh = total_kwh - peak_kwh - valley_kwh  # Ensure sum equals total

        # 4. Generate meter readings
        base_reading = random.randint(8000, 12000)
        prev_total_reading = base_reading
        curr_total_reading = prev_total_reading + total_kwh

        # Valley readings
        valley_base = random.randint(2000, 3000)
        prev_valley_reading = valley_base
        curr_valley_reading = prev_valley_reading + valley_kwh

        # Peak readings
        peak_base = random.randint(3000, 4000)
        prev_peak_reading = peak_base
        curr_peak_reading = prev_peak_reading + peak_kwh

        # 5. Calculate fees
        billing = self._calculate_billing(total_kwh, peak_kwh, normal_kwh, valley_kwh)

        return ElectricityData(
            total_kwh=total_kwh,
            peak_kwh=peak_kwh,
            normal_kwh=normal_kwh,
            valley_kwh=valley_kwh,
            prev_total_reading=prev_total_reading,
            curr_total_reading=curr_total_reading,
            prev_valley_reading=prev_valley_reading,
            curr_valley_reading=curr_valley_reading,
            prev_peak_reading=prev_peak_reading,
            curr_peak_reading=curr_peak_reading,
            peak_fee=billing['peak_fee'],
            normal_fee=billing['normal_fee'],
            valley_fee=billing['valley_fee'],
            tier2_surcharge=billing['tier2_surcharge'],
            tier3_surcharge=billing['tier3_surcharge'],
            total_fee=billing['total_fee'],
            avg_price=billing['avg_price'],
            tier2_kwh=billing['tier2_kwh'],
            tier3_kwh=billing['tier3_kwh']
        )

    def _calculate_billing(self, total_kwh: int, peak_kwh: int, normal_kwh: int, valley_kwh: int) -> dict:
        """
        Calculate billing based on Zhejiang Province rules

        Args:
            total_kwh: Total monthly usage
            peak_kwh: Peak hours usage
            normal_kwh: Normal hours usage
            valley_kwh: Valley hours usage

        Returns:
            Dictionary with all fee calculations
        """
        # 1. Calculate base fees (Tier 1 prices)
        peak_fee = round(peak_kwh * self.PEAK_PRICE, 2)
        normal_fee = round(normal_kwh * self.NORMAL_PRICE, 2)
        valley_fee = round(valley_kwh * self.VALLEY_PRICE, 2)

        # 2. Calculate tier surcharges based on monthly usage
        tier2_kwh = 0
        tier2_surcharge = 0.0
        tier3_kwh = 0
        tier3_surcharge = 0.0

        if total_kwh > 230:
            # Tier 2: 230-400 kWh, surcharge 0.05 yuan/kWh
            tier2_kwh = min(total_kwh - 230, 170)  # Max 170 kWh in tier 2
            tier2_surcharge = round(tier2_kwh * self.TIER2_SURCHARGE, 2)

        if total_kwh > 400:
            # Tier 3: >400 kWh, surcharge 0.30 yuan/kWh
            tier3_kwh = total_kwh - 400
            tier3_surcharge = round(tier3_kwh * self.TIER3_SURCHARGE, 2)

        # 3. Calculate total fee
        total_fee = round(peak_fee + normal_fee + valley_fee + tier2_surcharge + tier3_surcharge, 2)

        # 4. Calculate average price
        avg_price = round(total_fee / total_kwh, 4) if total_kwh > 0 else 0.0

        return {
            'peak_fee': peak_fee,
            'normal_fee': normal_fee,
            'valley_fee': valley_fee,
            'tier2_kwh': tier2_kwh,
            'tier2_surcharge': tier2_surcharge,
            'tier3_kwh': tier3_kwh,
            'tier3_surcharge': tier3_surcharge,
            'total_fee': total_fee,
            'avg_price': avg_price
        }
