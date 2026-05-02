from typing import Any
import pandas as pd
import numpy as np
from bist_signal_bot.patterns.base import BasePatternDetector
from bist_signal_bot.patterns.models import PatternSpec, PatternCategory

class PriceBreakoutDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="price_breakout",
            display_name="Price Breakout",
            category=PatternCategory.BREAKOUT,
            required_columns=["high", "low", "close"],
            default_params={"window": 20},
            output_columns=[
                "price_breakout_up_{window}",
                "price_breakout_down_{window}",
                "price_breakout_distance_up_{window}",
                "price_breakout_distance_down_{window}"
            ],
            min_rows=2,
            description="Detects price breakouts from rolling high/low windows"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        w = params["window"]

        prev_high = data["high"].rolling(w).max().shift(1)
        prev_low = data["low"].rolling(w).min().shift(1)

        brk_up = data["close"] > prev_high
        brk_down = data["close"] < prev_low

        df[f"price_breakout_up_{w}"] = brk_up.astype(float)
        df[f"price_breakout_down_{w}"] = brk_down.astype(float)

        safe_high = prev_high.replace(0, np.nan)
        safe_low = prev_low.replace(0, np.nan)

        df[f"price_breakout_distance_up_{w}"] = (data["close"] / safe_high) - 1.0
        df[f"price_breakout_distance_down_{w}"] = (data["close"] / safe_low) - 1.0

        return df

class VolumeConfirmedBreakoutDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="volume_confirmed_breakout",
            display_name="Volume Confirmed Breakout",
            category=PatternCategory.BREAKOUT,
            required_columns=["high", "low", "close", "volume"],
            default_params={"price_window": 20, "volume_window": 20, "volume_multiplier": 1.5},
            output_columns=[
                "volume_confirmed_breakout_up_{price_window}_{volume_window}",
                "volume_confirmed_breakout_down_{price_window}_{volume_window}",
                "breakout_volume_ratio_{volume_window}"
            ],
            min_rows=2,
            description="Breakouts supported by abnormally high volume"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        pw = params["price_window"]
        vw = params["volume_window"]
        mult = params["volume_multiplier"]

        prev_high = data["high"].rolling(pw).max().shift(1)
        prev_low = data["low"].rolling(pw).min().shift(1)

        prev_vol_mean = data["volume"].rolling(vw).mean().shift(1)
        safe_vol_mean = prev_vol_mean.replace(0, np.nan)
        vol_ratio = data["volume"] / safe_vol_mean

        vol_confirmed = data["volume"] > (prev_vol_mean * mult)

        brk_up = (data["close"] > prev_high) & vol_confirmed
        brk_down = (data["close"] < prev_low) & vol_confirmed

        df[f"volume_confirmed_breakout_up_{pw}_{vw}"] = brk_up.astype(float)
        df[f"volume_confirmed_breakout_down_{pw}_{vw}"] = brk_down.astype(float)
        df[f"breakout_volume_ratio_{vw}"] = vol_ratio

        return df

class LaggedFalseBreakoutDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="false_breakout",
            display_name="Lagged False Breakout",
            category=PatternCategory.BREAKOUT,
            required_columns=["high", "low", "close"],
            default_params={"window": 20, "fail_within_bars": 3},
            output_columns=[
                "false_breakout_up_lagged_{window}_{fail_within_bars}",
                "false_breakout_down_lagged_{window}_{fail_within_bars}"
            ],
            min_rows=2,
            description="Identifies historically failed breakouts without using future data"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        w = params["window"]
        lag = params["fail_within_bars"]

        # A false breakout UP happened "lag" bars ago if:
        # At t-lag, there was a breakout UP.
        # Now at t, the close is back below the t-lag breakout level.

        shifted_data = data.shift(lag)
        shifted_prev_high = data["high"].shift(lag + 1).rolling(w).max() # High before the breakout bar
        shifted_prev_low = data["low"].shift(lag + 1).rolling(w).min()

        # Was there a breakout 'lag' bars ago?
        was_brk_up = shifted_data["close"] > shifted_prev_high
        was_brk_down = shifted_data["close"] < shifted_prev_low

        # Has it failed now?
        failed_up = was_brk_up & (data["close"] < shifted_prev_high)
        failed_down = was_brk_down & (data["close"] > shifted_prev_low)

        df[f"false_breakout_up_lagged_{w}_{lag}"] = failed_up.astype(float)
        df[f"false_breakout_down_lagged_{w}_{lag}"] = failed_down.astype(float)

        return df

class BreakoutRetestDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="breakout_retest",
            display_name="Breakout Retest",
            category=PatternCategory.BREAKOUT,
            required_columns=["high", "low", "close"],
            default_params={"window": 20, "tolerance_pct": 0.01},
            output_columns=[
                "breakout_retest_up_{window}",
                "breakout_retest_down_{window}"
            ],
            min_rows=2,
            description="Detects price retesting a previous breakout level"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        w = params["window"]
        tol = params["tolerance_pct"]

        prev_high = data["high"].rolling(w).max().shift(1)
        prev_low = data["low"].rolling(w).min().shift(1)

        retest_up = (data["low"] <= prev_high * (1 + tol)) & (data["low"] >= prev_high * (1 - tol)) & (data["close"] > prev_high * (1 - tol))
        retest_down = (data["high"] >= prev_low * (1 - tol)) & (data["high"] <= prev_low * (1 + tol)) & (data["close"] < prev_low * (1 + tol))

        df[f"breakout_retest_up_{w}"] = retest_up.astype(float)
        df[f"breakout_retest_down_{w}"] = retest_down.astype(float)

        return df

class GapBreakoutDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="gap_breakout",
            display_name="Gap Breakout",
            category=PatternCategory.GAP,
            required_columns=["open", "close"],
            default_params={"gap_threshold": 0.02},
            output_columns=["gap_up_{gap_threshold}", "gap_down_{gap_threshold}"],
            min_rows=2,
            description="Detects significant gaps between previous close and current open"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)
        thresh = params["gap_threshold"]

        prev_close = data["close"].shift(1)
        safe_close = prev_close.replace(0, np.nan)
        gap_pct = (data["open"] / safe_close) - 1.0

        df[f"gap_up_{thresh}"] = (gap_pct >= thresh).astype(float)
        df[f"gap_down_{thresh}"] = (gap_pct <= -thresh).astype(float)

        return df

class BreakoutCompositeDetector(BasePatternDetector):
    @property
    def spec(self) -> PatternSpec:
        return PatternSpec(
            name="breakout_composite",
            display_name="Breakout Composite Score",
            category=PatternCategory.BREAKOUT,
            required_columns=["high", "low", "close", "volume"],
            default_params={"price_window": 20, "volume_window": 20},
            output_columns=["breakout_pressure_score", "breakout_direction_score"],
            min_rows=2,
            description="Aggregates breakout signals into direction and pressure scores"
        )

    def detect(self, data: pd.DataFrame, **params) -> pd.DataFrame:
        df = pd.DataFrame(index=data.index)

        # Calculate sub-patterns implicitly
        pb = PriceBreakoutDetector().detect(data, window=params["price_window"])
        vcb = VolumeConfirmedBreakoutDetector().detect(data, **VolumeConfirmedBreakoutDetector().spec.default_params)
        gb = GapBreakoutDetector().detect(data, **GapBreakoutDetector().spec.default_params)

        pw = params["price_window"]
        vw = params["volume_window"]

        pressure = pd.Series(0.0, index=data.index)
        direction = pd.Series(0.0, index=data.index)

        # Build direction score
        direction += pb[f"price_breakout_up_{pw}"] * 20
        direction -= pb[f"price_breakout_down_{pw}"] * 20

        # Accessing default param columns
        vol_up_col = f"volume_confirmed_breakout_up_{VolumeConfirmedBreakoutDetector().spec.default_params['price_window']}_{VolumeConfirmedBreakoutDetector().spec.default_params['volume_window']}"
        vol_down_col = f"volume_confirmed_breakout_down_{VolumeConfirmedBreakoutDetector().spec.default_params['price_window']}_{VolumeConfirmedBreakoutDetector().spec.default_params['volume_window']}"
        direction += vcb[vol_up_col] * 30
        direction -= vcb[vol_down_col] * 30

        gap_up_col = f"gap_up_{GapBreakoutDetector().spec.default_params['gap_threshold']}"
        gap_down_col = f"gap_down_{GapBreakoutDetector().spec.default_params['gap_threshold']}"
        direction += gb[gap_up_col] * 20
        direction -= gb[gap_down_col] * 20

        # Build pressure score
        pressure += pb[f"price_breakout_up_{pw}"] * 20
        pressure += pb[f"price_breakout_down_{pw}"] * 20
        pressure += vcb[vol_up_col] * 40
        pressure += vcb[vol_down_col] * 40
        pressure += gb[gap_up_col] * 20
        pressure += gb[gap_down_col] * 20

        df["breakout_pressure_score"] = pressure.clip(0, 100)
        df["breakout_direction_score"] = direction.clip(-100, 100)

        return df
