import logging
import time
import pandas as pd
from typing import Union, List

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.models import MarketDataFrame
from bist_signal_bot.indicators.engine import IndicatorEngine
from bist_signal_bot.divergence.models import (
    DivergenceRequest, DivergenceResult, DivergenceFeatureResult,
    DivergenceStatus, DivergenceIssue, PivotMode
)
from bist_signal_bot.divergence.pivots import PivotDetector
from bist_signal_bot.divergence.detectors import DivergenceDetector

class DivergenceEngine:
    def __init__(self, indicator_engine: IndicatorEngine | None = None, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.settings = settings or Settings()
        self.indicator_engine = indicator_engine or IndicatorEngine(settings=self.settings)
        self.logger = logger or logging.getLogger("bist_signal_bot.divergence")

    def parse_request(self, raw: str | None = None, indicators: List[str] | None = None, **kwargs) -> DivergenceRequest:
        if raw is not None and indicators is None:
            indicators = [i.strip() for i in raw.split(",") if i.strip()]

        if not indicators:
            indicators = [i.strip() for i in self.settings.DIVERGENCE_DEFAULT_INDICATORS.split(",") if i.strip()]

        pivot_mode = kwargs.get("pivot_mode", PivotMode(self.settings.DIVERGENCE_PIVOT_MODE))

        return DivergenceRequest(
            indicators=indicators,
            pivot_mode=pivot_mode,
            lookback=kwargs.get("lookback", self.settings.DIVERGENCE_LOOKBACK),
            confirmation_bars=kwargs.get("confirmation_bars", self.settings.DIVERGENCE_CONFIRMATION_BARS),
            max_pivot_distance=kwargs.get("max_pivot_distance", self.settings.DIVERGENCE_MAX_PIVOT_DISTANCE),
            min_pivot_distance=kwargs.get("min_pivot_distance", self.settings.DIVERGENCE_MIN_PIVOT_DISTANCE),
            min_strength_score=kwargs.get("min_strength_score", self.settings.DIVERGENCE_MIN_STRENGTH_SCORE),
            include_hidden=kwargs.get("include_hidden", self.settings.DIVERGENCE_INCLUDE_HIDDEN),
            include_regular=kwargs.get("include_regular", self.settings.DIVERGENCE_INCLUDE_REGULAR)
        )

    def ensure_indicator_columns(self, data: pd.DataFrame, indicators: List[str]) -> pd.DataFrame:
        df = data.copy()
        missing = [ind for ind in indicators if ind not in df.columns]

        if not missing:
            return df

        shorthand_map = {
            "rsi": "rsi_14",
            "macd_hist": "macd_12_26_9",  # the engine outputs macd_hist_12_26_9 but the request name is macd_12_26_9 or just macd
            "obv": "obv",
            "mfi": "mfi_14",
            "stoch_k": "stoch_14_3", # outputs stoch_k_14_3
            "ppo_hist": "ppo_12_26_9",
            "cmf": "cmf_20",
            "momentum": "roc_10"
        }

        requests = []
        for ind in missing:
            mapped = shorthand_map.get(ind, ind)
            # Basic parsing to request indicator
            from bist_signal_bot.indicators.engine import IndicatorRequest
            if "_" in mapped and not mapped in shorthand_map.values(): # simple heuristic
                 parts = mapped.split("_")
                 name = parts[0]
                 params = {}
                 if len(parts) > 1 and parts[1].isdigit():
                     if name in ["rsi", "mfi", "cmf", "roc"]: params["window"] = int(parts[1])
                 requests.append(IndicatorRequest(name=name, params=params))
            else:
                 # Default cases
                 if mapped == "macd_12_26_9": requests.append(IndicatorRequest(name="macd"))
                 elif mapped == "rsi_14": requests.append(IndicatorRequest(name="rsi", params={"window": 14}))
                 elif mapped == "mfi_14": requests.append(IndicatorRequest(name="mfi", params={"window": 14}))
                 elif mapped == "obv": requests.append(IndicatorRequest(name="obv"))
                 elif mapped == "stoch_14_3": requests.append(IndicatorRequest(name="stoch", params={"k_window": 14, "d_window": 3}))
                 elif mapped == "ppo_12_26_9": requests.append(IndicatorRequest(name="ppo"))
                 elif mapped == "cmf_20": requests.append(IndicatorRequest(name="cmf", params={"window": 20}))
                 elif mapped == "roc_10": requests.append(IndicatorRequest(name="roc", params={"window": 10}))
                 else:
                     requests.append(IndicatorRequest(name=mapped))

        if requests:
            try:
                batch_res = self.indicator_engine.calculate_many(df, requests, continue_on_error=True)
                df = batch_res.output_data
            except Exception as e:
                self.logger.warning(f"Failed to calculate missing indicators: {e}")

        # Handle aliasing (e.g. we want 'rsi' but calculated 'rsi_14')
        for ind in missing:
            if ind not in df.columns:
                # Try to find the closest match
                if ind == "macd_hist" and "macd_hist_12_26_9" in df.columns:
                    df[ind] = df["macd_hist_12_26_9"]
                elif ind == "stoch_k" and "stoch_k_14_3" in df.columns:
                    df[ind] = df["stoch_k_14_3"]
                elif ind == "ppo_hist" and "ppo_hist_12_26_9" in df.columns:
                    df[ind] = df["ppo_hist_12_26_9"]
                elif ind == "momentum" and "roc_10" in df.columns:
                    df[ind] = df["roc_10"]
                elif ind == "rsi" and "rsi_14" in df.columns:
                    df[ind] = df["rsi_14"]
                elif ind == "mfi" and "mfi_14" in df.columns:
                    df[ind] = df["mfi_14"]
                elif ind == "cmf" and "cmf_20" in df.columns:
                    df[ind] = df["cmf_20"]

        return df

    def detect(self, data: Union[MarketDataFrame, pd.DataFrame], request: DivergenceRequest, symbol: str | None = None, timeframe: str | None = None) -> DivergenceFeatureResult:
        start_time = time.time()

        if isinstance(data, MarketDataFrame):
            df = data.data.copy()
            symbol = symbol or data.symbol
            timeframe = timeframe or data.timeframe
        else:
            df = data.copy()
            symbol = symbol or "UNKNOWN"
            timeframe = timeframe or "UNKNOWN"

        df = self.ensure_indicator_columns(df, request.indicators)

        pivot_detector = PivotDetector(
            mode=request.pivot_mode,
            lookback=request.lookback,
            confirmation_bars=request.confirmation_bars
        )
        detector = DivergenceDetector(pivot_detector, self.settings)

        all_events = []
        all_issues = []
        output_columns = []

        for ind in request.indicators:
            if ind not in df.columns:
                all_issues.append(DivergenceIssue(
                    indicator=ind,
                    message=f"Indicator column '{ind}' could not be resolved or calculated.",
                    severity="ERROR"
                ))
                continue

            df, events, issues = detector.detect_for_indicator(df, "close", ind, request, symbol, timeframe)
            all_events.extend(events)
            all_issues.extend(issues)
            output_columns.extend(detector.build_feature_columns(ind))

        status = DivergenceStatus.SUCCESS
        if all_issues:
            if any(i.severity == "ERROR" for i in all_issues):
                status = DivergenceStatus.FAILED if len(all_events) == 0 else DivergenceStatus.WARNING
            else:
                status = DivergenceStatus.WARNING

        elapsed = time.time() - start_time

        result = DivergenceResult(
            symbol=symbol,
            timeframe=timeframe,
            status=status,
            pivot_mode=request.pivot_mode,
            requested_indicators=request.indicators,
            events=all_events,
            output_columns=output_columns,
            row_count=len(df),
            detected_count=len(all_events),
            issues=all_issues,
            elapsed_seconds=elapsed
        )

        return DivergenceFeatureResult(result=result, output_data=df)

    def detect_default_set(self, data: Union[MarketDataFrame, pd.DataFrame]) -> DivergenceFeatureResult:
        req = self.parse_request(raw=self.settings.DIVERGENCE_DEFAULT_INDICATORS)
        return self.detect(data, req)
