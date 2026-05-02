from typing import Any
import pandas as pd
import numpy as np
from bist_signal_bot.patterns.base import BasePatternDetector
from bist_signal_bot.patterns.models import PatternSpec, PatternCategory

class RollingHighLowDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="rolling_high_low",
            display_name="Rolling Higher High / Lower Low",
            category=PatternCategory.PRICE_STRUCTURE,
            required_columns=["high", "low"],
            default_params={"window": 20},
            output_columns=["rolling_higher_high_{window}", "rolling_lower_low_{window}"],
            min_rows=2,
            description="Detects if current bar makes a higher high or lower low relative to a rolling window"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        window = params["window"]

        prev_rolling_high = data["high"].rolling(window).max().shift(1)
        prev_rolling_low = data["low"].rolling(window).min().shift(1)

        df[f"rolling_higher_high_{window}"] = (data["high"] > prev_rolling_high).astype(float)
        df[f"rolling_lower_low_{window}"] = (data["low"] < prev_rolling_low).astype(float)

        return df

class SwingPointDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="swing_points",
            display_name="Swing High / Swing Low",
            category=PatternCategory.PRICE_STRUCTURE,
            required_columns=["high", "low"],
            default_params={"lookback": 5},
            output_columns=["swing_high_lb_{lookback}", "swing_low_lb_{lookback}"],
            min_rows=2,
            description="Detects swing points using ONLY past data (non-lookahead breakout proxy)"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        lb = params["lookback"]

        prev_max = data["high"].rolling(lb).max().shift(1)
        prev_min = data["low"].rolling(lb).min().shift(1)

        df[f"swing_high_lb_{lb}"] = (data["high"] > prev_max).astype(float)
        df[f"swing_low_lb_{lb}"] = (data["low"] < prev_min).astype(float)

        return df

class MarketStructureStateDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="market_structure_state",
            display_name="Market Structure State",
            category=PatternCategory.PRICE_STRUCTURE,
            required_columns=["high", "low", "close"],
            default_params={"window": 20},
            output_columns=["structure_state_{window}"],
            min_rows=2,
            description="Simple directional structure state proxy (1: Bullish, -1: Bearish, 0: Neutral)"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        w = params["window"]

        hh = (data["high"] > data["high"].rolling(w).max().shift(1)).astype(int)
        hl = (data["low"] > data["low"].rolling(w).min().shift(1)).astype(int)
        lh = (data["high"] < data["high"].rolling(w).max().shift(1)).astype(int)
        ll = (data["low"] < data["low"].rolling(w).min().shift(1)).astype(int)

        state = pd.Series(0.0, index=data.index)
        state.loc[(hh == 1) | (hl == 1)] = 1.0
        state.loc[(lh == 1) | (ll == 1)] = -1.0
        # If both are somehow true (rare but possible with very wild bars), we can let it be overridden or neutralized
        state.loc[((hh == 1) | (hl == 1)) & ((lh == 1) | (ll == 1))] = 0.0

        df[f"structure_state_{w}"] = state
        return df

class RangePositionDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="range_position",
            display_name="Range Position",
            category=PatternCategory.RANGE,
            required_columns=["high", "low", "close"],
            default_params={"window": 20},
            output_columns=["range_position_{window}"],
            min_rows=2,
            description="Measures where the current close is relative to the recent range"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        w = params["window"]

        rolling_high = data["high"].rolling(w).max()
        rolling_low = data["low"].rolling(w).min()
        range_hl = rolling_high - rolling_low
        safe_range = range_hl.replace(0, np.nan)

        df[f"range_position_{w}"] = (data["close"] - rolling_low) / safe_range
        return df

class RangeCompressionDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="range_compression",
            display_name="Range Compression",
            category=PatternCategory.RANGE,
            required_columns=["high", "low", "close"],
            default_params={"short_window": 10, "long_window": 50},
            output_columns=["range_compression_{short_window}_{long_window}"],
            min_rows=2,
            description="Ratio of short term average range to long term average range"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        sw = params["short_window"]
        lw = params["long_window"]

        tr = data["high"] - data["low"]
        short_atr = tr.rolling(sw).mean()
        long_atr = tr.rolling(lw).mean()

        safe_long = long_atr.replace(0, np.nan)

        df[f"range_compression_{sw}_{lw}"] = short_atr / safe_long
        return df
