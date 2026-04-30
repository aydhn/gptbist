import pandas as pd
import numpy as np
from typing import Any, Dict

from bist_signal_bot.indicators.base import BaseIndicator
from bist_signal_bot.indicators.models import IndicatorSpec, IndicatorCategory, IndicatorBackend
from bist_signal_bot.core.exceptions import IndicatorValidationError

# 1. Moving Average Distance
class MovingAverageDistanceIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="ma_distance",
                display_name="Moving Average Distance",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"ma_type": "sma", "window": 20},
                output_columns=["dynamic"],
                min_rows=1
            )
        )

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        self.validate_input(data, params)
        ma_type = params.get("ma_type", "sma").lower()
        window = int(params.get("window", 20))

        if window <= 0:
            raise IndicatorValidationError(f"Window must be positive, got {window}")
        if ma_type not in ["sma", "ema"]:
            raise IndicatorValidationError(f"Invalid ma_type {ma_type}")

        result = pd.DataFrame(index=data.index)
        col_name = f"ma_distance_{ma_type}_{window}"
        self.spec.output_columns = [col_name]

        close = data["close"]
        if ma_type == "sma":
            ma = close.rolling(window=window, min_periods=1).mean()
        else:
            ma = close.ewm(span=window, adjust=False, min_periods=1).mean()

        result[col_name] = (close / ma) - 1
        return result

# 2. Moving Average Crossover State
class MovingAverageCrossoverStateIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="ma_cross_state",
                display_name="Moving Average Crossover State",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"fast": 20, "slow": 50, "ma_type": "sma"},
                output_columns=["dynamic"],
                min_rows=1
            )
        )

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        self.validate_input(data, params)
        fast = int(params.get("fast", 20))
        slow = int(params.get("slow", 50))
        ma_type = params.get("ma_type", "sma").lower()

        if fast <= 0 or slow <= 0:
            raise IndicatorValidationError("Windows must be positive")
        if fast >= slow:
            raise IndicatorValidationError("fast window must be less than slow window")
        if ma_type not in ["sma", "ema"]:
            raise IndicatorValidationError(f"Invalid ma_type {ma_type}")

        result = pd.DataFrame(index=data.index)
        col_name = f"ma_cross_state_{ma_type}_{fast}_{slow}"
        self.spec.output_columns = [col_name]

        close = data["close"]
        if ma_type == "sma":
            fast_ma = close.rolling(window=fast, min_periods=1).mean()
            slow_ma = close.rolling(window=slow, min_periods=1).mean()
        else:
            fast_ma = close.ewm(span=fast, adjust=False, min_periods=1).mean()
            slow_ma = close.ewm(span=slow, adjust=False, min_periods=1).mean()

        state = np.where(fast_ma > slow_ma, 1, np.where(fast_ma < slow_ma, -1, 0))
        # Mask where either is NaN
        mask = fast_ma.isna() | slow_ma.isna()
        result[col_name] = pd.Series(state, index=data.index).mask(mask, np.nan)
        return result

# 3. Moving Average Crossover Event
class MovingAverageCrossoverEventIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="ma_cross_event",
                display_name="Moving Average Crossover Event",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"fast": 20, "slow": 50, "ma_type": "sma"},
                output_columns=["dynamic"],
                min_rows=1
            )
        )

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        self.validate_input(data, params)
        fast = int(params.get("fast", 20))
        slow = int(params.get("slow", 50))
        ma_type = params.get("ma_type", "sma").lower()

        if fast <= 0 or slow <= 0:
            raise IndicatorValidationError("Windows must be positive")
        if fast >= slow:
            raise IndicatorValidationError("fast window must be less than slow window")
        if ma_type not in ["sma", "ema"]:
            raise IndicatorValidationError(f"Invalid ma_type {ma_type}")

        result = pd.DataFrame(index=data.index)
        col_name = f"ma_cross_event_{ma_type}_{fast}_{slow}"
        self.spec.output_columns = [col_name]

        close = data["close"]
        if ma_type == "sma":
            fast_ma = close.rolling(window=fast, min_periods=1).mean()
            slow_ma = close.rolling(window=slow, min_periods=1).mean()
        else:
            fast_ma = close.ewm(span=fast, adjust=False, min_periods=1).mean()
            slow_ma = close.ewm(span=slow, adjust=False, min_periods=1).mean()

        prev_fast = fast_ma.shift(1)
        prev_slow = slow_ma.shift(1)

        event = pd.Series(0, index=data.index, dtype=float)

        # Cross up
        cross_up = (prev_fast <= prev_slow) & (fast_ma > slow_ma)
        # Cross down
        cross_down = (prev_fast >= prev_slow) & (fast_ma < slow_ma)

        event.loc[cross_up] = 1
        event.loc[cross_down] = -1

        # Mask where either is NaN
        mask = fast_ma.isna() | slow_ma.isna() | prev_fast.isna() | prev_slow.isna()
        result[col_name] = event.mask(mask, np.nan)
        return result

# 4. Moving Average Slope
class MovingAverageSlopeIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="ma_slope",
                display_name="Moving Average Slope",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"ma_type": "sma", "window": 20, "slope_window": 5, "normalize": True},
                output_columns=["dynamic"],
                min_rows=1
            )
        )

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        self.validate_input(data, params)
        ma_type = params.get("ma_type", "sma").lower()
        window = int(params.get("window", 20))
        slope_window = int(params.get("slope_window", 5))
        normalize = bool(params.get("normalize", True))

        if window <= 0 or slope_window <= 0:
            raise IndicatorValidationError("Windows must be positive")
        if ma_type not in ["sma", "ema"]:
            raise IndicatorValidationError(f"Invalid ma_type {ma_type}")

        result = pd.DataFrame(index=data.index)
        col_name = f"ma_slope_{ma_type}_{window}_{slope_window}"
        self.spec.output_columns = [col_name]

        close = data["close"]
        if ma_type == "sma":
            ma = close.rolling(window=window, min_periods=1).mean()
        else:
            ma = close.ewm(span=window, adjust=False, min_periods=1).mean()

        diff = ma.diff(slope_window)
        if normalize:
            diff = diff / ma

        result[col_name] = diff
        return result

# 5. Price Above Moving Average
class PriceAboveMovingAverageIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="price_above_ma",
                display_name="Price Above Moving Average",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"ma_type": "sma", "window": 20},
                output_columns=["dynamic"],
                min_rows=1
            )
        )

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        self.validate_input(data, params)
        ma_type = params.get("ma_type", "sma").lower()
        window = int(params.get("window", 20))

        if window <= 0:
            raise IndicatorValidationError("Window must be positive")
        if ma_type not in ["sma", "ema"]:
            raise IndicatorValidationError(f"Invalid ma_type {ma_type}")

        result = pd.DataFrame(index=data.index)
        col_name = f"price_above_{ma_type}_{window}"
        self.spec.output_columns = [col_name]

        close = data["close"]
        if ma_type == "sma":
            ma = close.rolling(window=window, min_periods=1).mean()
        else:
            ma = close.ewm(span=window, adjust=False, min_periods=1).mean()

        above = np.where(close > ma, 1.0, 0.0)
        mask = ma.isna() | close.isna()
        result[col_name] = pd.Series(above, index=data.index).mask(mask, np.nan)
        return result

# 6. Consecutive Above / Below MA Count
class ConsecutiveAboveBelowMAIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="bars_above_below_ma",
                display_name="Consecutive Above/Below MA Count",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"ma_type": "sma", "window": 20},
                output_columns=["dynamic"],
                min_rows=1
            )
        )

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        self.validate_input(data, params)
        ma_type = params.get("ma_type", "sma").lower()
        window = int(params.get("window", 20))

        if window <= 0:
            raise IndicatorValidationError("Window must be positive")
        if ma_type not in ["sma", "ema"]:
            raise IndicatorValidationError(f"Invalid ma_type {ma_type}")

        result = pd.DataFrame(index=data.index)
        col_above = f"bars_above_{ma_type}_{window}"
        col_below = f"bars_below_{ma_type}_{window}"
        self.spec.output_columns = [col_above, col_below]

        close = data["close"]
        if ma_type == "sma":
            ma = close.rolling(window=window, min_periods=1).mean()
        else:
            ma = close.ewm(span=window, adjust=False, min_periods=1).mean()

        is_above = (close > ma)
        is_below = (close < ma)

        above_cumsum = is_above.cumsum()
        above_groups = above_cumsum - above_cumsum.where(~is_above).ffill().fillna(0)

        below_cumsum = is_below.cumsum()
        below_groups = below_cumsum - below_cumsum.where(~is_below).ffill().fillna(0)

        mask = ma.isna() | close.isna()
        result[col_above] = above_groups.mask(mask, np.nan)
        result[col_below] = below_groups.mask(mask, np.nan)
        return result

# 7. Donchian Channel
class DonchianChannelIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="donchian",
                display_name="Donchian Channel",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"window": 20},
                output_columns=["dynamic"],
                min_rows=1
            )
        )

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        self.validate_input(data, params)
        window = int(params.get("window", 20))
        if window <= 0:
            raise IndicatorValidationError("Window must be positive")

        result = pd.DataFrame(index=data.index)
        col_high = f"donchian_high_{window}"
        col_low = f"donchian_low_{window}"
        col_mid = f"donchian_mid_{window}"
        col_width = f"donchian_width_{window}"
        col_break_up = f"donchian_breakout_up_{window}"
        col_break_down = f"donchian_breakout_down_{window}"
        self.spec.output_columns = [col_high, col_low, col_mid, col_width, col_break_up, col_break_down]

        high = data["high"]
        low = data["low"]
        close = data["close"]

        dc_high = high.rolling(window=window, min_periods=1).max()
        dc_low = low.rolling(window=window, min_periods=1).min()

        result[col_high] = dc_high
        result[col_low] = dc_low
        result[col_mid] = (dc_high + dc_low) / 2
        result[col_width] = dc_high - dc_low

        prev_dc_high = high.shift(1).rolling(window=window, min_periods=1).max()
        prev_dc_low = low.shift(1).rolling(window=window, min_periods=1).min()

        break_up = np.where(close > prev_dc_high, 1.0, 0.0)
        break_down = np.where(close < prev_dc_low, 1.0, 0.0)

        mask = prev_dc_high.isna() | prev_dc_low.isna() | close.isna()
        result[col_break_up] = pd.Series(break_up, index=data.index).mask(mask, np.nan)
        result[col_break_down] = pd.Series(break_down, index=data.index).mask(mask, np.nan)

        return result

# 8. Keltner Channel
class KeltnerChannelIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="keltner",
                display_name="Keltner Channel",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"ema_window": 20, "atr_window": 14, "atr_multiplier": 2.0},
                output_columns=["dynamic"],
                min_rows=1
            )
        )

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        self.validate_input(data, params)
        ema_window = int(params.get("ema_window", 20))
        atr_window = int(params.get("atr_window", 14))
        atr_multiplier = float(params.get("atr_multiplier", 2.0))

        if ema_window <= 0 or atr_window <= 0:
            raise IndicatorValidationError("Windows must be positive")
        if atr_multiplier <= 0:
            raise IndicatorValidationError("ATR multiplier must be positive")

        result = pd.DataFrame(index=data.index)

        col_mid = f"keltner_mid_{ema_window}"
        col_upper = f"keltner_upper_{ema_window}_{atr_window}_{atr_multiplier}"
        col_lower = f"keltner_lower_{ema_window}_{atr_window}_{atr_multiplier}"
        col_width = f"keltner_width_{ema_window}_{atr_window}_{atr_multiplier}"
        col_position = f"keltner_position_{ema_window}_{atr_window}_{atr_multiplier}"
        self.spec.output_columns = [col_mid, col_upper, col_lower, col_width, col_position]

        high = data["high"]
        low = data["low"]
        close = data["close"]

        # TR calculation
        h_l = high - low
        h_pc = (high - close.shift(1)).abs()
        l_pc = (low - close.shift(1)).abs()
        tr = pd.concat([h_l, h_pc, l_pc], axis=1).max(axis=1)

        # ATR Wilder's Smoothing
        # First value is simple mean, then EMA-like
        atr = tr.ewm(alpha=1/atr_window, adjust=False, min_periods=1).mean()

        ema = close.ewm(span=ema_window, adjust=False, min_periods=1).mean()

        upper = ema + (atr_multiplier * atr)
        lower = ema - (atr_multiplier * atr)

        result[col_mid] = ema
        result[col_upper] = upper
        result[col_lower] = lower
        result[col_width] = upper - lower

        denom = upper - lower
        # handle division by zero
        safe_denom = denom.replace(0, np.nan)
        result[col_position] = (close - lower) / safe_denom

        return result

# 9. ADX / DMI
class ADXIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="adx",
                display_name="Average Directional Index",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"window": 14},
                output_columns=["dynamic"],
                min_rows=1
            )
        )

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        self.validate_input(data, params)
        window = int(params.get("window", 14))
        if window <= 0:
            raise IndicatorValidationError("Window must be positive")

        result = pd.DataFrame(index=data.index)
        col_plus_di = f"plus_di_{window}"
        col_minus_di = f"minus_di_{window}"
        col_adx = f"adx_{window}"
        col_state = f"dmi_state_{window}"
        self.spec.output_columns = [col_plus_di, col_minus_di, col_adx, col_state]

        high = data["high"]
        low = data["low"]
        close = data["close"]

        up_move = high.diff()
        down_move = low.diff() * -1

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        plus_dm = pd.Series(plus_dm, index=data.index)
        minus_dm = pd.Series(minus_dm, index=data.index)

        h_l = high - low
        h_pc = (high - close.shift(1)).abs()
        l_pc = (low - close.shift(1)).abs()
        tr = pd.concat([h_l, h_pc, l_pc], axis=1).max(axis=1)

        # Wilder's Smoothing
        atr = tr.ewm(alpha=1/window, adjust=False, min_periods=1).mean()
        plus_dm_smoothed = plus_dm.ewm(alpha=1/window, adjust=False, min_periods=1).mean()
        minus_dm_smoothed = minus_dm.ewm(alpha=1/window, adjust=False, min_periods=1).mean()

        safe_atr = atr.replace(0, np.nan)
        plus_di = 100 * (plus_dm_smoothed / safe_atr)
        minus_di = 100 * (minus_dm_smoothed / safe_atr)

        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.ewm(alpha=1/window, adjust=False, min_periods=1).mean()

        state = np.where(plus_di > minus_di, 1.0, np.where(minus_di > plus_di, -1.0, 0.0))

        result[col_plus_di] = plus_di
        result[col_minus_di] = minus_di
        result[col_adx] = adx
        mask = plus_di.isna() | minus_di.isna()
        result[col_state] = pd.Series(state, index=data.index).mask(mask, np.nan)

        return result

# 10. Aroon
class AroonIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="aroon",
                display_name="Aroon Indicator",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low"],
                default_params={"window": 25},
                output_columns=["dynamic"],
                min_rows=1
            )
        )

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        self.validate_input(data, params)
        window = int(params.get("window", 25))
        if window <= 0:
            raise IndicatorValidationError("Window must be positive")

        result = pd.DataFrame(index=data.index)
        col_up = f"aroon_up_{window}"
        col_down = f"aroon_down_{window}"
        col_osc = f"aroon_osc_{window}"
        self.spec.output_columns = [col_up, col_down, col_osc]

        high = data["high"]
        low = data["low"]

        # find the index of max/min over the window
        def aroon_up_calc(series):
            if len(series) == 0: return np.nan
            # Days since n-day high
            return 100 * (window - (len(series) - 1 - series.argmax())) / window

        def aroon_down_calc(series):
            if len(series) == 0: return np.nan
            # Days since n-day low
            return 100 * (window - (len(series) - 1 - series.argmin())) / window

        # Using rolling + apply is slow, but correct. For native pandas, we can use the following approach
        # Note: pandas rolling argmax returns the numeric index.
        # Using min_periods=window is typical for Aroon but we allow min_periods=1 for consistency

        # To avoid apply which is slow, we use rolling.apply.
        # Alternatively, loop if data is small, but pandas rolling apply is okay.
        # Days since highest high

        aroon_up = high.rolling(window=window+1, min_periods=1).apply(lambda x: 100 * (window - (len(x) - 1 - np.argmax(x))) / window, raw=True)
        aroon_down = low.rolling(window=window+1, min_periods=1).apply(lambda x: 100 * (window - (len(x) - 1 - np.argmin(x))) / window, raw=True)

        # Cap at 100 just in case min_periods causes >100 when len < window
        aroon_up = aroon_up.clip(upper=100)
        aroon_down = aroon_down.clip(upper=100)

        result[col_up] = aroon_up
        result[col_down] = aroon_down
        result[col_osc] = aroon_up - aroon_down

        return result

# 11. Ichimoku Components
class IchimokuIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="ichimoku",
                display_name="Ichimoku Cloud",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"tenkan_window": 9, "kijun_window": 26, "senkou_b_window": 52, "displacement": 26},
                output_columns=["dynamic"],
                min_rows=1
            )
        )

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        self.validate_input(data, params)
        t_win = int(params.get("tenkan_window", 9))
        k_win = int(params.get("kijun_window", 26))
        sb_win = int(params.get("senkou_b_window", 52))
        disp = int(params.get("displacement", 26))

        if t_win <= 0 or k_win <= 0 or sb_win <= 0:
            raise IndicatorValidationError("Windows must be positive")
        if disp < 0:
            raise IndicatorValidationError("Displacement cannot be negative")

        result = pd.DataFrame(index=data.index)
        col_t = f"ichimoku_tenkan_{t_win}"
        col_k = f"ichimoku_kijun_{k_win}"
        col_sa = f"ichimoku_senkou_a_raw"
        col_sb = f"ichimoku_senkou_b_raw"
        col_state = f"ichimoku_cloud_state"

        self.spec.output_columns = [col_t, col_k, col_sa, col_sb, col_state]

        high = data["high"]
        low = data["low"]
        close = data["close"]

        tenkan = (high.rolling(window=t_win, min_periods=1).max() + low.rolling(window=t_win, min_periods=1).min()) / 2
        kijun = (high.rolling(window=k_win, min_periods=1).max() + low.rolling(window=k_win, min_periods=1).min()) / 2

        senkou_a = (tenkan + kijun) / 2
        senkou_b = (high.rolling(window=sb_win, min_periods=1).max() + low.rolling(window=sb_win, min_periods=1).min()) / 2

        result[col_t] = tenkan
        result[col_k] = kijun
        result[col_sa] = senkou_a
        result[col_sb] = senkou_b

        # Cloud state based on current raw senkou values, avoiding lookahead.
        # This is a proxy since true Ichimoku shifts senkou A/B forward
        state = np.where(senkou_a > senkou_b, 1.0, np.where(senkou_b > senkou_a, -1.0, 0.0))
        mask = senkou_a.isna() | senkou_b.isna()
        result[col_state] = pd.Series(state, index=data.index).mask(mask, np.nan)

        return result

# 12. Supertrend
class SupertrendIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="supertrend",
                display_name="Supertrend",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"atr_window": 10, "multiplier": 3.0},
                output_columns=["dynamic"],
                min_rows=1
            )
        )

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        self.validate_input(data, params)
        atr_window = int(params.get("atr_window", 10))
        multiplier = float(params.get("multiplier", 3.0))

        if atr_window <= 0:
            raise IndicatorValidationError("ATR window must be positive")
        if multiplier <= 0:
            raise IndicatorValidationError("Multiplier must be positive")

        result = pd.DataFrame(index=data.index)
        col_st = f"supertrend_{atr_window}_{multiplier}"
        col_dir = f"supertrend_direction_{atr_window}_{multiplier}"
        self.spec.output_columns = [col_st, col_dir]

        high = data["high"]
        low = data["low"]
        close = data["close"]

        # TR calculation
        h_l = high - low
        h_pc = (high - close.shift(1)).abs()
        l_pc = (low - close.shift(1)).abs()
        tr = pd.concat([h_l, h_pc, l_pc], axis=1).max(axis=1)

        atr = tr.ewm(alpha=1/atr_window, adjust=False, min_periods=1).mean()

        hl2 = (high + low) / 2
        basic_upperband = hl2 + (multiplier * atr)
        basic_lowerband = hl2 - (multiplier * atr)

        # Use iterative approach for supertrend logic
        final_upperband = pd.Series(0.0, index=data.index)
        final_lowerband = pd.Series(0.0, index=data.index)
        supertrend = pd.Series(0.0, index=data.index)
        direction = pd.Series(1, index=data.index)

        # Pre-allocate numpy arrays for speed
        n = len(data)
        bu_arr = basic_upperband.values
        bl_arr = basic_lowerband.values
        close_arr = close.values

        fu_arr = np.zeros(n)
        fl_arr = np.zeros(n)
        st_arr = np.zeros(n)
        dir_arr = np.ones(n)

        fu_arr[0] = bu_arr[0]
        fl_arr[0] = bl_arr[0]
        st_arr[0] = fl_arr[0]

        for i in range(1, n):
            if pd.isna(bu_arr[i]) or pd.isna(bl_arr[i]) or pd.isna(close_arr[i]) or pd.isna(close_arr[i-1]):
                fu_arr[i] = bu_arr[i]
                fl_arr[i] = bl_arr[i]
                st_arr[i] = np.nan
                dir_arr[i] = dir_arr[i-1]
                continue

            # Upperband
            if bu_arr[i] < fu_arr[i-1] or close_arr[i-1] > fu_arr[i-1]:
                fu_arr[i] = bu_arr[i]
            else:
                fu_arr[i] = fu_arr[i-1]

            # Lowerband
            if bl_arr[i] > fl_arr[i-1] or close_arr[i-1] < fl_arr[i-1]:
                fl_arr[i] = bl_arr[i]
            else:
                fl_arr[i] = fl_arr[i-1]

            # Direction and Supertrend
            if st_arr[i-1] == fu_arr[i-1] and close_arr[i] <= fu_arr[i]:
                dir_arr[i] = -1
                st_arr[i] = fu_arr[i]
            elif st_arr[i-1] == fu_arr[i-1] and close_arr[i] >= fu_arr[i]:
                dir_arr[i] = 1
                st_arr[i] = fl_arr[i]
            elif st_arr[i-1] == fl_arr[i-1] and close_arr[i] >= fl_arr[i]:
                dir_arr[i] = 1
                st_arr[i] = fl_arr[i]
            elif st_arr[i-1] == fl_arr[i-1] and close_arr[i] <= fl_arr[i]:
                dir_arr[i] = -1
                st_arr[i] = fu_arr[i]

        result[col_st] = pd.Series(st_arr, index=data.index)
        result[col_dir] = pd.Series(dir_arr, index=data.index)

        # Mask NaNs at the beginning properly
        mask = close.isna() | atr.isna()
        result[col_st] = result[col_st].mask(mask, np.nan)
        result[col_dir] = result[col_dir].mask(mask, np.nan)

        return result

# 13. Linear Regression Slope
class LinearRegressionSlopeIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="linreg_slope",
                display_name="Linear Regression Slope",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"window": 20, "normalize": True},
                output_columns=["dynamic"],
                min_rows=1
            )
        )

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        self.validate_input(data, params)
        window = int(params.get("window", 20))
        normalize = bool(params.get("normalize", True))

        if window <= 0:
            raise IndicatorValidationError("Window must be positive")

        result = pd.DataFrame(index=data.index)
        col_name = f"linreg_slope_{window}"
        self.spec.output_columns = [col_name]

        close = data["close"]

        # Quick OLS calculation over rolling window using numpy
        def get_slope(y):
            if len(y) < 2 or np.isnan(y).any():
                return np.nan
            x = np.arange(len(y))
            # x_mean = np.mean(x), y_mean = np.mean(y)
            # slope = cov(x,y) / var(x)
            # using numpy polyfit is easy but slow over rolling.
            # cov/var is faster
            x_mean = (len(y) - 1) / 2.0
            y_mean = np.mean(y)
            numerator = np.sum((x - x_mean) * (y - y_mean))
            denominator = np.sum((x - x_mean)**2)
            if denominator == 0:
                return 0.0
            return numerator / denominator

        slope = close.rolling(window=window).apply(get_slope, raw=True)

        if normalize:
            # normalize slope by the average price in the window to get % change per bar
            mean_px = close.rolling(window=window).mean()
            slope = slope / mean_px

        result[col_name] = slope
        return result

# 14. Trend Strength Composite
class TrendStrengthCompositeIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="trend_strength",
                display_name="Trend Strength Composite Score",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"short_window": 20, "medium_window": 50, "long_window": 200, "adx_window": 14},
                output_columns=["trend_strength_score", "trend_direction_score"],
                min_rows=1
            )
        )

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        self.validate_input(data, params)
        s_win = int(params.get("short_window", 20))
        m_win = int(params.get("medium_window", 50))
        l_win = int(params.get("long_window", 200))
        adx_win = int(params.get("adx_window", 14))

        if s_win <= 0 or m_win <= 0 or l_win <= 0 or adx_win <= 0:
            raise IndicatorValidationError("Windows must be positive")
        if not (s_win < m_win < l_win):
            raise IndicatorValidationError("Windows must follow: short < medium < long")

        result = pd.DataFrame(index=data.index)

        close = data["close"]
        sma_s = close.rolling(window=s_win, min_periods=1).mean()
        sma_m = close.rolling(window=m_win, min_periods=1).mean()
        sma_l = close.rolling(window=l_win, min_periods=1).mean()

        # Calculate ADX manually here or rely on the other class?
        # Better to calculate internally to avoid dependencies for now.
        high = data["high"]
        low = data["low"]
        up_move = high.diff()
        down_move = low.diff() * -1
        plus_dm = pd.Series(np.where((up_move > down_move) & (up_move > 0), up_move, 0.0), index=data.index)
        minus_dm = pd.Series(np.where((down_move > up_move) & (down_move > 0), down_move, 0.0), index=data.index)
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)

        atr = tr.ewm(alpha=1/adx_win, adjust=False, min_periods=1).mean()
        plus_dm_sm = plus_dm.ewm(alpha=1/adx_win, adjust=False, min_periods=1).mean()
        minus_dm_sm = minus_dm.ewm(alpha=1/adx_win, adjust=False, min_periods=1).mean()

        plus_di = 100 * (plus_dm_sm / atr.replace(0, np.nan))
        minus_di = 100 * (minus_dm_sm / atr.replace(0, np.nan))
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.ewm(alpha=1/adx_win, adjust=False, min_periods=1).mean()

        # Scoring logic
        # Direction: +1 for each bullish sign, -1 for bearish
        dir_score = pd.Series(0.0, index=data.index)

        # 1. Price vs MAs (max +3/-3)
        dir_score += np.where(close > sma_s, 1, -1)
        dir_score += np.where(close > sma_m, 1, -1)
        dir_score += np.where(close > sma_l, 1, -1)

        # 2. MA crossovers (max +3/-3)
        dir_score += np.where(sma_s > sma_m, 1, -1)
        dir_score += np.where(sma_m > sma_l, 1, -1)
        dir_score += np.where(sma_s > sma_l, 1, -1)

        # 3. DI state (max +2/-2)
        dir_score += np.where(plus_di > minus_di, 2, -2)

        # 4. MA slopes (max +2/-2)
        dir_score += np.where(sma_s.diff() > 0, 1, -1)
        dir_score += np.where(sma_m.diff() > 0, 1, -1)

        # Max theoretical score is 10, min is -10. Scale to -100 to 100
        # Replace NaNs
        dir_score = dir_score / 10.0 * 100.0

        # Strength score: 0 to 100 based on ADX and alignment
        # if adx > 25, trend is strong.
        # score = adx * alignment
        alignment = dir_score.abs() / 100.0  # 0 to 1
        strength_score = adx * alignment
        strength_score = strength_score.clip(lower=0, upper=100)

        mask = close.isna() | sma_l.isna() | adx.isna()
        result["trend_strength_score"] = strength_score.mask(mask, np.nan)
        result["trend_direction_score"] = dir_score.mask(mask, np.nan)

        return result
