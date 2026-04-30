from typing import List, Union
import pandas as pd

from bist_signal_bot.indicators.engine import IndicatorEngine
from bist_signal_bot.indicators.models import IndicatorRequest, IndicatorBatchResult
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.models import MarketDataFrame

class MomentumFeatureBuilder:
    def __init__(self, indicator_engine: IndicatorEngine | None = None, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.engine = indicator_engine or IndicatorEngine(settings=self.settings)

    def default_momentum_requests(self, level: str = "basic") -> List[IndicatorRequest]:
        level = level.lower()
        if level not in ["basic", "advanced", "full"]:
            raise ValueError(f"Invalid momentum feature level: {level}")

        requests = []

        # Basic features
        if level in ["basic", "full"]:
            requests.extend([
                IndicatorRequest(name="rsi_enhanced", params={"window": self.settings.MOMENTUM_RSI_WINDOW}),
                IndicatorRequest(name="roc_pct", params={"window": self.settings.MOMENTUM_ROC_WINDOW}),
                IndicatorRequest(name="momentum", params={"window": self.settings.MOMENTUM_ROC_WINDOW}),
                IndicatorRequest(name="stoch_enhanced", params={"k_window": self.settings.MOMENTUM_STOCH_K_WINDOW, "d_window": self.settings.MOMENTUM_STOCH_D_WINDOW}),
                IndicatorRequest(name="williams_r", params={"window": self.settings.MOMENTUM_WILLIAMS_WINDOW}),
            ])

        # Advanced features
        if level in ["advanced", "full"]:
            requests.extend([
                IndicatorRequest(name="cci", params={"window": self.settings.MOMENTUM_CCI_WINDOW}),
                IndicatorRequest(name="mfi", params={"window": self.settings.MOMENTUM_MFI_WINDOW}),
                IndicatorRequest(name="tsi", params={
                    "slow": self.settings.MOMENTUM_TSI_SLOW,
                    "fast": self.settings.MOMENTUM_TSI_FAST,
                    "signal": self.settings.MOMENTUM_TSI_SIGNAL
                }),
                IndicatorRequest(name="ppo", params={
                    "fast": self.settings.MOMENTUM_PPO_FAST,
                    "slow": self.settings.MOMENTUM_PPO_SLOW,
                    "signal": self.settings.MOMENTUM_PPO_SIGNAL
                }),
                IndicatorRequest(name="ultimate_osc", params={
                    "short_window": self.settings.MOMENTUM_ULTIMATE_SHORT,
                    "medium_window": self.settings.MOMENTUM_ULTIMATE_MEDIUM,
                    "long_window": self.settings.MOMENTUM_ULTIMATE_LONG
                }),
                IndicatorRequest(name="kst", params={}),
                IndicatorRequest(name="connors_rsi", params={}),
                IndicatorRequest(name="momentum_strength", params={
                    "rsi_window": self.settings.MOMENTUM_RSI_WINDOW,
                    "roc_window": self.settings.MOMENTUM_ROC_WINDOW,
                    "stoch_window": self.settings.MOMENTUM_STOCH_K_WINDOW,
                    "mfi_window": self.settings.MOMENTUM_MFI_WINDOW
                }),
            ])

        return requests

    def build_basic_momentum_features(self, market_data: Union[MarketDataFrame, pd.DataFrame]) -> IndicatorBatchResult:
        requests = self.default_momentum_requests(level="basic")
        return self.engine.calculate_many(market_data, requests)

    def build_advanced_momentum_features(self, market_data: Union[MarketDataFrame, pd.DataFrame]) -> IndicatorBatchResult:
        requests = self.default_momentum_requests(level="advanced")
        return self.engine.calculate_many(market_data, requests)

    def build_full_momentum_features(self, market_data: Union[MarketDataFrame, pd.DataFrame]) -> IndicatorBatchResult:
        requests = self.default_momentum_requests(level="full")
        return self.engine.calculate_many(market_data, requests)
