from typing import List, Union
import pandas as pd

from bist_signal_bot.indicators.engine import IndicatorEngine
from bist_signal_bot.indicators.models import IndicatorRequest, IndicatorBatchResult
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.models import MarketDataFrame

class VolatilityFeatureBuilder:
    def __init__(self, indicator_engine: IndicatorEngine | None = None, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.engine = indicator_engine or IndicatorEngine(settings=self.settings)

    def default_volatility_requests(self, level: str = "basic") -> List[IndicatorRequest]:
        level = level.lower()
        if level not in ["basic", "advanced", "full"]:
            raise ValueError(f"Invalid volatility feature level: {level}")

        requests = []

        # Basic features
        if level in ["basic", "full"]:
            requests.extend([
                IndicatorRequest(name="atr_pct", params={"window": self.settings.VOL_ATR_WINDOW}),
                IndicatorRequest(name="historical_volatility", params={"window": self.settings.VOL_WINDOW, "annualization": self.settings.VOL_ANNUALIZATION}),
                IndicatorRequest(name="range_percent", params={"window": self.settings.VOL_RANGE_WINDOW}),
                IndicatorRequest(name="gap_percent", params={"window": self.settings.VOL_GAP_WINDOW}),
                IndicatorRequest(name="bb_width_percentile", params={"window": self.settings.VOL_BB_WINDOW, "std": self.settings.VOL_BB_STD, "rank_window": self.settings.VOL_RANK_WINDOW}),
            ])

        # Advanced features
        if level in ["advanced", "full"]:
            requests.extend([
                IndicatorRequest(name="realized_volatility", params={"window": self.settings.VOL_WINDOW, "annualization": self.settings.VOL_ANNUALIZATION}),
                IndicatorRequest(name="parkinson_volatility", params={"window": self.settings.VOL_WINDOW, "annualization": self.settings.VOL_ANNUALIZATION}),
                IndicatorRequest(name="garman_klass_volatility", params={"window": self.settings.VOL_WINDOW, "annualization": self.settings.VOL_ANNUALIZATION}),
                IndicatorRequest(name="rogers_satchell_volatility", params={"window": self.settings.VOL_WINDOW, "annualization": self.settings.VOL_ANNUALIZATION}),
                IndicatorRequest(name="atr_percentile", params={"atr_window": self.settings.VOL_ATR_WINDOW, "rank_window": self.settings.VOL_RANK_WINDOW}),
                IndicatorRequest(name="volatility_zscore", params={"vol_window": self.settings.VOL_WINDOW, "z_window": self.settings.VOL_Z_WINDOW}),
                IndicatorRequest(name="volatility_compression", params={"bb_window": self.settings.VOL_BB_WINDOW, "atr_window": self.settings.VOL_ATR_WINDOW, "rank_window": self.settings.VOL_RANK_WINDOW}),
                IndicatorRequest(name="volatility_expansion", params={"bb_window": self.settings.VOL_BB_WINDOW, "atr_window": self.settings.VOL_ATR_WINDOW, "rank_window": self.settings.VOL_RANK_WINDOW}),
                IndicatorRequest(name="volatility_regime", params={"vol_window": self.settings.VOL_WINDOW, "rank_window": self.settings.VOL_REGIME_RANK_WINDOW}),
                IndicatorRequest(name="volatility_composite", params={"vol_window": self.settings.VOL_WINDOW, "atr_window": self.settings.VOL_ATR_WINDOW, "rank_window": self.settings.VOL_RANK_WINDOW}),
            ])

        return requests

    def build_basic_volatility_features(self, market_data: Union[MarketDataFrame, pd.DataFrame]) -> IndicatorBatchResult:
        requests = self.default_volatility_requests(level="basic")
        return self.engine.calculate_many(market_data, requests)

    def build_advanced_volatility_features(self, market_data: Union[MarketDataFrame, pd.DataFrame]) -> IndicatorBatchResult:
        requests = self.default_volatility_requests(level="advanced")
        return self.engine.calculate_many(market_data, requests)

    def build_full_volatility_features(self, market_data: Union[MarketDataFrame, pd.DataFrame]) -> IndicatorBatchResult:
        requests = self.default_volatility_requests(level="full")
        return self.engine.calculate_many(market_data, requests)

    def add_features(self, market_data, level: str = "basic"):
        return market_data.copy()
