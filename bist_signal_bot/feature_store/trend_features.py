from typing import List, Union
import pandas as pd

from bist_signal_bot.indicators.engine import IndicatorEngine
from bist_signal_bot.indicators.models import IndicatorRequest, IndicatorBatchResult
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.models import MarketDataFrame

class TrendFeatureBuilder:
    def __init__(self, indicator_engine: IndicatorEngine | None = None, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.engine = indicator_engine or IndicatorEngine(settings=self.settings)

    def default_trend_requests(self, level: str = "basic") -> List[IndicatorRequest]:
        level = level.lower()
        if level not in ["basic", "advanced", "full"]:
            raise ValueError(f"Invalid trend feature level: {level}")

        requests = []

        # Basic features
        if level in ["basic", "full"]:
            requests.extend([
                IndicatorRequest(name="sma", params={"window": self.settings.TREND_SHORT_WINDOW}),
                IndicatorRequest(name="sma", params={"window": self.settings.TREND_MEDIUM_WINDOW}),
                IndicatorRequest(name="sma", params={"window": self.settings.TREND_LONG_WINDOW}),
                IndicatorRequest(name="ema", params={"window": self.settings.TREND_SHORT_WINDOW}),
                IndicatorRequest(name="ema", params={"window": self.settings.TREND_MEDIUM_WINDOW}),

                IndicatorRequest(name="ma_distance", params={"ma_type": "sma", "window": self.settings.TREND_SHORT_WINDOW}),
                IndicatorRequest(name="ma_distance", params={"ma_type": "sma", "window": self.settings.TREND_MEDIUM_WINDOW}),
                IndicatorRequest(name="ma_distance", params={"ma_type": "sma", "window": self.settings.TREND_LONG_WINDOW}),

                IndicatorRequest(name="ma_cross_state", params={"ma_type": "sma", "fast": self.settings.TREND_SHORT_WINDOW, "slow": self.settings.TREND_MEDIUM_WINDOW}),

                IndicatorRequest(name="price_above_ma", params={"ma_type": "sma", "window": self.settings.TREND_SHORT_WINDOW}),
                IndicatorRequest(name="price_above_ma", params={"ma_type": "sma", "window": self.settings.TREND_MEDIUM_WINDOW}),
                IndicatorRequest(name="price_above_ma", params={"ma_type": "sma", "window": self.settings.TREND_LONG_WINDOW}),

                IndicatorRequest(name="ma_slope", params={"ma_type": "sma", "window": self.settings.TREND_SHORT_WINDOW}),
                IndicatorRequest(name="ma_slope", params={"ma_type": "sma", "window": self.settings.TREND_MEDIUM_WINDOW}),
            ])

        # Advanced features
        if level in ["advanced", "full"]:
            requests.extend([
                IndicatorRequest(name="adx", params={"window": self.settings.TREND_ADX_WINDOW}),
                IndicatorRequest(name="donchian", params={"window": self.settings.TREND_DONCHIAN_WINDOW}),
                IndicatorRequest(name="keltner", params={
                    "ema_window": self.settings.TREND_KELTNER_EMA_WINDOW,
                    "atr_window": self.settings.TREND_ATR_WINDOW,
                    "atr_multiplier": self.settings.TREND_KELTNER_ATR_MULTIPLIER
                }),
                IndicatorRequest(name="aroon", params={"window": self.settings.TREND_AROON_WINDOW}),
                IndicatorRequest(name="supertrend", params={
                    "atr_window": self.settings.TREND_SUPERTREND_ATR_WINDOW,
                    "multiplier": self.settings.TREND_SUPERTREND_MULTIPLIER
                }),
                IndicatorRequest(name="linreg_slope", params={"window": self.settings.TREND_LINREG_WINDOW}),
                IndicatorRequest(name="trend_strength", params={
                    "short_window": self.settings.TREND_SHORT_WINDOW,
                    "medium_window": self.settings.TREND_MEDIUM_WINDOW,
                    "long_window": self.settings.TREND_LONG_WINDOW,
                    "adx_window": self.settings.TREND_ADX_WINDOW
                }),
            ])

        return requests

    def build_basic_trend_features(self, market_data: Union[MarketDataFrame, pd.DataFrame]) -> IndicatorBatchResult:
        requests = self.default_trend_requests(level="basic")
        return self.engine.calculate_many(market_data, requests)

    def build_advanced_trend_features(self, market_data: Union[MarketDataFrame, pd.DataFrame]) -> IndicatorBatchResult:
        requests = self.default_trend_requests(level="advanced")
        return self.engine.calculate_many(market_data, requests)

    def build_full_trend_features(self, market_data: Union[MarketDataFrame, pd.DataFrame]) -> IndicatorBatchResult:
        requests = self.default_trend_requests(level="full")
        return self.engine.calculate_many(market_data, requests)

    def add_features(self, market_data, level: str = "basic"):
        return market_data.copy()
