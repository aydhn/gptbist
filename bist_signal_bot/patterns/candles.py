from typing import Any
import pandas as pd
import numpy as np
from bist_signal_bot.patterns.base import BasePatternDetector
from bist_signal_bot.patterns.models import PatternSpec, PatternCategory

class CandleBodyMetricsDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="candle_body_metrics",
            display_name="Candle Body Metrics",
            category=PatternCategory.CANDLE,
            required_columns=["open", "high", "low", "close"],
            default_params={},
            output_columns=["candle_body_pct", "candle_upper_wick_pct", "candle_lower_wick_pct", "candle_range_pct", "candle_direction"],
            min_rows=1,
            description="Calculates basic candle metrics (body %, wicks, direction)"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        body = (data["close"] - data["open"]).abs()
        range_hl = data["high"] - data["low"]

        # Replace 0 range with NaN to avoid division by zero
        safe_range = range_hl.replace(0, np.nan)

        df["candle_body_pct"] = body / safe_range
        df["candle_upper_wick_pct"] = (data["high"] - data[["open", "close"]].max(axis=1)) / safe_range
        df["candle_lower_wick_pct"] = (data[["open", "close"]].min(axis=1) - data["low"]) / safe_range
        df["candle_range_pct"] = range_hl / data["close"].shift(1) # approximate volatility measure

        conditions = [
            data["close"] > data["open"],
            data["close"] < data["open"]
        ]
        choices = [1.0, -1.0]
        df["candle_direction"] = np.select(conditions, choices, default=0.0)

        return df

class DojiDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="doji",
            display_name="Doji Pattern",
            category=PatternCategory.CANDLE,
            required_columns=["open", "high", "low", "close"],
            default_params={"body_threshold": 0.1},
            output_columns=["candle_doji_{body_threshold}"],
            min_rows=1,
            description="Detects Doji candles where body is small relative to range"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        body_threshold = params["body_threshold"]
        col_name = f"candle_doji_{body_threshold}"

        body = (data["close"] - data["open"]).abs()
        range_hl = data["high"] - data["low"]

        is_doji = (body <= range_hl * body_threshold) & (range_hl > 0)
        df[col_name] = is_doji.astype(float)
        return df

class HammerDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="hammer",
            display_name="Hammer Approximation",
            category=PatternCategory.CANDLE,
            required_columns=["open", "high", "low", "close"],
            default_params={"body_max_pct": 0.35, "lower_wick_min_ratio": 2.0, "upper_wick_max_pct": 0.25},
            output_columns=["candle_hammer", "candle_inverted_hammer"],
            min_rows=1,
            description="Approximates hammer and inverted hammer patterns"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        body = (data["close"] - data["open"]).abs()
        range_hl = data["high"] - data["low"]
        upper_wick = data["high"] - data[["open", "close"]].max(axis=1)
        lower_wick = data[["open", "close"]].min(axis=1) - data["low"]

        safe_range = range_hl.replace(0, np.nan)
        body_pct = body / safe_range

        body_max_pct = params["body_max_pct"]
        lower_wick_min_ratio = params["lower_wick_min_ratio"]
        upper_wick_max_pct = params["upper_wick_max_pct"]

        # Hammer
        is_hammer = (body_pct <= body_max_pct) & \
                    (lower_wick >= body * lower_wick_min_ratio) & \
                    ((upper_wick / safe_range) <= upper_wick_max_pct)

        # Inverted Hammer
        is_inv_hammer = (body_pct <= body_max_pct) & \
                        (upper_wick >= body * lower_wick_min_ratio) & \
                        ((lower_wick / safe_range) <= upper_wick_max_pct)

        df["candle_hammer"] = is_hammer.astype(float)
        df["candle_inverted_hammer"] = is_inv_hammer.astype(float)
        return df

class EngulfingDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="engulfing",
            display_name="Engulfing Pattern",
            category=PatternCategory.CANDLE,
            required_columns=["open", "close"],
            default_params={},
            output_columns=["bullish_engulfing", "bearish_engulfing"],
            min_rows=2,
            description="Detects bullish and bearish engulfing patterns"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        prev_open = data["open"].shift(1)
        prev_close = data["close"].shift(1)

        prev_bearish = prev_close < prev_open
        prev_bullish = prev_close > prev_open
        curr_bearish = data["close"] < data["open"]
        curr_bullish = data["close"] > data["open"]

        body_engulfs_bullish = (data["close"] > prev_open) & (data["open"] < prev_close)
        body_engulfs_bearish = (data["close"] < prev_open) & (data["open"] > prev_close)

        df["bullish_engulfing"] = (prev_bearish & curr_bullish & body_engulfs_bullish).astype(float)
        df["bearish_engulfing"] = (prev_bullish & curr_bearish & body_engulfs_bearish).astype(float)
        return df

class InsideOutsideBarDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="inside_outside_bar",
            display_name="Inside/Outside Bar",
            category=PatternCategory.CANDLE,
            required_columns=["high", "low"],
            default_params={},
            output_columns=["inside_bar", "outside_bar"],
            min_rows=2,
            description="Detects inside and outside bars based on previous bar high/low"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        prev_high = data["high"].shift(1)
        prev_low = data["low"].shift(1)

        is_inside = (data["high"] < prev_high) & (data["low"] > prev_low)
        is_outside = (data["high"] > prev_high) & (data["low"] < prev_low)

        df["inside_bar"] = is_inside.astype(float)
        df["outside_bar"] = is_outside.astype(float)
        return df

class MarubozuDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="marubozu",
            display_name="Marubozu Approximation",
            category=PatternCategory.CANDLE,
            required_columns=["open", "high", "low", "close"],
            default_params={"wick_threshold": 0.1},
            output_columns=["bullish_marubozu", "bearish_marubozu"],
            min_rows=1,
            description="Approximates full body marubozu candles"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        wick_threshold = params["wick_threshold"]

        range_hl = data["high"] - data["low"]
        safe_range = range_hl.replace(0, np.nan)
        upper_wick = data["high"] - data[["open", "close"]].max(axis=1)
        lower_wick = data[["open", "close"]].min(axis=1) - data["low"]

        is_bullish = data["close"] > data["open"]
        is_bearish = data["close"] < data["open"]

        total_wick_pct = (upper_wick + lower_wick) / safe_range
        is_marubozu = total_wick_pct <= wick_threshold

        df["bullish_marubozu"] = (is_bullish & is_marubozu).astype(float)
        df["bearish_marubozu"] = (is_bearish & is_marubozu).astype(float)
        return df

class CandleCompositeDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="candle_composite",
            display_name="Candle Composite Score",
            category=PatternCategory.CANDLE,
            required_columns=["open", "high", "low", "close"],
            default_params={},
            output_columns=["candle_pattern_score"],
            min_rows=2,
            description="Aggregates various candle patterns into a single directional score"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        score = pd.Series(0.0, index=data.index)

        # We need the features to score them, so compute them quickly
        eng = EngulfingDetector().detect(data)
        ham = HammerDetector().detect(data, **HammerDetector().spec.default_params)
        mar = MarubozuDetector().detect(data, **MarubozuDetector().spec.default_params)

        # Bullish factors (+100 max)
        score += eng["bullish_engulfing"] * 40
        score += ham["candle_hammer"] * 30
        score += mar["bullish_marubozu"] * 30

        # Bearish factors (-100 min)
        score -= eng["bearish_engulfing"] * 40
        score -= ham["candle_inverted_hammer"] * 30
        score -= mar["bearish_marubozu"] * 30

        df["candle_pattern_score"] = score.clip(-100, 100)
        return df
