import pandas as pd
from typing import List, Dict, Any, Optional
from bist_signal_bot.data.providers_v2.models import DataComparisonReport

class MarketDataComparator:
    def compare(
        self,
        symbol: str,
        timeframe: str,
        left: pd.DataFrame,
        right: pd.DataFrame,
        left_source: str,
        right_source: str,
        close_tolerance_pct: float = 0.1,
        volume_tolerance_pct: float = 5.0
    ) -> DataComparisonReport:
        warnings = []

        left_count = len(left) if left is not None and not left.empty else 0
        right_count = len(right) if right is not None and not right.empty else 0

        if left_count == 0 or right_count == 0:
            return DataComparisonReport(
                symbol=symbol,
                timeframe=timeframe,
                left_source=left_source,
                right_source=right_source,
                row_count_left=left_count,
                row_count_right=right_count,
                status="FAILED",
                warnings=[f"One or both dataframes are empty. Left: {left_count}, Right: {right_count}"]
            )

        left = left.copy()
        right = right.copy()
        left['date'] = pd.to_datetime(left['date']).dt.tz_localize(None)
        right['date'] = pd.to_datetime(right['date']).dt.tz_localize(None)

        merged = pd.merge(left, right, on='date', suffixes=('_l', '_r'), how='inner')
        matching_dates = len(merged)

        if matching_dates == 0:
            return DataComparisonReport(
                symbol=symbol,
                timeframe=timeframe,
                left_source=left_source,
                right_source=right_source,
                row_count_left=left_count,
                row_count_right=right_count,
                status="FAILED",
                warnings=["No overlapping dates found between sources."]
            )

        price_diff_count, max_close_diff = self.compare_close_prices(merged, close_tolerance_pct)
        vol_diff_count, max_vol_diff = self.compare_volumes(merged, volume_tolerance_pct)

        if price_diff_count > 0:
            warnings.append(f"Found {price_diff_count} days with close price diff > {close_tolerance_pct}%")
        if vol_diff_count > 0:
            warnings.append(f"Found {vol_diff_count} days with volume diff > {volume_tolerance_pct}%")

        status = "PASSED" if not warnings else "WARNING"

        return DataComparisonReport(
            symbol=symbol,
            timeframe=timeframe,
            left_source=left_source,
            right_source=right_source,
            row_count_left=left_count,
            row_count_right=right_count,
            matching_dates=matching_dates,
            price_diff_count=price_diff_count,
            volume_diff_count=vol_diff_count,
            max_close_diff_pct=max_close_diff,
            max_volume_diff_pct=max_vol_diff,
            status=status,
            warnings=warnings
        )

    def compare_close_prices(self, merged: pd.DataFrame, tolerance_pct: float) -> tuple[int, Optional[float]]:
        if 'close_l' not in merged.columns or 'close_r' not in merged.columns:
            return 0, None

        diff_pct = (merged['close_l'] - merged['close_r']).abs() / merged['close_l'].replace(0, 1) * 100
        diff_count = (diff_pct > tolerance_pct).sum()
        max_diff = diff_pct.max() if not diff_pct.empty else None

        return int(diff_count), float(max_diff) if pd.notna(max_diff) else None

    def compare_volumes(self, merged: pd.DataFrame, tolerance_pct: float) -> tuple[int, Optional[float]]:
        if 'volume_l' not in merged.columns or 'volume_r' not in merged.columns:
            return 0, None

        diff_pct = (merged['volume_l'] - merged['volume_r']).abs() / merged['volume_l'].replace(0, 1) * 100
        diff_count = (diff_pct > tolerance_pct).sum()
        max_diff = diff_pct.max() if not diff_pct.empty else None

        return int(diff_count), float(max_diff) if pd.notna(max_diff) else None

    def build_warning_summary(self, report: DataComparisonReport) -> List[str]:
        return report.warnings
