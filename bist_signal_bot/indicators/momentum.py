import pandas as pd
import numpy as np
from typing import Any, Dict, List

from bist_signal_bot.indicators.base import BaseIndicator
from bist_signal_bot.indicators.models import IndicatorSpec, IndicatorCategory, IndicatorBackend
from bist_signal_bot.core.exceptions import IndicatorValidationError

class MomentumIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="momentum",
                display_name="Momentum",
                category=IndicatorCategory.MOMENTUM,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"window": 10},
                output_columns=["momentum"],
                min_rows=11
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"momentum_{params['window']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        col = f"momentum_{window}"
        out = pd.DataFrame(index=data.index)
        out[col] = data['close'] - data['close'].shift(window)
        return out


class RateOfChangePercentIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="roc_pct",
                display_name="Rate of Change Percent",
                category=IndicatorCategory.MOMENTUM,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"window": 10},
                output_columns=["roc_pct"],
                min_rows=11
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"roc_pct_{params['window']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        col = f"roc_pct_{window}"
        out = pd.DataFrame(index=data.index)
        out[col] = (data['close'] / data['close'].shift(window)) - 1
        return out


class RSIEnhancedIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="rsi_enhanced",
                display_name="RSI Enhanced",
                category=IndicatorCategory.MOMENTUM,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"window": 14, "slope_window": 3, "oversold": 30.0, "overbought": 70.0},
                output_columns=["rsi", "rsi_slope", "rsi_zone", "rsi_above_50"],
                min_rows=15
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0 or params.get("slope_window", 0) <= 0:
            raise IndicatorValidationError("Windows must be positive integers.")
        ob, os = params.get("overbought", 70), params.get("oversold", 30)
        if not (0 <= os < ob <= 100):
            raise IndicatorValidationError("Invalid overbought/oversold levels.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        w, sw = params['window'], params['slope_window']
        return [
            f"rsi_{w}",
            f"rsi_slope_{w}_{sw}",
            f"rsi_zone_{w}",
            f"rsi_above_50_{w}"
        ]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        slope_window = params["slope_window"]
        ob = params["overbought"]
        os = params["oversold"]

        rsi_col = f"rsi_{window}"
        slope_col = f"rsi_slope_{window}_{slope_window}"
        zone_col = f"rsi_zone_{window}"
        above_col = f"rsi_above_50_{window}"

        out = pd.DataFrame(index=data.index)

        delta = data['close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=window - 1, adjust=False).mean()
        avg_loss = loss.ewm(com=window - 1, adjust=False).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        out[rsi_col] = rsi
        out[slope_col] = out[rsi_col].diff(slope_window)

        out[zone_col] = 0
        out.loc[out[rsi_col] >= ob, zone_col] = 1
        out.loc[out[rsi_col] <= os, zone_col] = -1
        out.loc[out[rsi_col].isna(), zone_col] = np.nan

        out[above_col] = (out[rsi_col] > 50).astype(int)
        out.loc[out[rsi_col].isna(), above_col] = np.nan

        return out


class StochasticEnhancedIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="stoch_enhanced",
                display_name="Stochastic Enhanced",
                category=IndicatorCategory.MOMENTUM,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"k_window": 14, "d_window": 3, "overbought": 80.0, "oversold": 20.0},
                output_columns=["stoch_k", "stoch_d", "stoch_state", "stoch_cross_event"],
                min_rows=16
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("k_window", 0) <= 0 or params.get("d_window", 0) <= 0:
            raise IndicatorValidationError("Windows must be positive integers.")
        ob, os = params.get("overbought", 80), params.get("oversold", 20)
        if not (0 <= os < ob <= 100):
            raise IndicatorValidationError("Invalid overbought/oversold levels.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        k, d = params['k_window'], params['d_window']
        return [
            f"stoch_k_{k}",
            f"stoch_d_{k}_{d}",
            f"stoch_state_{k}_{d}",
            f"stoch_cross_event_{k}_{d}"
        ]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        k_window = params["k_window"]
        d_window = params["d_window"]

        k_col = f"stoch_k_{k_window}"
        d_col = f"stoch_d_{k_window}_{d_window}"
        state_col = f"stoch_state_{k_window}_{d_window}"
        cross_col = f"stoch_cross_event_{k_window}_{d_window}"

        out = pd.DataFrame(index=data.index)

        roll_low = data['low'].rolling(window=k_window).min()
        roll_high = data['high'].rolling(window=k_window).max()
        out[k_col] = 100 * ((data['close'] - roll_low) / (roll_high - roll_low))
        out[d_col] = out[k_col].rolling(window=d_window).mean()

        out[state_col] = 0
        out.loc[out[k_col] > out[d_col], state_col] = 1
        out.loc[out[k_col] < out[d_col], state_col] = -1
        out.loc[out[k_col].isna() | out[d_col].isna(), state_col] = np.nan

        prev_k = out[k_col].shift(1)
        prev_d = out[d_col].shift(1)

        cross_up = (prev_k <= prev_d) & (out[k_col] > out[d_col])
        cross_down = (prev_k >= prev_d) & (out[k_col] < out[d_col])

        out[cross_col] = 0
        out.loc[cross_up, cross_col] = 1
        out.loc[cross_down, cross_col] = -1
        out.loc[out[k_col].isna() | out[d_col].isna(), cross_col] = np.nan

        return out


class WilliamsRIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="williams_r",
                display_name="Williams %R",
                category=IndicatorCategory.MOMENTUM,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"window": 14},
                output_columns=["williams_r"],
                min_rows=14
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"williams_r_{params['window']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        col = f"williams_r_{window}"
        out = pd.DataFrame(index=data.index)

        roll_high = data['high'].rolling(window=window).max()
        roll_low = data['low'].rolling(window=window).min()

        # Avoid division by zero
        denom = roll_high - roll_low
        out[col] = np.where(denom == 0, np.nan, -100 * (roll_high - data['close']) / denom)
        out[col] = out[col].astype(float) # Ensure correctly typed as float
        return out


class CCIIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="cci",
                display_name="Commodity Channel Index",
                category=IndicatorCategory.MOMENTUM,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"window": 20, "constant": 0.015},
                output_columns=["cci"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")
        if params.get("constant", 0) <= 0:
            raise IndicatorValidationError("Constant must be positive.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"cci_{params['window']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        constant = params["constant"]
        col = f"cci_{window}"
        out = pd.DataFrame(index=data.index)

        tp = (data['high'] + data['low'] + data['close']) / 3
        sma_tp = tp.rolling(window=window).mean()

        from numpy.lib.stride_tricks import sliding_window_view

        tp_arr = tp.to_numpy()

        # Determine if we have enough data to form at least one window
        if len(tp_arr) >= window:
            v = sliding_window_view(tp_arr, window_shape=window)
            means = np.mean(v, axis=1, keepdims=True)
            mads = np.mean(np.abs(v - means), axis=1)

            mad_arr = np.empty(len(tp_arr))
            mad_arr[:] = np.nan
            mad_arr[window-1:] = mads

            mad = pd.Series(mad_arr, index=tp.index)
        else:
            # If not enough data, mad is all NaNs
            mad = pd.Series(np.nan, index=tp.index)

        out[col] = np.where(mad == 0, np.nan, (tp - sma_tp) / (constant * mad))
        out[col] = out[col].astype(float)
        return out


class MFIIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="mfi",
                display_name="Money Flow Index",
                category=IndicatorCategory.MOMENTUM,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close", "volume"],
                default_params={"window": 14},
                output_columns=["mfi"],
                min_rows=15
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"mfi_{params['window']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        col = f"mfi_{window}"
        out = pd.DataFrame(index=data.index)

        tp = (data['high'] + data['low'] + data['close']) / 3
        rmf = tp * data['volume']

        tp_diff = tp.diff()
        pos_mf = np.where(tp_diff > 0, rmf, 0)
        neg_mf = np.where(tp_diff < 0, rmf, 0)

        pos_mf_sum = pd.Series(pos_mf).rolling(window=window).sum()
        neg_mf_sum = pd.Series(neg_mf).rolling(window=window).sum()

        mfi = np.where(neg_mf_sum == 0, 100, 100 - (100 / (1 + (pos_mf_sum / neg_mf_sum))))
        out[col] = pd.Series(mfi, index=data.index)
        return out


class TSIIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="tsi",
                display_name="True Strength Index",
                category=IndicatorCategory.MOMENTUM,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"slow": 25, "fast": 13, "signal": 7},
                output_columns=["tsi", "tsi_signal", "tsi_hist"],
                min_rows=40
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        slow, fast, sig = params.get("slow", 0), params.get("fast", 0), params.get("signal", 0)
        if slow <= 0 or fast <= 0 or sig <= 0:
            raise IndicatorValidationError("Windows must be positive.")
        if fast >= slow:
            raise IndicatorValidationError("Fast window must be strictly less than slow window.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        s, f, sig = params['slow'], params['fast'], params['signal']
        return [
            f"tsi_{s}_{f}",
            f"tsi_signal_{s}_{f}_{sig}",
            f"tsi_hist_{s}_{f}_{sig}"
        ]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        slow, fast, sig = params["slow"], params["fast"], params["signal"]

        tsi_col = f"tsi_{slow}_{fast}"
        sig_col = f"tsi_signal_{slow}_{fast}_{sig}"
        hist_col = f"tsi_hist_{slow}_{fast}_{sig}"

        out = pd.DataFrame(index=data.index)

        diff = data['close'].diff()
        smooth1 = diff.ewm(span=slow, adjust=False).mean()
        smooth2 = smooth1.ewm(span=fast, adjust=False).mean()

        abs_diff = diff.abs()
        abs_smooth1 = abs_diff.ewm(span=slow, adjust=False).mean()
        abs_smooth2 = abs_smooth1.ewm(span=fast, adjust=False).mean()

        out[tsi_col] = 100 * (smooth2 / abs_smooth2)
        out[sig_col] = out[tsi_col].ewm(span=sig, adjust=False).mean()
        out[hist_col] = out[tsi_col] - out[sig_col]

        return out


class UltimateOscillatorIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="ultimate_osc",
                display_name="Ultimate Oscillator",
                category=IndicatorCategory.MOMENTUM,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"short_window": 7, "medium_window": 14, "long_window": 28},
                output_columns=["ultimate_osc"],
                min_rows=29
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        s, m, l = params.get("short_window", 0), params.get("medium_window", 0), params.get("long_window", 0)
        if s <= 0 or m <= 0 or l <= 0:
            raise IndicatorValidationError("Windows must be positive.")
        if not (s < m < l):
            raise IndicatorValidationError("Ultimate oscillator windows must follow: short < medium < long.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        s, m, l = params['short_window'], params['medium_window'], params['long_window']
        return [f"ultimate_osc_{s}_{m}_{l}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        s, m, l = params["short_window"], params["medium_window"], params["long_window"]
        col = f"ultimate_osc_{s}_{m}_{l}"
        out = pd.DataFrame(index=data.index)

        prev_close = data['close'].shift(1)
        min_low_pc = pd.concat([data['low'], prev_close], axis=1).min(axis=1)
        max_high_pc = pd.concat([data['high'], prev_close], axis=1).max(axis=1)

        bp = data['close'] - min_low_pc
        tr = max_high_pc - min_low_pc

        avg_s = bp.rolling(window=s).sum() / tr.rolling(window=s).sum()
        avg_m = bp.rolling(window=m).sum() / tr.rolling(window=m).sum()
        avg_l = bp.rolling(window=l).sum() / tr.rolling(window=l).sum()

        out[col] = 100 * (4 * avg_s + 2 * avg_m + avg_l) / 7
        return out


class PPOIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="ppo",
                display_name="Percentage Price Oscillator",
                category=IndicatorCategory.MOMENTUM,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"fast": 12, "slow": 26, "signal": 9},
                output_columns=["ppo", "ppo_signal", "ppo_hist"],
                min_rows=27
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        fast, slow, sig = params.get("fast", 0), params.get("slow", 0), params.get("signal", 0)
        if fast <= 0 or slow <= 0 or sig <= 0:
            raise IndicatorValidationError("Windows must be positive.")
        if fast >= slow:
            raise IndicatorValidationError("Fast window must be strictly less than slow window.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        f, s, sig = params['fast'], params['slow'], params['signal']
        return [
            f"ppo_{f}_{s}_{sig}",
            f"ppo_signal_{f}_{s}_{sig}",
            f"ppo_hist_{f}_{s}_{sig}"
        ]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        fast, slow, sig = params["fast"], params["slow"], params["signal"]

        ppo_col = f"ppo_{fast}_{slow}_{sig}"
        sig_col = f"ppo_signal_{fast}_{slow}_{sig}"
        hist_col = f"ppo_hist_{fast}_{slow}_{sig}"

        out = pd.DataFrame(index=data.index)

        ema_f = data['close'].ewm(span=fast, adjust=False).mean()
        ema_s = data['close'].ewm(span=slow, adjust=False).mean()

        out[ppo_col] = np.where(ema_s == 0, np.nan, 100 * (ema_f - ema_s) / ema_s)
        out[ppo_col] = out[ppo_col].astype(float)
        out[sig_col] = out[ppo_col].ewm(span=sig, adjust=False).mean()
        out[hist_col] = out[ppo_col] - out[sig_col]

        return out


class KSTIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="kst",
                display_name="Know Sure Thing",
                category=IndicatorCategory.MOMENTUM,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={
                    "roc1": 10, "roc2": 15, "roc3": 20, "roc4": 30,
                    "sma1": 10, "sma2": 10, "sma3": 10, "sma4": 15,
                    "signal": 9
                },
                output_columns=["kst", "kst_signal", "kst_hist"],
                min_rows=46
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        for k, v in params.items():
            if v <= 0:
                raise IndicatorValidationError(f"Parameter {k} must be positive.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        sig = params['signal']
        return ["kst", f"kst_signal_{sig}", f"kst_hist_{sig}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        sig = params["signal"]
        sig_col = f"kst_signal_{sig}"
        hist_col = f"kst_hist_{sig}"

        out = pd.DataFrame(index=data.index)

        def calc_roc(w):
            return (data['close'] / data['close'].shift(w)) - 1

        r1 = calc_roc(params["roc1"]).rolling(window=params["sma1"]).mean()
        r2 = calc_roc(params["roc2"]).rolling(window=params["sma2"]).mean()
        r3 = calc_roc(params["roc3"]).rolling(window=params["sma3"]).mean()
        r4 = calc_roc(params["roc4"]).rolling(window=params["sma4"]).mean()

        out["kst"] = (r1 * 1) + (r2 * 2) + (r3 * 3) + (r4 * 4)
        out[sig_col] = out["kst"].rolling(window=sig).mean()
        out[hist_col] = out["kst"] - out[sig_col]

        return out


class ConnorsRSIIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="connors_rsi",
                display_name="Connors RSI",
                category=IndicatorCategory.MOMENTUM,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"rsi_window": 3, "streak_rsi_window": 2, "rank_window": 100},
                output_columns=["connors_rsi"],
                min_rows=102
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        r, s, rank = params.get("rsi_window", 0), params.get("streak_rsi_window", 0), params.get("rank_window", 0)
        if r <= 0 or s <= 0 or rank <= 0:
            raise IndicatorValidationError("Windows must be positive.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        r, s, rank = params['rsi_window'], params['streak_rsi_window'], params['rank_window']
        return [f"connors_rsi_{r}_{s}_{rank}"]

    def _calc_rsi(self, series: pd.Series, window: int) -> pd.Series:
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=window - 1, adjust=False).mean()
        avg_loss = loss.ewm(com=window - 1, adjust=False).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        r, s, rank = params["rsi_window"], params["streak_rsi_window"], params["rank_window"]
        col = f"connors_rsi_{r}_{s}_{rank}"
        out = pd.DataFrame(index=data.index)

        rsi_close = self._calc_rsi(data['close'], r)

        diff = data['close'].diff()
        streak = pd.Series(0, index=data.index)

        # Calculate streak
        current_streak = 0
        for i in range(1, len(diff)):
            if diff.iloc[i] > 0:
                current_streak = current_streak + 1 if current_streak > 0 else 1
            elif diff.iloc[i] < 0:
                current_streak = current_streak - 1 if current_streak < 0 else -1
            else:
                current_streak = 0
            streak.iloc[i] = current_streak

        rsi_streak = self._calc_rsi(streak, s)

        ret = data['close'].pct_change()
        # Calculate percentile rank
        # Use pandas rolling rank and normalize to percentage
        pct_rank = ret.rolling(window=rank).rank(pct=True) * 100

        out[col] = (rsi_close + rsi_streak + pct_rank) / 3
        return out


class MomentumStrengthCompositeIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="momentum_strength",
                display_name="Momentum Strength Composite",
                category=IndicatorCategory.MOMENTUM,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close", "volume"],
                default_params={"rsi_window": 14, "roc_window": 10, "stoch_window": 14, "mfi_window": 14},
                output_columns=["momentum_strength_score", "momentum_direction_score"],
                min_rows=16
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        for k, v in params.items():
            if v <= 0:
                raise IndicatorValidationError(f"Parameter {k} must be positive.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return ["momentum_strength_score", "momentum_direction_score"]

    def _calc_rsi(self, series: pd.Series, window: int) -> pd.Series:
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(com=window - 1, adjust=False).mean()
        avg_loss = loss.ewm(com=window - 1, adjust=False).mean()
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)

        rsi = self._calc_rsi(data['close'], params["rsi_window"])
        roc = (data['close'] / data['close'].shift(params["roc_window"])) - 1

        roll_low = data['low'].rolling(window=params["stoch_window"]).min()
        roll_high = data['high'].rolling(window=params["stoch_window"]).max()
        stoch_k = 100 * ((data['close'] - roll_low) / (roll_high - roll_low))
        stoch_d = stoch_k.rolling(window=3).mean()

        tp = (data['high'] + data['low'] + data['close']) / 3
        rmf = tp * data['volume']
        tp_diff = tp.diff()
        pos_mf = np.where(tp_diff > 0, rmf, 0)
        neg_mf = np.where(tp_diff < 0, rmf, 0)
        pos_mf_sum = pd.Series(pos_mf).rolling(window=params["mfi_window"]).sum()
        neg_mf_sum = pd.Series(neg_mf).rolling(window=params["mfi_window"]).sum()
        mfi = pd.Series(np.where(neg_mf_sum == 0, 100, 100 - (100 / (1 + (pos_mf_sum / neg_mf_sum)))), index=data.index)


        # Logic
        rsi_bull = (rsi > 50).astype(int)
        rsi_bear = (rsi < 50).astype(int)

        roc_bull = (roc > 0).astype(int)
        roc_bear = (roc < 0).astype(int)

        stoch_bull = (stoch_k > stoch_d).astype(int)
        stoch_bear = (stoch_k < stoch_d).astype(int)

        mfi_bull = (mfi > 50).astype(int)
        mfi_bear = (mfi < 50).astype(int)

        bull_score = rsi_bull + roc_bull + stoch_bull + mfi_bull
        bear_score = rsi_bear + roc_bear + stoch_bear + mfi_bear

        out["momentum_strength_score"] = ((bull_score + bear_score) / 4) * 100
        out["momentum_direction_score"] = ((bull_score - bear_score) / 4) * 100

        return out
