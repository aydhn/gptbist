import pandas as pd
import numpy as np
from typing import Any, Dict, List
from bist_signal_bot.indicators.base import BaseIndicator
from bist_signal_bot.indicators.models import IndicatorSpec, IndicatorCategory, IndicatorBackend
from bist_signal_bot.core.exceptions import IndicatorValidationError

class SMAIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="sma",
                display_name="Simple Moving Average",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"window": 20},
                output_columns=["sma"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"sma_{params['window']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        result_col = f"sma_{window}"
        out = pd.DataFrame(index=data.index)
        out[result_col] = data['close'].rolling(window=window, min_periods=1).mean()
        return out

class EMAIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="ema",
                display_name="Exponential Moving Average",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"span": 20},
                output_columns=["ema"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("span", 0) <= 0:
            raise IndicatorValidationError("Span must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"ema_{params['span']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        span = params["span"]
        result_col = f"ema_{span}"
        out = pd.DataFrame(index=data.index)
        out[result_col] = data['close'].ewm(span=span, adjust=False).mean()
        return out

class WMAIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="wma",
                display_name="Weighted Moving Average",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"window": 20},
                output_columns=["wma"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"wma_{params['window']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        result_col = f"wma_{window}"
        out = pd.DataFrame(index=data.index)
        weights = np.arange(1, window + 1)

        def wma(x):
            if len(x) < window:
                w = weights[-len(x):]
                return np.dot(x, w) / w.sum()
            return np.dot(x, weights) / weights.sum()

        out[result_col] = data['close'].rolling(window=window, min_periods=1).apply(wma, raw=True)
        return out

class RSIIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="rsi",
                display_name="Relative Strength Index",
                category=IndicatorCategory.MOMENTUM,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"window": 14},
                output_columns=["rsi"],
                min_rows=15
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"rsi_{params['window']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        result_col = f"rsi_{window}"
        out = pd.DataFrame(index=data.index)

        delta = data['close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(alpha=1/window, adjust=False, min_periods=window).mean()
        avg_loss = loss.ewm(alpha=1/window, adjust=False, min_periods=window).mean()

        rs = avg_gain / avg_loss
        out[result_col] = 100 - (100 / (1 + rs))
        out.loc[avg_loss == 0, result_col] = 100
        out.loc[(avg_loss == 0) & (avg_gain == 0), result_col] = 50

        return out

class ROCIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="roc",
                display_name="Rate of Change",
                category=IndicatorCategory.MOMENTUM,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"window": 10},
                output_columns=["roc"],
                min_rows=11
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"roc_{params['window']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        result_col = f"roc_{window}"
        out = pd.DataFrame(index=data.index)
        out[result_col] = data['close'].pct_change(periods=window) * 100
        return out

class TrueRangeIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="tr",
                display_name="True Range",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={},
                output_columns=["tr"],
                min_rows=2
            )
        )

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return ["tr"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        high_low = data['high'] - data['low']
        high_close = (data['high'] - data['close'].shift()).abs()
        low_close = (data['low'] - data['close'].shift()).abs()

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        out["tr"] = ranges.max(axis=1)
        return out

class ATRIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="atr",
                display_name="Average True Range",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"window": 14},
                output_columns=["atr"],
                min_rows=15
            )
        )
        self.tr_indicator = TrueRangeIndicator()

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"atr_{params['window']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        result_col = f"atr_{window}"
        out = pd.DataFrame(index=data.index)

        tr_out = self.tr_indicator.calculate(data)
        out[result_col] = tr_out["tr"].ewm(alpha=1/window, adjust=False, min_periods=window).mean()
        return out

class BollingerBandsIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="bb",
                display_name="Bollinger Bands",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"window": 20, "std": 2.0},
                output_columns=["bb_mid", "bb_upper", "bb_lower", "bb_width"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")
        if params.get("std", 0) <= 0:
            raise IndicatorValidationError("Standard deviation must be positive.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        w = params['window']
        s = str(params['std']).replace('.', '_')
        return [
            f"bb_mid_{w}",
            f"bb_upper_{w}_{s}",
            f"bb_lower_{w}_{s}",
            f"bb_width_{w}_{s}"
        ]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        std_multiplier = params["std"]

        s = str(std_multiplier).replace('.', '_')
        mid_col = f"bb_mid_{window}"
        upper_col = f"bb_upper_{window}_{s}"
        lower_col = f"bb_lower_{window}_{s}"
        width_col = f"bb_width_{window}_{s}"

        out = pd.DataFrame(index=data.index)
        rolling_close = data['close'].rolling(window=window)

        out[mid_col] = rolling_close.mean()
        std_dev = rolling_close.std(ddof=0)

        out[upper_col] = out[mid_col] + (std_dev * std_multiplier)
        out[lower_col] = out[mid_col] - (std_dev * std_multiplier)
        out[width_col] = (out[upper_col] - out[lower_col]) / out[mid_col]

        return out

class MACDIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="macd",
                display_name="Moving Average Convergence Divergence",
                category=IndicatorCategory.TREND,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"fast": 12, "slow": 26, "signal": 9},
                output_columns=["macd", "macd_signal", "macd_hist"],
                min_rows=35
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        fast = params.get("fast", 0)
        slow = params.get("slow", 0)
        signal = params.get("signal", 0)

        if fast <= 0 or slow <= 0 or signal <= 0:
            raise IndicatorValidationError("Parameters fast, slow, and signal must be positive.")
        if fast >= slow:
            raise IndicatorValidationError("Fast period must be less than slow period.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        f, s, sig = params['fast'], params['slow'], params['signal']
        return [
            f"macd_{f}_{s}_{sig}",
            f"macd_signal_{f}_{s}_{sig}",
            f"macd_hist_{f}_{s}_{sig}"
        ]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        fast = params["fast"]
        slow = params["slow"]
        signal = params["signal"]

        macd_col = f"macd_{fast}_{slow}_{signal}"
        sig_col = f"macd_signal_{fast}_{slow}_{signal}"
        hist_col = f"macd_hist_{fast}_{slow}_{signal}"

        out = pd.DataFrame(index=data.index)

        ema_fast = data['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = data['close'].ewm(span=slow, adjust=False).mean()

        out[macd_col] = ema_fast - ema_slow
        out[sig_col] = out[macd_col].ewm(span=signal, adjust=False).mean()
        out[hist_col] = out[macd_col] - out[sig_col]

        return out

class StochasticIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="stoch",
                display_name="Stochastic Oscillator",
                category=IndicatorCategory.MOMENTUM,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"k_window": 14, "d_window": 3},
                output_columns=["stoch_k", "stoch_d"],
                min_rows=16
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("k_window", 0) <= 0 or params.get("d_window", 0) <= 0:
            raise IndicatorValidationError("k_window and d_window must be positive.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        k, d = params['k_window'], params['d_window']
        return [f"stoch_k_{k}", f"stoch_d_{k}_{d}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        k_window = params["k_window"]
        d_window = params["d_window"]

        k_col = f"stoch_k_{k_window}"
        d_col = f"stoch_d_{k_window}_{d_window}"

        out = pd.DataFrame(index=data.index)

        roll_low = data['low'].rolling(window=k_window).min()
        roll_high = data['high'].rolling(window=k_window).max()

        out[k_col] = 100 * ((data['close'] - roll_low) / (roll_high - roll_low))
        out[d_col] = out[k_col].rolling(window=d_window).mean()

        return out

class OBVIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="obv",
                display_name="On Balance Volume",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close", "volume"],
                default_params={},
                output_columns=["obv"],
                min_rows=2
            )
        )

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return ["obv"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        direction = np.sign(data['close'].diff())
        direction[direction == 0] = 0

        vol_adj = data['volume'] * direction
        vol_adj.iloc[0] = data['volume'].iloc[0]

        out["obv"] = vol_adj.cumsum()
        return out

class VWAPIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="vwap",
                display_name="Rolling VWAP",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close", "volume"],
                default_params={"window": 20},
                output_columns=["vwap"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"vwap_{params['window']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        result_col = f"vwap_{window}"
        out = pd.DataFrame(index=data.index)

        typical_price = (data['high'] + data['low'] + data['close']) / 3
        tp_vol = typical_price * data['volume']

        roll_tp_vol = tp_vol.rolling(window=window).sum()
        roll_vol = data['volume'].rolling(window=window).sum()

        out[result_col] = roll_tp_vol / roll_vol
        return out

class DailyReturnIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="return",
                display_name="Daily Return",
                category=IndicatorCategory.PRICE,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"periods": 1},
                output_columns=["return"],
                min_rows=2
            )
        )

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"return_{params.get('periods', 1)}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        periods = params.get("periods", 1)
        result_col = f"return_{periods}"
        out = pd.DataFrame(index=data.index)
        out[result_col] = data['close'].pct_change(periods=periods)
        return out

class LogReturnIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="log_return",
                display_name="Log Return",
                category=IndicatorCategory.PRICE,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"periods": 1},
                output_columns=["log_return"],
                min_rows=2
            )
        )

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"log_return_{params.get('periods', 1)}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        periods = params.get("periods", 1)
        result_col = f"log_return_{periods}"
        out = pd.DataFrame(index=data.index)
        out[result_col] = np.log(data['close'] / data['close'].shift(periods))
        return out

class RollingVolatilityIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="volatility",
                display_name="Rolling Volatility",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"window": 20},
                output_columns=["volatility"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"volatility_{params['window']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        result_col = f"volatility_{window}"
        out = pd.DataFrame(index=data.index)

        returns = data['close'].pct_change()
        out[result_col] = returns.rolling(window=window).std()
        return out
