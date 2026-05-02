import pandas as pd
from typing import Union, List

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.models import MarketDataFrame
from bist_signal_bot.divergence.engine import DivergenceEngine
from bist_signal_bot.divergence.models import DivergenceFeatureResult

class DivergenceFeatureBuilder:
    def __init__(self, divergence_engine: DivergenceEngine | None = None, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.engine = divergence_engine or DivergenceEngine(settings=self.settings)

    def default_divergence_indicators(self, level: str = "basic") -> List[str]:
        if level == "basic":
            return ["rsi", "macd_hist", "obv"]
        elif level == "advanced":
            return ["mfi", "stoch_k", "ppo_hist", "cmf", "momentum"]
        elif level == "full":
            return ["rsi", "macd_hist", "obv", "mfi", "stoch_k", "ppo_hist", "cmf", "momentum"]
        else:
            raise ValueError(f"Invalid divergence feature level: {level}")

    def build_basic_divergence_features(self, market_data: Union[MarketDataFrame, pd.DataFrame]) -> DivergenceFeatureResult:
        indicators = self.default_divergence_indicators("basic")
        request = self.engine.parse_request(indicators=indicators)
        return self.engine.detect(market_data, request)

    def build_advanced_divergence_features(self, market_data: Union[MarketDataFrame, pd.DataFrame]) -> DivergenceFeatureResult:
        indicators = self.default_divergence_indicators("advanced")
        request = self.engine.parse_request(indicators=indicators)
        return self.engine.detect(market_data, request)

    def build_full_divergence_features(self, market_data: Union[MarketDataFrame, pd.DataFrame]) -> DivergenceFeatureResult:
        indicators = self.default_divergence_indicators("full")
        request = self.engine.parse_request(indicators=indicators)
        return self.engine.detect(market_data, request)
