from typing import Any, Dict, List
import pandas as pd
import numpy as np

from bist_signal_bot.indicators.base import BaseIndicator
from bist_signal_bot.indicators.models import IndicatorSpec, IndicatorCategory, IndicatorBackend
from bist_signal_bot.core.exceptions import IndicatorValidationError

class VolumeSMAIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="volume_sma",
                display_name="Volume Simple Moving Average",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["volume"],
                default_params={"window": 20},
                output_columns=["volume_sma"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        window = params["window"]
        col_name = self.build_column_name("volume_sma", params)
        out[col_name] = data['volume'].rolling(window=window, min_periods=window).mean()
        return out


class VolumeEMAIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="volume_ema",
                display_name="Volume Exponential Moving Average",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["volume"],
                default_params={"span": 20},
                output_columns=["volume_ema"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("span", 0) <= 0:
            raise IndicatorValidationError("Span must be a positive integer.")

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        span = params["span"]
        col_name = self.build_column_name("volume_ema", params)
        out[col_name] = data['volume'].ewm(span=span, adjust=False, min_periods=span).mean()
        return out


class VolumeRatioIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="volume_ratio",
                display_name="Volume Ratio",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["volume"],
                default_params={"window": 20},
                output_columns=["volume_ratio"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        window = params["window"]
        col_name = self.build_column_name("volume_ratio", params)
        sma = data['volume'].rolling(window=window, min_periods=window).mean()
        # safe division
        ratio = data['volume'] / sma
        ratio = ratio.replace([np.inf, -np.inf], np.nan)
        out[col_name] = ratio
        return out


class VolumeROCIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="volume_roc",
                display_name="Volume Rate of Change",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["volume"],
                default_params={"window": 10},
                output_columns=["volume_roc"],
                min_rows=10
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        window = params["window"]
        col_name = self.build_column_name("volume_roc", params)
        shifted = data['volume'].shift(window)
        roc = (data['volume'] / shifted) - 1
        roc = roc.replace([np.inf, -np.inf], np.nan)
        out[col_name] = roc
        return out

class VolumeZScoreIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="volume_zscore",
                display_name="Volume Z-Score",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["volume"],
                default_params={"window": 20},
                output_columns=["volume_zscore"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        window = params["window"]
        col_name = self.build_column_name("volume_zscore", params)

        rolling_mean = data['volume'].rolling(window=window, min_periods=window).mean()
        rolling_std = data['volume'].rolling(window=window, min_periods=window).std()

        zscore = (data['volume'] - rolling_mean) / rolling_std
        zscore = zscore.replace([np.inf, -np.inf], np.nan)

        out[col_name] = zscore
        return out


class VolumeSpikeIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="volume_spike",
                display_name="Volume Spike Indicator",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["volume"],
                default_params={"window": 20, "multiplier": 2.0, "use_previous_baseline": True},
                output_columns=["volume_spike", "volume_spike_ratio"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")
        if params.get("multiplier", 0.0) <= 0:
            raise IndicatorValidationError("Multiplier must be positive.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        window = params.get("window", 20)
        multiplier = params.get("multiplier", 2.0)
        mult_str = str(multiplier).replace('.', '_')
        return [
            f"volume_spike_{window}_{mult_str}",
            f"volume_spike_ratio_{window}"
        ]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        window = params["window"]
        multiplier = params["multiplier"]
        use_prev = params.get("use_previous_baseline", True)

        mult_str = str(multiplier).replace('.', '_')
        spike_col = f"volume_spike_{window}_{mult_str}"
        ratio_col = f"volume_spike_ratio_{window}"

        rolling_mean = data['volume'].rolling(window=window, min_periods=window).mean()

        if use_prev:
            baseline = rolling_mean.shift(1)
        else:
            baseline = rolling_mean

        ratio = data['volume'] / baseline
        ratio = ratio.replace([np.inf, -np.inf], np.nan)

        spike = (data['volume'] > (baseline * multiplier)).astype(int)
        spike.loc[baseline.isna()] = np.nan

        out[spike_col] = spike
        out[ratio_col] = ratio
        return out


class TurnoverTRYProxyIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="turnover_try",
                display_name="Turnover TRY Proxy",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close", "volume"],
                default_params={"price_col": "close", "window": 20},
                output_columns=["turnover_try", "turnover_try_sma"],
                min_rows=1
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")
        if params.get("price_col") not in data.columns:
            raise IndicatorValidationError(f"Price column '{params.get('price_col')}' missing.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        window = params.get("window", 20)
        return [
            "turnover_try",
            f"turnover_try_sma_{window}"
        ]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        window = params["window"]
        price_col = params["price_col"]

        turnover = data[price_col] * data['volume']
        out["turnover_try"] = turnover
        out[f"turnover_try_sma_{window}"] = turnover.rolling(window=window, min_periods=1).mean()

        return out


class VWMAIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="vwma",
                display_name="Volume Weighted Moving Average",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close", "volume"],
                default_params={"window": 20},
                output_columns=["vwma"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        window = params["window"]
        col_name = self.build_column_name("vwma", params)

        pv = data['close'] * data['volume']
        rolling_pv = pv.rolling(window=window, min_periods=window).sum()
        rolling_vol = data['volume'].rolling(window=window, min_periods=window).sum()

        vwma = rolling_pv / rolling_vol
        vwma = vwma.replace([np.inf, -np.inf], np.nan)
        out[col_name] = vwma
        return out


class VWMADistanceIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="vwma_distance",
                display_name="VWMA Distance",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close", "volume"],
                default_params={"window": 20},
                output_columns=["vwma_distance"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        window = params["window"]
        col_name = self.build_column_name("vwma_distance", params)

        pv = data['close'] * data['volume']
        rolling_pv = pv.rolling(window=window, min_periods=window).sum()
        rolling_vol = data['volume'].rolling(window=window, min_periods=window).sum()

        vwma = rolling_pv / rolling_vol
        vwma = vwma.replace([np.inf, -np.inf], np.nan)

        dist = (data['close'] / vwma) - 1
        dist = dist.replace([np.inf, -np.inf], np.nan)
        out[col_name] = dist
        return out


class ADLIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="adl",
                display_name="Accumulation / Distribution Line",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close", "volume"],
                default_params={},
                output_columns=["adl"],
                min_rows=1
            )
        )

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return ["adl"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)

        num = (data['close'] - data['low']) - (data['high'] - data['close'])
        den = data['high'] - data['low']

        mf_mult = num / den
        mf_mult = mf_mult.replace([np.inf, -np.inf, np.nan], 0.0)

        mf_vol = mf_mult * data['volume']
        out["adl"] = mf_vol.cumsum()
        return out


class CMFIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="cmf",
                display_name="Chaikin Money Flow",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close", "volume"],
                default_params={"window": 20},
                output_columns=["cmf"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        window = params["window"]
        col_name = self.build_column_name("cmf", params)

        num = (data['close'] - data['low']) - (data['high'] - data['close'])
        den = data['high'] - data['low']

        mf_mult = num / den
        mf_mult = mf_mult.replace([np.inf, -np.inf, np.nan], 0.0)

        mf_vol = mf_mult * data['volume']

        rolling_mf_vol = mf_vol.rolling(window=window, min_periods=window).sum()
        rolling_vol = data['volume'].rolling(window=window, min_periods=window).sum()

        cmf = rolling_mf_vol / rolling_vol
        cmf = cmf.replace([np.inf, -np.inf], np.nan)
        out[col_name] = cmf
        return out


class ChaikinOscillatorIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="chaikin_osc",
                display_name="Chaikin Oscillator",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close", "volume"],
                default_params={"fast": 3, "slow": 10},
                output_columns=["chaikin_osc"],
                min_rows=10
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        fast = params.get("fast", 0)
        slow = params.get("slow", 0)
        if fast <= 0 or slow <= 0:
            raise IndicatorValidationError("Fast and slow must be positive integers.")
        if fast >= slow:
            raise IndicatorValidationError("Fast period must be less than slow period.")

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        fast = params["fast"]
        slow = params["slow"]
        col_name = f"chaikin_osc_{fast}_{slow}"

        num = (data['close'] - data['low']) - (data['high'] - data['close'])
        den = data['high'] - data['low']

        mf_mult = num / den
        mf_mult = mf_mult.replace([np.inf, -np.inf, np.nan], 0.0)
        mf_vol = mf_mult * data['volume']
        adl = mf_vol.cumsum()

        ema_fast = adl.ewm(span=fast, adjust=False, min_periods=fast).mean()
        ema_slow = adl.ewm(span=slow, adjust=False, min_periods=slow).mean()

        out[col_name] = ema_fast - ema_slow
        return out


class PVTIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="pvt",
                display_name="Price Volume Trend",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close", "volume"],
                default_params={},
                output_columns=["pvt"],
                min_rows=2
            )
        )

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return ["pvt"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        pct_change = data['close'].pct_change()
        pct_change = pct_change.replace([np.inf, -np.inf, np.nan], 0.0)
        pvt_step = data['volume'] * pct_change
        out["pvt"] = pvt_step.cumsum()
        return out


class ForceIndexIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="force_index",
                display_name="Force Index",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close", "volume"],
                default_params={"ema_span": 13},
                output_columns=["force_index", "force_index_ema"],
                min_rows=13
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("ema_span", 0) <= 0:
            raise IndicatorValidationError("ema_span must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        span = params.get("ema_span", 13)
        return ["force_index", f"force_index_ema_{span}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        span = params["ema_span"]

        fi = data['close'].diff() * data['volume']
        out["force_index"] = fi
        out[f"force_index_ema_{span}"] = fi.ewm(span=span, adjust=False, min_periods=span).mean()

        return out


class EaseOfMovementIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="ease_of_movement",
                display_name="Ease of Movement",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "volume"],
                default_params={"window": 14},
                output_columns=["eom", "eom_sma"],
                min_rows=14
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        window = params.get("window", 14)
        return ["eom", f"eom_sma_{window}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        window = params["window"]

        midpoint = (data['high'] + data['low']) / 2
        distance_moved = midpoint - midpoint.shift(1)

        box_ratio = data['volume'] / (data['high'] - data['low'])
        box_ratio = box_ratio.replace([np.inf, -np.inf, 0], np.nan)

        eom = distance_moved / box_ratio
        eom = eom.replace([np.inf, -np.inf], np.nan)

        out["eom"] = eom
        out[f"eom_sma_{window}"] = eom.rolling(window=window, min_periods=window).mean()

        return out

class NVIIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="nvi",
                display_name="Negative Volume Index",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close", "volume"],
                default_params={},
                output_columns=["nvi"],
                min_rows=2
            )
        )

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return ["nvi"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)

        pct_change = data['close'].pct_change()
        pct_change = pct_change.replace([np.inf, -np.inf, np.nan], 0.0)

        vol_change = data['volume'].diff()

        nvi = np.zeros(len(data))
        nvi[0] = 1000.0

        for i in range(1, len(data)):
            if vol_change.iloc[i] < 0:
                nvi[i] = nvi[i-1] * (1.0 + pct_change.iloc[i])
            else:
                nvi[i] = nvi[i-1]

        out["nvi"] = nvi
        if len(data) > 0:
            out.iloc[0, out.columns.get_loc("nvi")] = np.nan
        return out


class PVIIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="pvi",
                display_name="Positive Volume Index",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close", "volume"],
                default_params={},
                output_columns=["pvi"],
                min_rows=2
            )
        )

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return ["pvi"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)

        pct_change = data['close'].pct_change()
        pct_change = pct_change.replace([np.inf, -np.inf, np.nan], 0.0)

        vol_change = data['volume'].diff()

        pvi = np.zeros(len(data))
        pvi[0] = 1000.0

        for i in range(1, len(data)):
            if vol_change.iloc[i] > 0:
                pvi[i] = pvi[i-1] * (1.0 + pct_change.iloc[i])
            else:
                pvi[i] = pvi[i-1]

        out["pvi"] = pvi
        if len(data) > 0:
            out.iloc[0, out.columns.get_loc("pvi")] = np.nan
        return out


class KVOIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="kvo",
                display_name="Klinger Volume Oscillator",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close", "volume"],
                default_params={"fast": 34, "slow": 55, "signal": 13},
                output_columns=["kvo", "kvo_signal", "kvo_hist"],
                min_rows=55
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        fast = params.get("fast", 34)
        slow = params.get("slow", 55)
        signal = params.get("signal", 13)
        if fast <= 0 or slow <= 0 or signal <= 0:
            raise IndicatorValidationError("Parameters must be positive integers.")
        if fast >= slow:
            raise IndicatorValidationError("Fast period must be less than slow period.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        fast = params.get("fast", 34)
        slow = params.get("slow", 55)
        signal = params.get("signal", 13)
        return [
            f"kvo_{fast}_{slow}",
            f"kvo_signal_{fast}_{slow}_{signal}",
            f"kvo_hist_{fast}_{slow}_{signal}"
        ]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        fast = params["fast"]
        slow = params["slow"]
        signal = params["signal"]

        kvo_col = f"kvo_{fast}_{slow}"
        sig_col = f"kvo_signal_{fast}_{slow}_{signal}"
        hist_col = f"kvo_hist_{fast}_{slow}_{signal}"

        tp = (data['high'] + data['low'] + data['close']) / 3
        trend = np.where(tp > tp.shift(1), 1, np.where(tp < tp.shift(1), -1, 0))
        vf = data['volume'] * np.abs(2 * (tp - tp.shift(1))) * trend

        ema_fast = vf.ewm(span=fast, adjust=False, min_periods=fast).mean()
        ema_slow = vf.ewm(span=slow, adjust=False, min_periods=slow).mean()

        kvo = ema_fast - ema_slow
        out[kvo_col] = kvo
        out[sig_col] = kvo.ewm(span=signal, adjust=False, min_periods=signal).mean()
        out[hist_col] = out[kvo_col] - out[sig_col]

        return out


class VWAPEnhancedIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="vwap_enhanced",
                display_name="Enhanced Rolling VWAP",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close", "volume"],
                default_params={"window": 20},
                output_columns=["vwap", "vwap_distance"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        window = params.get("window", 20)
        return [f"vwap_{window}", f"vwap_distance_{window}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        window = params["window"]

        tp = (data['high'] + data['low'] + data['close']) / 3
        pv = tp * data['volume']

        rolling_pv = pv.rolling(window=window, min_periods=window).sum()
        rolling_vol = data['volume'].rolling(window=window, min_periods=window).sum()

        vwap = rolling_pv / rolling_vol
        vwap = vwap.replace([np.inf, -np.inf], np.nan)

        dist = (data['close'] / vwap) - 1
        dist = dist.replace([np.inf, -np.inf], np.nan)

        out[f"vwap_{window}"] = vwap
        out[f"vwap_distance_{window}"] = dist
        return out


class OBVEnhancedIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="obv_enhanced",
                display_name="Enhanced On Balance Volume",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close", "volume"],
                default_params={"slope_window": 5},
                output_columns=["obv", "obv_slope", "obv_direction"],
                min_rows=5
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("slope_window", 0) <= 0:
            raise IndicatorValidationError("Slope window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        window = params.get("slope_window", 5)
        return ["obv", f"obv_slope_{window}", f"obv_direction_{window}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        window = params["slope_window"]

        direction = np.sign(data['close'].diff())
        direction = direction.fillna(0)
        vol_dir = direction * data['volume']
        obv = vol_dir.cumsum()

        slope = obv.diff(window)

        out["obv"] = obv
        out[f"obv_slope_{window}"] = slope

        obv_dir = np.sign(slope)
        obv_dir = obv_dir.replace([np.inf, -np.inf, np.nan], 0.0)

        out[f"obv_direction_{window}"] = obv_dir
        return out

class VolumeBreakoutConfirmationIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="volume_breakout",
                display_name="Volume Breakout Confirmation",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "close", "volume"],
                default_params={"volume_window": 20, "price_window": 20, "volume_multiplier": 1.5},
                output_columns=["volume_breakout_confirm", "volume_breakout_score"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("volume_window", 0) <= 0 or params.get("price_window", 0) <= 0:
            raise IndicatorValidationError("Windows must be positive integers.")
        if params.get("volume_multiplier", 0.0) <= 0:
            raise IndicatorValidationError("Multiplier must be positive.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        vw = params.get("volume_window", 20)
        pw = params.get("price_window", 20)
        return [
            f"volume_breakout_confirm_{pw}_{vw}",
            f"volume_breakout_score_{pw}_{vw}"
        ]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        vw = params["volume_window"]
        pw = params["price_window"]
        mult = params["volume_multiplier"]

        conf_col = f"volume_breakout_confirm_{pw}_{vw}"
        score_col = f"volume_breakout_score_{pw}_{vw}"

        prev_high = data['high'].rolling(window=pw, min_periods=pw).max().shift(1)
        vol_baseline = data['volume'].rolling(window=vw, min_periods=vw).mean().shift(1)

        is_price_breakout = data['close'] > prev_high
        is_vol_breakout = data['volume'] > (vol_baseline * mult)

        confirm = (is_price_breakout & is_vol_breakout).astype(int)

        price_dist = ((data['close'] / prev_high) - 1).clip(lower=0) * 1000
        vol_dist = (data['volume'] / vol_baseline).clip(lower=0) * 10

        score = (price_dist + vol_dist).clip(lower=0, upper=100)

        confirm.loc[vol_baseline.isna() | prev_high.isna()] = np.nan
        score.loc[vol_baseline.isna() | prev_high.isna()] = np.nan

        out[conf_col] = confirm
        out[score_col] = score
        return out


class LiquidityScoreIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="liquidity_score",
                display_name="Liquidity Score",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close", "volume"],
                default_params={"window": 20, "min_turnover_try": 1000000.0},
                output_columns=["liquidity_turnover_sma", "liquidity_score"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")
        if params.get("min_turnover_try", -1) < 0:
            raise IndicatorValidationError("min_turnover_try cannot be negative.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        window = params.get("window", 20)
        return [
            f"liquidity_turnover_sma_{window}",
            f"liquidity_score_{window}"
        ]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        window = params["window"]
        min_t = params["min_turnover_try"]

        turnover = data['close'] * data['volume']
        sma_t = turnover.rolling(window=window, min_periods=window).mean()

        score = (sma_t / min_t) * 50
        score = score.clip(lower=0, upper=100)

        out[f"liquidity_turnover_sma_{window}"] = sma_t
        out[f"liquidity_score_{window}"] = score
        return out


class VolumeCompositeScoreIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="volume_composite",
                display_name="Volume Composite Score",
                category=IndicatorCategory.VOLUME,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close", "volume"],
                default_params={"volume_window": 20, "price_window": 20},
                output_columns=["volume_activity_score", "volume_pressure_score"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("volume_window", 0) <= 0 or params.get("price_window", 0) <= 0:
            raise IndicatorValidationError("Windows must be positive integers.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return ["volume_activity_score", "volume_pressure_score"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        out = pd.DataFrame(index=data.index)
        vw = params["volume_window"]
        pw = params["price_window"]

        vol_mean = data['volume'].rolling(window=vw, min_periods=vw).mean()
        vol_std = data['volume'].rolling(window=vw, min_periods=vw).std()

        zscore = (data['volume'] - vol_mean) / vol_std

        act_score = (zscore + 3) * (100 / 6)
        act_score = act_score.clip(lower=0, upper=100)

        num = (data['close'] - data['low']) - (data['high'] - data['close'])
        den = data['high'] - data['low']
        mf_mult = num / den
        mf_mult = mf_mult.replace([np.inf, -np.inf, np.nan], 0.0)

        mf_vol = mf_mult * data['volume']
        rolling_mf_vol = mf_vol.rolling(window=vw, min_periods=vw).sum()
        rolling_vol = data['volume'].rolling(window=vw, min_periods=vw).sum()
        cmf = rolling_mf_vol / rolling_vol

        pres_score = cmf * 100
        pres_score = pres_score.clip(lower=-100, upper=100)

        out["volume_activity_score"] = act_score
        out["volume_pressure_score"] = pres_score
        return out
