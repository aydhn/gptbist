from typing import Any, Dict, List
import numpy as np
import pandas as pd

from bist_signal_bot.indicators.base import BaseIndicator
from bist_signal_bot.indicators.models import IndicatorSpec, IndicatorCategory, IndicatorBackend
from bist_signal_bot.core.exceptions import IndicatorValidationError

class ATRPercentIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="atr_pct",
                display_name="ATR Percent",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"window": 14},
                output_columns=["atr_pct"],
                min_rows=15
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        w = params['window']
        return [f"atr_pct_{w}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        out = pd.DataFrame(index=data.index)

        high_low = data['high'] - data['low']
        high_close = (data['high'] - data['close'].shift()).abs()
        low_close = (data['low'] - data['close'].shift()).abs()

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=window).mean()

        out[f"atr_pct_{window}"] = atr / data['close']
        return out


class NormalizedTrueRangeIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="normalized_true_range",
                display_name="Normalized True Range",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"window": 14},
                output_columns=["ntr", "ntr_ma"],
                min_rows=15
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        w = params['window']
        return [f"ntr_{w}", f"ntr_ma_{w}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        out = pd.DataFrame(index=data.index)

        high_low = data['high'] - data['low']
        high_close = (data['high'] - data['close'].shift()).abs()
        low_close = (data['low'] - data['close'].shift()).abs()

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        ntr = tr / data['close']
        out[f"ntr_{window}"] = ntr
        out[f"ntr_ma_{window}"] = ntr.rolling(window=window).mean()
        return out


class HistoricalVolatilityIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="historical_volatility",
                display_name="Historical Volatility",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"window": 20, "annualization": 252},
                output_columns=["hist_vol"],
                min_rows=21
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")
        if params.get("annualization", 0) <= 0:
            raise IndicatorValidationError("Annualization must be positive.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"hist_vol_{params['window']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        ann = params["annualization"]
        out = pd.DataFrame(index=data.index)

        # log returns safely
        # to avoid log(neg) -> NaN safely, log of close/close.shift
        prev_close = data['close'].shift(1)
        # Handle zero or negative price safely by returning NaN for those returns
        valid_prices = (data['close'] > 0) & (prev_close > 0)
        returns = pd.Series(np.nan, index=data.index)
        returns.loc[valid_prices] = np.log(data['close'].loc[valid_prices] / prev_close.loc[valid_prices])

        out[f"hist_vol_{window}"] = returns.rolling(window=window).std(ddof=1) * np.sqrt(ann)
        return out


class RealizedVolatilityIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="realized_volatility",
                display_name="Realized Volatility",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"window": 20, "annualization": 252},
                output_columns=["realized_vol"],
                min_rows=21
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")
        if params.get("annualization", 0) <= 0:
            raise IndicatorValidationError("Annualization must be positive.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"realized_vol_{params['window']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        ann = params["annualization"]
        out = pd.DataFrame(index=data.index)

        prev_close = data['close'].shift(1)
        valid_prices = (data['close'] > 0) & (prev_close > 0)
        returns = pd.Series(np.nan, index=data.index)
        returns.loc[valid_prices] = np.log(data['close'].loc[valid_prices] / prev_close.loc[valid_prices])

        squared_returns = returns ** 2
        sum_sq = squared_returns.rolling(window=window).sum()

        out[f"realized_vol_{window}"] = np.sqrt(sum_sq) * np.sqrt(ann / window)
        return out


class ParkinsonVolatilityIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="parkinson_volatility",
                display_name="Parkinson Volatility",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low"],
                default_params={"window": 20, "annualization": 252},
                output_columns=["parkinson_vol"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")
        if params.get("annualization", 0) <= 0:
            raise IndicatorValidationError("Annualization must be positive.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"parkinson_vol_{params['window']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        ann = params["annualization"]
        out = pd.DataFrame(index=data.index)

        valid_prices = (data['high'] > 0) & (data['low'] > 0)
        term = pd.Series(np.nan, index=data.index)
        term.loc[valid_prices] = np.log(data['high'].loc[valid_prices] / data['low'].loc[valid_prices]) ** 2

        roll_mean = term.rolling(window=window).mean()

        var = (1.0 / (4.0 * np.log(2.0))) * roll_mean * ann
        out[f"parkinson_vol_{window}"] = np.sqrt(var.clip(lower=0))
        return out


class GarmanKlassVolatilityIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="garman_klass_volatility",
                display_name="Garman-Klass Volatility",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["open", "high", "low", "close"],
                default_params={"window": 20, "annualization": 252},
                output_columns=["garman_klass_vol"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")
        if params.get("annualization", 0) <= 0:
            raise IndicatorValidationError("Annualization must be positive.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"garman_klass_vol_{params['window']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        ann = params["annualization"]
        out = pd.DataFrame(index=data.index)

        valid_prices = (data['open'] > 0) & (data['high'] > 0) & (data['low'] > 0) & (data['close'] > 0)

        log_hl2 = pd.Series(np.nan, index=data.index)
        log_co2 = pd.Series(np.nan, index=data.index)

        log_hl2.loc[valid_prices] = np.log(data['high'].loc[valid_prices] / data['low'].loc[valid_prices]) ** 2
        log_co2.loc[valid_prices] = np.log(data['close'].loc[valid_prices] / data['open'].loc[valid_prices]) ** 2

        gk_daily = 0.5 * log_hl2 - (2 * np.log(2) - 1) * log_co2
        gk_var = gk_daily.rolling(window=window).mean() * ann

        out[f"garman_klass_vol_{window}"] = np.sqrt(gk_var.clip(lower=0))
        return out


class RogersSatchellVolatilityIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="rogers_satchell_volatility",
                display_name="Rogers-Satchell Volatility",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["open", "high", "low", "close"],
                default_params={"window": 20, "annualization": 252},
                output_columns=["rogers_satchell_vol"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")
        if params.get("annualization", 0) <= 0:
            raise IndicatorValidationError("Annualization must be positive.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return [f"rogers_satchell_vol_{params['window']}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        ann = params["annualization"]
        out = pd.DataFrame(index=data.index)

        valid_prices = (data['open'] > 0) & (data['high'] > 0) & (data['low'] > 0) & (data['close'] > 0)

        term1 = pd.Series(np.nan, index=data.index)
        term2 = pd.Series(np.nan, index=data.index)

        v = valid_prices
        term1.loc[v] = np.log(data['high'].loc[v]/data['close'].loc[v]) * np.log(data['high'].loc[v]/data['open'].loc[v])
        term2.loc[v] = np.log(data['low'].loc[v]/data['close'].loc[v]) * np.log(data['low'].loc[v]/data['open'].loc[v])

        rs_daily = term1 + term2
        rs_var = rs_daily.rolling(window=window).mean() * ann

        out[f"rogers_satchell_vol_{window}"] = np.sqrt(rs_var.clip(lower=0))
        return out


class RangePercentIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="range_percent",
                display_name="Range Percent",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"window": 20},
                output_columns=["range_pct", "range_pct_ma", "range_pct_zscore"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        w = params['window']
        return ["range_pct", f"range_pct_ma_{w}", f"range_pct_zscore_{w}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        out = pd.DataFrame(index=data.index)

        range_pct = (data['high'] - data['low']) / data['close']
        out["range_pct"] = range_pct

        ma = range_pct.rolling(window=window).mean()
        std = range_pct.rolling(window=window).std(ddof=1)

        out[f"range_pct_ma_{window}"] = ma
        out[f"range_pct_zscore_{window}"] = (range_pct - ma) / std
        return out


class GapPercentIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="gap_percent",
                display_name="Gap Percent",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["open", "close"],
                default_params={"window": 20},
                output_columns=["gap_pct", "abs_gap_pct", "gap_pct_ma", "gap_pct_zscore"],
                min_rows=20
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0:
            raise IndicatorValidationError("Window must be a positive integer.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        w = params['window']
        return ["gap_pct", "abs_gap_pct", f"gap_pct_ma_{w}", f"gap_pct_zscore_{w}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        out = pd.DataFrame(index=data.index)

        prev_close = data['close'].shift(1)
        gap_pct = (data['open'] / prev_close) - 1

        out["gap_pct"] = gap_pct
        out["abs_gap_pct"] = gap_pct.abs()

        ma = out["abs_gap_pct"].rolling(window=window).mean()
        std = out["abs_gap_pct"].rolling(window=window).std(ddof=1)

        out[f"gap_pct_ma_{window}"] = ma
        out[f"gap_pct_zscore_{window}"] = (out["abs_gap_pct"] - ma) / std
        return out


class BollingerBandwidthPercentileIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="bb_width_percentile",
                display_name="Bollinger Bandwidth Percentile",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"window": 20, "std": 2.0, "rank_window": 100},
                output_columns=["bb_width_percentile"],
                min_rows=100
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("window", 0) <= 0 or params.get("rank_window", 0) <= 0:
            raise IndicatorValidationError("Window parameters must be positive integers.")
        if params.get("std", 0) <= 0:
            raise IndicatorValidationError("Std must be positive.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        w = params['window']
        rw = params['rank_window']
        return [f"bb_width_percentile_{w}_{rw}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        window = params["window"]
        std_multiplier = params["std"]
        rank_window = params["rank_window"]

        out = pd.DataFrame(index=data.index)
        rolling_close = data['close'].rolling(window=window)

        mid = rolling_close.mean()
        std_dev = rolling_close.std(ddof=0)
        upper = mid + (std_dev * std_multiplier)
        lower = mid - (std_dev * std_multiplier)
        bb_width = (upper - lower) / mid

        def pct_rank(x):
            if np.isnan(x[-1]):
                return np.nan
            valid = x[~np.isnan(x)]
            if len(valid) == 0:
                return np.nan
            return (valid <= x[-1]).mean() * 100.0

        out[f"bb_width_percentile_{window}_{rank_window}"] = bb_width.rolling(window=rank_window).apply(pct_rank, raw=True)
        return out


class ATRPercentileIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="atr_percentile",
                display_name="ATR Percentile",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"atr_window": 14, "rank_window": 100},
                output_columns=["atr_pct_percentile"],
                min_rows=100
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("atr_window", 0) <= 0 or params.get("rank_window", 0) <= 0:
            raise IndicatorValidationError("Window parameters must be positive integers.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        aw = params['atr_window']
        rw = params['rank_window']
        return [f"atr_pct_percentile_{aw}_{rw}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        atr_window = params["atr_window"]
        rank_window = params["rank_window"]
        out = pd.DataFrame(index=data.index)

        high_low = data['high'] - data['low']
        high_close = (data['high'] - data['close'].shift()).abs()
        low_close = (data['low'] - data['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)

        atr = tr.rolling(window=atr_window).mean()
        atr_pct = atr / data['close']

        def pct_rank(x):
            if np.isnan(x[-1]):
                return np.nan
            valid = x[~np.isnan(x)]
            if len(valid) == 0:
                return np.nan
            return (valid <= x[-1]).mean() * 100.0

        out[f"atr_pct_percentile_{atr_window}_{rank_window}"] = atr_pct.rolling(window=rank_window).apply(pct_rank, raw=True)
        return out


class VolatilityZScoreIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="volatility_zscore",
                display_name="Volatility Z-Score",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"vol_window": 20, "z_window": 100},
                output_columns=["vol_zscore"],
                min_rows=100
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("vol_window", 0) <= 0 or params.get("z_window", 0) <= 0:
            raise IndicatorValidationError("Window parameters must be positive integers.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        vw = params['vol_window']
        zw = params['z_window']
        return [f"vol_zscore_{vw}_{zw}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        vol_window = params["vol_window"]
        z_window = params["z_window"]
        out = pd.DataFrame(index=data.index)

        prev_close = data['close'].shift(1)
        valid_prices = (data['close'] > 0) & (prev_close > 0)
        returns = pd.Series(np.nan, index=data.index)
        returns.loc[valid_prices] = np.log(data['close'].loc[valid_prices] / prev_close.loc[valid_prices])

        hist_vol = returns.rolling(window=vol_window).std(ddof=1) * np.sqrt(252)

        ma = hist_vol.rolling(window=z_window).mean()
        std = hist_vol.rolling(window=z_window).std(ddof=1)

        out[f"vol_zscore_{vol_window}_{z_window}"] = (hist_vol - ma) / std
        return out


class VolatilityCompressionScoreIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="volatility_compression",
                display_name="Volatility Compression Score",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"bb_window": 20, "atr_window": 14, "rank_window": 100},
                output_columns=["vol_compression_score"],
                min_rows=100
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("bb_window", 0) <= 0 or params.get("atr_window", 0) <= 0 or params.get("rank_window", 0) <= 0:
            raise IndicatorValidationError("Window parameters must be positive integers.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return ["vol_compression_score"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        bb_window = params["bb_window"]
        atr_window = params["atr_window"]
        rank_window = params["rank_window"]

        out = pd.DataFrame(index=data.index)

        # BB width percentile
        rolling_close = data['close'].rolling(window=bb_window)
        mid = rolling_close.mean()
        std_dev = rolling_close.std(ddof=0)
        upper = mid + (std_dev * 2.0)
        lower = mid - (std_dev * 2.0)
        bb_width = (upper - lower) / mid

        # ATR pct percentile
        high_low = data['high'] - data['low']
        high_close = (data['high'] - data['close'].shift()).abs()
        low_close = (data['low'] - data['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=atr_window).mean()
        atr_pct = atr / data['close']

        def pct_rank(x):
            if np.isnan(x[-1]):
                return np.nan
            valid = x[~np.isnan(x)]
            if len(valid) == 0:
                return np.nan
            return (valid <= x[-1]).mean() * 100.0

        bb_rank = bb_width.rolling(window=rank_window).apply(pct_rank, raw=True)
        atr_rank = atr_pct.rolling(window=rank_window).apply(pct_rank, raw=True)

        # Score is inversely related to volatility percentiles: 100 means very compressed
        score = 100.0 - ((bb_rank + atr_rank) / 2.0)
        out["vol_compression_score"] = score.clip(0, 100)
        return out


class VolatilityExpansionScoreIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="volatility_expansion",
                display_name="Volatility Expansion Score",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["high", "low", "close"],
                default_params={"bb_window": 20, "atr_window": 14, "rank_window": 100},
                output_columns=["vol_expansion_score"],
                min_rows=100
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("bb_window", 0) <= 0 or params.get("atr_window", 0) <= 0 or params.get("rank_window", 0) <= 0:
            raise IndicatorValidationError("Window parameters must be positive integers.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return ["vol_expansion_score"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        bb_window = params["bb_window"]
        atr_window = params["atr_window"]
        rank_window = params["rank_window"]

        out = pd.DataFrame(index=data.index)

        rolling_close = data['close'].rolling(window=bb_window)
        mid = rolling_close.mean()
        std_dev = rolling_close.std(ddof=0)
        upper = mid + (std_dev * 2.0)
        lower = mid - (std_dev * 2.0)
        bb_width = (upper - lower) / mid

        high_low = data['high'] - data['low']
        high_close = (data['high'] - data['close'].shift()).abs()
        low_close = (data['low'] - data['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=atr_window).mean()
        atr_pct = atr / data['close']

        range_pct = (data['high'] - data['low']) / data['close']
        range_ma = range_pct.rolling(window=20).mean()
        range_std = range_pct.rolling(window=20).std(ddof=1)
        range_zscore = (range_pct - range_ma) / range_std

        def pct_rank(x):
            if np.isnan(x[-1]):
                return np.nan
            valid = x[~np.isnan(x)]
            if len(valid) == 0:
                return np.nan
            return (valid <= x[-1]).mean() * 100.0

        bb_rank = bb_width.rolling(window=rank_window).apply(pct_rank, raw=True)
        atr_rank = atr_pct.rolling(window=rank_window).apply(pct_rank, raw=True)

        # Z-score roughly maps 0..3+ to 0..100
        z_score_mapped = (range_zscore.clip(0, 3) / 3.0) * 100.0

        score = (bb_rank + atr_rank + z_score_mapped) / 3.0
        out["vol_expansion_score"] = score.clip(0, 100)
        return out


class VolatilityRegimeFeatureIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="volatility_regime",
                display_name="Volatility Regime Feature",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["close"],
                default_params={"vol_window": 20, "rank_window": 252},
                output_columns=["vol_regime_percentile", "vol_regime_state"],
                min_rows=252
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("vol_window", 0) <= 0 or params.get("rank_window", 0) <= 0:
            raise IndicatorValidationError("Window parameters must be positive integers.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        vw = params['vol_window']
        rw = params['rank_window']
        return [f"vol_regime_percentile_{vw}_{rw}", f"vol_regime_state_{vw}_{rw}"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        vol_window = params["vol_window"]
        rank_window = params["rank_window"]
        out = pd.DataFrame(index=data.index)

        prev_close = data['close'].shift(1)
        valid_prices = (data['close'] > 0) & (prev_close > 0)
        returns = pd.Series(np.nan, index=data.index)
        returns.loc[valid_prices] = np.log(data['close'].loc[valid_prices] / prev_close.loc[valid_prices])

        hist_vol = returns.rolling(window=vol_window).std(ddof=1) * np.sqrt(252)

        def pct_rank(x):
            if np.isnan(x[-1]):
                return np.nan
            valid = x[~np.isnan(x)]
            if len(valid) == 0:
                return np.nan
            return (valid <= x[-1]).mean() * 100.0

        percentile = hist_vol.rolling(window=rank_window).apply(pct_rank, raw=True)
        out[f"vol_regime_percentile_{vol_window}_{rank_window}"] = percentile

        state = pd.Series(np.nan, index=data.index)
        state.loc[percentile < 33.33] = 0
        state.loc[(percentile >= 33.33) & (percentile < 66.66)] = 1
        state.loc[percentile >= 66.66] = 2

        out[f"vol_regime_state_{vol_window}_{rank_window}"] = state
        return out


class VolatilityCompositeScoreIndicator(BaseIndicator):
    def __init__(self):
        super().__init__(
            spec=IndicatorSpec(
                name="volatility_composite",
                display_name="Volatility Composite Score",
                category=IndicatorCategory.VOLATILITY,
                backend=IndicatorBackend.NATIVE,
                required_columns=["open", "high", "low", "close"],
                default_params={"vol_window": 20, "atr_window": 14, "rank_window": 100},
                output_columns=["volatility_risk_score", "volatility_regime_score"],
                min_rows=100
            )
        )

    def validate_input(self, data: pd.DataFrame, params: Dict[str, Any]) -> None:
        super().validate_input(data, params)
        if params.get("vol_window", 0) <= 0 or params.get("atr_window", 0) <= 0 or params.get("rank_window", 0) <= 0:
            raise IndicatorValidationError("Window parameters must be positive integers.")

    def get_output_columns(self, params: Dict[str, Any]) -> List[str]:
        return ["volatility_risk_score", "volatility_regime_score"]

    def calculate(self, data: pd.DataFrame, **params: Any) -> pd.DataFrame:
        vol_window = params["vol_window"]
        atr_window = params["atr_window"]
        rank_window = params["rank_window"]
        out = pd.DataFrame(index=data.index)

        # ATR Pct Percentile
        high_low = data['high'] - data['low']
        high_close = (data['high'] - data['close'].shift()).abs()
        low_close = (data['low'] - data['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=atr_window).mean()
        atr_pct = atr / data['close']

        # BB Width Percentile
        rolling_close = data['close'].rolling(window=vol_window)
        mid = rolling_close.mean()
        std_dev = rolling_close.std(ddof=0)
        upper = mid + (std_dev * 2.0)
        lower = mid - (std_dev * 2.0)
        bb_width = (upper - lower) / mid

        # Historical Vol Percentile
        prev_close = data['close'].shift(1)
        valid_prices = (data['close'] > 0) & (prev_close > 0)
        returns = pd.Series(np.nan, index=data.index)
        returns.loc[valid_prices] = np.log(data['close'].loc[valid_prices] / prev_close.loc[valid_prices])
        hist_vol = returns.rolling(window=vol_window).std(ddof=1) * np.sqrt(252)

        def pct_rank(x):
            if np.isnan(x[-1]):
                return np.nan
            valid = x[~np.isnan(x)]
            if len(valid) == 0:
                return np.nan
            return (valid <= x[-1]).mean() * 100.0

        atr_rank = atr_pct.rolling(window=rank_window).apply(pct_rank, raw=True)
        bb_rank = bb_width.rolling(window=rank_window).apply(pct_rank, raw=True)
        hv_rank = hist_vol.rolling(window=rank_window).apply(pct_rank, raw=True)

        # Range and Gap Z-scores
        range_pct = (data['high'] - data['low']) / data['close']
        range_ma = range_pct.rolling(window=vol_window).mean()
        range_std = range_pct.rolling(window=vol_window).std(ddof=1)
        range_zscore = (range_pct - range_ma) / range_std
        range_z_mapped = (range_zscore.clip(0, 3) / 3.0) * 100.0

        gap_pct = (data['open'] / prev_close) - 1
        abs_gap_pct = gap_pct.abs()
        gap_ma = abs_gap_pct.rolling(window=vol_window).mean()
        gap_std = abs_gap_pct.rolling(window=vol_window).std(ddof=1)
        gap_zscore = (abs_gap_pct - gap_ma) / gap_std
        gap_z_mapped = (gap_zscore.clip(0, 3) / 3.0) * 100.0

        risk_score = (range_z_mapped + gap_z_mapped + atr_rank) / 3.0
        regime_score = (hv_rank + bb_rank + atr_rank) / 3.0

        out["volatility_risk_score"] = risk_score.clip(0, 100)
        out["volatility_regime_score"] = regime_score.clip(0, 100)
        return out
