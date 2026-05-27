import uuid
import numpy as np
from datetime import datetime
from typing import List, Optional, Dict

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.valuation.models import (
    ValuationMetricType, ValuationStatus, ValuationComparisonScope, ValuationBand, ValuationMultiple
)

class ValuationBandAnalyzer:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.min_history = getattr(self.settings, "VALUATION_MIN_HISTORY_POINTS", 8)
        self.ext_cheap_pct = getattr(self.settings, "VALUATION_EXTREME_CHEAP_PERCENTILE", 10.0)
        self.cheap_pct = getattr(self.settings, "VALUATION_CHEAP_PERCENTILE", 25.0)
        self.expensive_pct = getattr(self.settings, "VALUATION_EXPENSIVE_PERCENTILE", 75.0)
        self.ext_exp_pct = getattr(self.settings, "VALUATION_EXTREME_EXPENSIVE_PERCENTILE", 90.0)

    def percentile_rank(self, values: List[float], current: Optional[float]) -> Optional[float]:
        if not values or current is None:
            return None
        valid_values = [v for v in values if v is not None and not np.isnan(v)]
        if not valid_values:
            return None

        # Rank of current value within historical values
        count_below = sum(1 for v in valid_values if v < current)
        count_equal = sum(1 for v in valid_values if v == current)

        # Standard percentile formula
        pr = ((count_below + 0.5 * count_equal) / len(valid_values)) * 100.0
        return pr

    def z_score(self, values: List[float], current: Optional[float]) -> Optional[float]:
        if not values or current is None:
            return None
        valid_values = [v for v in values if v is not None and not np.isnan(v)]
        if len(valid_values) < 2:
            return None

        mean = np.mean(valid_values)
        std = np.std(valid_values, ddof=1)

        if std == 0:
            return 0.0

        return float((current - mean) / std)

    def classify_band(self, percentile_rank: Optional[float], z_score: Optional[float]) -> ValuationStatus:
        if percentile_rank is None:
            return ValuationStatus.INSUFFICIENT_DATA

        if percentile_rank <= self.ext_cheap_pct:
            return ValuationStatus.EXTREME_CHEAP
        elif percentile_rank <= self.cheap_pct:
            return ValuationStatus.CHEAP
        elif percentile_rank >= self.ext_exp_pct:
            return ValuationStatus.EXTREME_EXPENSIVE
        elif percentile_rank >= self.expensive_pct:
            return ValuationStatus.EXPENSIVE
        else:
            return ValuationStatus.FAIR

    def build_historical_band(self, symbol: str, metric_type: ValuationMetricType, history: List[ValuationMultiple]) -> ValuationBand:
        warnings = []
        valid_history = [m for m in history if m.metric_type == metric_type and m.value is not None]

        # Sort by date
        valid_history.sort(key=lambda x: x.as_of)

        current_value = valid_history[-1].value if valid_history else None
        as_of = valid_history[-1].as_of if valid_history else datetime.utcnow()

        values = [m.value for m in valid_history if m.value is not None]

        if len(values) < self.min_history:
            warnings.append(f"Insufficient history for {metric_type.value}. Found {len(values)}, minimum is {self.min_history}.")
            return ValuationBand(
                band_id=str(uuid.uuid4()),
                symbol=symbol,
                metric_type=metric_type,
                scope=ValuationComparisonScope.HISTORICAL_SELF,
                as_of=as_of,
                current_value=current_value,
                status=ValuationStatus.INSUFFICIENT_DATA,
                warnings=warnings
            )

        pr = self.percentile_rank(values, current_value)
        z = self.z_score(values, current_value)

        status = self.classify_band(pr, z)

        # Reverse logic for yields (higher yield = cheaper)
        if metric_type in [ValuationMetricType.FCF_YIELD, ValuationMetricType.EARNINGS_YIELD, ValuationMetricType.DIVIDEND_YIELD]:
             if status == ValuationStatus.EXTREME_CHEAP: status = ValuationStatus.EXTREME_EXPENSIVE
             elif status == ValuationStatus.CHEAP: status = ValuationStatus.EXPENSIVE
             elif status == ValuationStatus.EXPENSIVE: status = ValuationStatus.CHEAP
             elif status == ValuationStatus.EXTREME_EXPENSIVE: status = ValuationStatus.EXTREME_CHEAP

             if pr is not None:
                 pr = 100.0 - pr # invert percentile

        if current_value is not None and current_value < 0:
            warnings.append(f"Negative current value for {metric_type.value}; evaluation may be misleading.")
            status = ValuationStatus.WATCH

        return ValuationBand(
            band_id=str(uuid.uuid4()),
            symbol=symbol,
            metric_type=metric_type,
            scope=ValuationComparisonScope.HISTORICAL_SELF,
            as_of=as_of,
            current_value=current_value,
            historical_min=float(np.min(values)),
            historical_p25=float(np.percentile(values, 25)),
            historical_median=float(np.median(values)),
            historical_p75=float(np.percentile(values, 75)),
            historical_max=float(np.max(values)),
            percentile_rank=pr,
            z_score=z,
            status=status,
            warnings=warnings
        )

    def build_all_bands(self, symbol: str, multiples_history: List[ValuationMultiple]) -> List[ValuationBand]:
        bands = []
        metrics_present = {m.metric_type for m in multiples_history}
        for metric in metrics_present:
            band = self.build_historical_band(symbol, metric, multiples_history)
            bands.append(band)
        return bands
