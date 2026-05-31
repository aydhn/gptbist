from typing import Optional, Union, Dict, Any
import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.models import MarketDataFrame, Timeframe, DataVendor
from bist_signal_bot.timeframes.engine import MultiTimeframeEngine
from bist_signal_bot.timeframes.models import MultiTimeframeResult
from bist_signal_bot.indicators.models import IndicatorRequest
from datetime import datetime

class MultiTimeframeFeatureBuilder:
    def __init__(self, mtf_engine: Optional[MultiTimeframeEngine] = None, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.mtf_engine = mtf_engine or MultiTimeframeEngine(settings=self.settings)

    def _ensure_market_data(self, data: Union[MarketDataFrame, pd.DataFrame], symbol: str) -> MarketDataFrame:
        if isinstance(data, MarketDataFrame):
            return data

        return MarketDataFrame(
            symbol=symbol,
            timeframe=Timeframe(self.settings.MTF_BASE_TIMEFRAME),
            source=DataVendor.UNKNOWN,
            data=data,
            fetched_at=datetime.utcnow()
        )

    def default_mtf_level_config(self, level: str = "basic") -> Dict[str, Any]:
        if level == "basic":
            return {
                Timeframe.WEEKLY: [
                    IndicatorRequest(name="sma", params={"window": 20}),
                    IndicatorRequest(name="sma", params={"window": 50}),
                    IndicatorRequest(name="rsi", params={"window": 14})
                ]
            }
        elif level == "advanced":
            return {
                Timeframe.WEEKLY: [
                    IndicatorRequest(name="sma", params={"window": 20}),
                    IndicatorRequest(name="sma", params={"window": 50}),
                    IndicatorRequest(name="rsi", params={"window": 14}),
                    IndicatorRequest(name="atr_pct", params={"window": 14}),
                    IndicatorRequest(name="macd", params={})
                ],
                Timeframe.MONTHLY: [
                    IndicatorRequest(name="sma", params={"window": 10}),
                    IndicatorRequest(name="rsi", params={"window": 14}),
                    IndicatorRequest(name="historical_volatility", params={"window": 12})
                ]
            }
        elif level == "full":
            return {
                Timeframe.WEEKLY: [
                    IndicatorRequest(name="sma", params={"window": 20}),
                    IndicatorRequest(name="sma", params={"window": 50}),
                    IndicatorRequest(name="ema", params={"span": 20}),
                    IndicatorRequest(name="rsi", params={"window": 14}),
                    IndicatorRequest(name="atr_pct", params={"window": 14}),
                    IndicatorRequest(name="macd", params={}),
                    IndicatorRequest(name="bb_20", params={})
                ],
                Timeframe.MONTHLY: [
                    IndicatorRequest(name="sma", params={"window": 10}),
                    IndicatorRequest(name="sma", params={"window": 20}),
                    IndicatorRequest(name="rsi", params={"window": 14}),
                    IndicatorRequest(name="historical_volatility", params={"window": 12}),
                    IndicatorRequest(name="macd", params={})
                ]
            }
        else:
            raise ValueError(f"Unknown MTF feature level: {level}")

    def build_basic_mtf_features(self, market_data: Union[MarketDataFrame, pd.DataFrame], symbol: str = "UNKNOWN") -> MultiTimeframeResult:
        mdf = self._ensure_market_data(market_data, symbol)
        requests = self.default_mtf_level_config("basic")
        return self.mtf_engine.build_from_base_data(mdf, higher_timeframes=list(requests.keys()), indicator_requests_by_timeframe=requests)

    def build_advanced_mtf_features(self, market_data: Union[MarketDataFrame, pd.DataFrame], symbol: str = "UNKNOWN") -> MultiTimeframeResult:
        mdf = self._ensure_market_data(market_data, symbol)
        requests = self.default_mtf_level_config("advanced")
        return self.mtf_engine.build_from_base_data(mdf, higher_timeframes=list(requests.keys()), indicator_requests_by_timeframe=requests)

    def build_full_mtf_features(self, market_data: Union[MarketDataFrame, pd.DataFrame], symbol: str = "UNKNOWN") -> MultiTimeframeResult:
        mdf = self._ensure_market_data(market_data, symbol)
        requests = self.default_mtf_level_config("full")
        return self.mtf_engine.build_from_base_data(mdf, higher_timeframes=list(requests.keys()), indicator_requests_by_timeframe=requests)

    def add_features(self, market_data, symbol: str, base_timeframe: str):
        return market_data.copy()
