from typing import Any
import pandas as pd
import numpy as np
from bist_signal_bot.patterns.base import BasePatternDetector
from bist_signal_bot.patterns.models import PatternSpec, PatternCategory

class RollingSupportResistanceDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="rolling_sr",
            display_name="Rolling Support/Resistance",
            category=PatternCategory.SUPPORT_RESISTANCE,
            required_columns=["high", "low", "close"],
            default_params={"window": 50},
            output_columns=[
                "rolling_resistance_{window}",
                "rolling_support_{window}",
                "distance_to_resistance_{window}",
                "distance_to_support_{window}"
            ],
            min_rows=2,
            description="Calculates SR levels based on rolling high/low windows"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        w = params["window"]

        # Calculate shifted so we don't leak current bar
        res = data["high"].rolling(w).max().shift(1)
        sup = data["low"].rolling(w).min().shift(1)

        df[f"rolling_resistance_{w}"] = res
        df[f"rolling_support_{w}"] = sup

        safe_close = data["close"].replace(0, np.nan)
        df[f"distance_to_resistance_{w}"] = (res - data["close"]) / safe_close
        df[f"distance_to_support_{w}"] = (data["close"] - sup) / safe_close

        return df

class PivotPointsDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="pivot_points",
            display_name="Pivot Points (Previous Bar)",
            category=PatternCategory.SUPPORT_RESISTANCE,
            required_columns=["high", "low", "close"],
            default_params={},
            output_columns=["pivot_point", "pivot_r1", "pivot_s1", "pivot_r2", "pivot_s2"],
            min_rows=2,
            description="Calculates standard pivot points using the previous bar's values"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)

        prev_h = data["high"].shift(1)
        prev_l = data["low"].shift(1)
        prev_c = data["close"].shift(1)

        pp = (prev_h + prev_l + prev_c) / 3

        df["pivot_point"] = pp
        df["pivot_r1"] = (2 * pp) - prev_l
        df["pivot_s1"] = (2 * pp) - prev_h
        df["pivot_r2"] = pp + (prev_h - prev_l)
        df["pivot_s2"] = pp - (prev_h - prev_l)

        return df

class SRTouchCountDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="sr_touch_count",
            display_name="Support/Resistance Touch Count",
            category=PatternCategory.SUPPORT_RESISTANCE,
            required_columns=["high", "low", "close"],
            default_params={"window": 50, "tolerance_pct": 0.01},
            output_columns=["resistance_touch_count_{window}", "support_touch_count_{window}"],
            min_rows=2,
            description="Counts the number of times price has touched the current rolling SR levels"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        w = params["window"]
        tol = params["tolerance_pct"]

        # We need to find how many times in the last w bars the high/low was within tolerance
        # of the CURRENT (shifted) rolling high/low. This is a bit complex in pandas without a loop.

        res = data["high"].rolling(w).max().shift(1)
        sup = data["low"].rolling(w).min().shift(1)

        # A simple approximation: if high > res*(1-tol), it's a touch.
        # For a full rolling count of *past* touches against the *current* line, we need an expanding/rolling apply.

        # Helper to count touches
        def count_touches(series, target, is_high=True):
            if pd.isna(target):
                return np.nan
            if is_high:
                return np.sum(series >= target * (1 - tol))
            else:
                return np.sum(series <= target * (1 + tol))

        res_touches = pd.Series(np.nan, index=data.index)
        sup_touches = pd.Series(np.nan, index=data.index)

        # Optimization: Only calculate if we have enough data
        for i in range(w, len(data)):
            window_highs = data["high"].iloc[i-w:i]
            window_lows = data["low"].iloc[i-w:i]

            res_val = res.iloc[i]
            sup_val = sup.iloc[i]

            res_touches.iloc[i] = count_touches(window_highs, res_val, True)
            sup_touches.iloc[i] = count_touches(window_lows, sup_val, False)

        df[f"resistance_touch_count_{w}"] = res_touches
        df[f"support_touch_count_{w}"] = sup_touches

        return df

class NearSRDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="near_sr",
            display_name="Near Support/Resistance",
            category=PatternCategory.SUPPORT_RESISTANCE,
            required_columns=["high", "low", "close"],
            default_params={"window": 50, "tolerance_pct": 0.02},
            output_columns=["near_resistance_{window}", "near_support_{window}"],
            min_rows=2,
            description="Flags if price is within a percentage tolerance of a support or resistance level"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        w = params["window"]
        tol = params["tolerance_pct"]

        res = data["high"].rolling(w).max().shift(1)
        sup = data["low"].rolling(w).min().shift(1)

        df[f"near_resistance_{w}"] = (data["close"] >= res * (1 - tol)).astype(float)
        df[f"near_support_{w}"] = (data["close"] <= sup * (1 + tol)).astype(float)

        return df

class SRCompositeDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="sr_composite",
            display_name="Support Resistance Composite Score",
            category=PatternCategory.SUPPORT_RESISTANCE,
            required_columns=["high", "low", "close"],
            default_params={"window": 50},
            output_columns=["sr_position_score", "sr_pressure_score"],
            min_rows=2,
            description="Aggregates SR factors into position and pressure scores"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        w = params["window"]

        rsr = RollingSupportResistanceDetector().detect(data, window=w)
        nsr = NearSRDetector().detect(data, window=w, tolerance_pct=0.02)

        res = rsr[f"rolling_resistance_{w}"]
        sup = rsr[f"rolling_support_{w}"]
        range_hl = res - sup
        safe_range = range_hl.replace(0, np.nan)

        # Position 0-100 (0=near sup, 100=near res)
        pos = (data["close"] - sup) / safe_range
        df["sr_position_score"] = (pos * 100).clip(0, 100)

        # Pressure
        pressure = pd.Series(0.0, index=data.index)
        pressure -= nsr[f"near_resistance_{w}"] * 50 # Bearish pressure if hitting resistance
        pressure += nsr[f"near_support_{w}"] * 50    # Bullish pressure if hitting support

        df["sr_pressure_score"] = pressure.clip(-100, 100)

        return df
