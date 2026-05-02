from typing import List, Union
import pandas as pd

from bist_signal_bot.indicators.engine import IndicatorEngine
from bist_signal_bot.indicators.models import IndicatorRequest, IndicatorBatchResult
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.models import MarketDataFrame

class VolumeFeatureBuilder:
    def __init__(self, indicator_engine: IndicatorEngine | None = None, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.engine = indicator_engine or IndicatorEngine(settings=self.settings)

    def default_volume_requests(self, level: str = "basic") -> List[IndicatorRequest]:
        level = level.lower()
        if level not in ["basic", "advanced", "full"]:
            raise ValueError(f"Invalid volume feature level: {level}")

        requests = []

        # Basic features
        if level in ["basic", "full"]:
            requests.extend([
                IndicatorRequest(name="volume_sma", params={"window": self.settings.VOLUME_WINDOW}),
                IndicatorRequest(name="volume_ratio", params={"window": self.settings.VOLUME_WINDOW}),
                IndicatorRequest(name="volume_zscore", params={"window": self.settings.VOLUME_WINDOW}),
                IndicatorRequest(name="volume_spike", params={"window": self.settings.VOLUME_WINDOW, "multiplier": self.settings.VOLUME_SPIKE_MULTIPLIER}),
                IndicatorRequest(name="turnover_try", params={"window": self.settings.VOLUME_WINDOW}),
                IndicatorRequest(name="vwma", params={"window": self.settings.VOLUME_WINDOW}),
                IndicatorRequest(name="obv_enhanced", params={"slope_window": 5}),
            ])

        # Advanced features
        if level in ["advanced", "full"]:
            requests.extend([
                IndicatorRequest(name="adl"),
                IndicatorRequest(name="cmf", params={"window": self.settings.VOLUME_CMF_WINDOW}),
                IndicatorRequest(name="chaikin_osc"),
                IndicatorRequest(name="pvt"),
                IndicatorRequest(name="force_index", params={"ema_span": self.settings.VOLUME_FORCE_EMA_SPAN}),
                IndicatorRequest(name="ease_of_movement", params={"window": self.settings.VOLUME_EOM_WINDOW}),
                IndicatorRequest(name="nvi"),
                IndicatorRequest(name="pvi"),
                IndicatorRequest(name="kvo", params={"fast": self.settings.VOLUME_KVO_FAST, "slow": self.settings.VOLUME_KVO_SLOW, "signal": self.settings.VOLUME_KVO_SIGNAL}),
                IndicatorRequest(name="volume_breakout", params={"volume_window": self.settings.VOLUME_WINDOW, "price_window": self.settings.VOLUME_PRICE_WINDOW, "volume_multiplier": self.settings.VOLUME_BREAKOUT_MULTIPLIER}),
                IndicatorRequest(name="liquidity_score", params={"window": self.settings.VOLUME_LIQUIDITY_WINDOW, "min_turnover_try": self.settings.VOLUME_MIN_TURNOVER_TRY}),
                IndicatorRequest(name="volume_composite", params={"volume_window": self.settings.VOLUME_WINDOW, "price_window": self.settings.VOLUME_PRICE_WINDOW}),
            ])

        return requests

    def build_basic_volume_features(self, market_data: Union[MarketDataFrame, pd.DataFrame]) -> IndicatorBatchResult:
        requests = self.default_volume_requests(level="basic")
        return self.engine.calculate_many(market_data, requests)

    def build_advanced_volume_features(self, market_data: Union[MarketDataFrame, pd.DataFrame]) -> IndicatorBatchResult:
        requests = self.default_volume_requests(level="advanced")
        return self.engine.calculate_many(market_data, requests)

    def build_full_volume_features(self, market_data: Union[MarketDataFrame, pd.DataFrame]) -> IndicatorBatchResult:
        requests = self.default_volume_requests(level="full")
        return self.engine.calculate_many(market_data, requests)
