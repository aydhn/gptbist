import pandas as pd
import logging
import time

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.signals.models import SignalCandidate
from bist_signal_bot.regime.models import (
    RegimeConfig, RegimeClassification, RegimeFilterResult, RegimeBatchResult, RegimeScoreMode
)
from bist_signal_bot.regime.features import RegimeFeatureBuilder
from bist_signal_bot.regime.classifier import RegimeClassifier
from bist_signal_bot.regime.filters import RegimeSignalFilter
from bist_signal_bot.core.exceptions import RegimeError

class RegimeEngine:
    def __init__(self,
                 feature_builder: RegimeFeatureBuilder | None = None,
                 classifier: RegimeClassifier | None = None,
                 signal_filter: RegimeSignalFilter | None = None,
                 settings: Settings | None = None,
                 logger: logging.Logger | None = None):

        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)

        self.feature_builder = feature_builder or RegimeFeatureBuilder(self.settings)
        self.classifier = classifier or RegimeClassifier(self.settings)
        self.signal_filter = signal_filter or RegimeSignalFilter(self.settings)

    @classmethod
    def from_settings(cls, settings: Settings) -> "RegimeEngine":
        return cls(settings=settings)

    def build_default_config(self) -> RegimeConfig:
        return RegimeConfig(
            trend_window=getattr(self.settings, 'REGIME_TREND_WINDOW', 50),
            volatility_window=getattr(self.settings, 'REGIME_VOLATILITY_WINDOW', 20),
            momentum_window=getattr(self.settings, 'REGIME_MOMENTUM_WINDOW', 20),
            liquidity_window=getattr(self.settings, 'REGIME_LIQUIDITY_WINDOW', 20),
            correlation_window=getattr(self.settings, 'REGIME_CORRELATION_WINDOW', 60),
            use_mtf=getattr(self.settings, 'REGIME_USE_MTF', False),
            use_benchmark_relative=getattr(self.settings, 'REGIME_USE_BENCHMARK_RELATIVE', False),
            mode=RegimeScoreMode(getattr(self.settings, 'REGIME_SCORE_MODE', 'FILTER_AND_SCORE')),
            min_regime_score=getattr(self.settings, 'REGIME_MIN_SCORE', 40.0),
            reject_stress_regime=getattr(self.settings, 'REGIME_REJECT_STRESS', False),
            reduce_in_stress=getattr(self.settings, 'REGIME_REDUCE_IN_STRESS', True),
            stress_reduction_factor=getattr(self.settings, 'REGIME_STRESS_REDUCTION_FACTOR', 0.50)
        )

    def classify_symbol(self, symbol: str, data: pd.DataFrame, config: RegimeConfig | None = None, benchmark_data: pd.DataFrame | None = None) -> RegimeClassification:
        if config is None:
            config = self.build_default_config()

        try:
            feature_set = self.feature_builder.build_feature_set(data, symbol, config, benchmark_data)
            classification = self.classifier.classify(feature_set, config)
            return classification
        except Exception as e:
            self.logger.error(f"Failed to classify regime for {symbol}: {e}", exc_info=True)
            raise RegimeError(f"Classification failed for {symbol}: {e}")

    def add_regime_features(self, data: pd.DataFrame, config: RegimeConfig | None = None) -> pd.DataFrame:
        if config is None:
            config = self.build_default_config()
        return self.feature_builder.add_regime_feature_columns(data, config)

    def filter_signal(self, signal: SignalCandidate, symbol: str, data: pd.DataFrame, config: RegimeConfig | None = None) -> RegimeFilterResult:
        if config is None:
            config = self.build_default_config()

        classification = self.classify_symbol(symbol, data, config)
        return self.signal_filter.filter_signal(signal, classification, config)

    def classify_many(self, data_by_symbol: dict[str, pd.DataFrame], config: RegimeConfig | None = None) -> RegimeBatchResult:
        start_time = time.time()
        classifications = []
        failed = 0

        for symbol, data in data_by_symbol.items():
            try:
                cl = self.classify_symbol(symbol, data, config)
                classifications.append(cl)
            except Exception as e:
                self.logger.warning(f"Classification failed for {symbol} in batch: {e}")
                failed += 1

        return RegimeBatchResult(
            classifications=classifications,
            requested_count=len(data_by_symbol),
            success_count=len(classifications),
            failed_count=failed,
            elapsed_seconds=time.time() - start_time
        )

    def filter_signals(self, signals: list[SignalCandidate], data_by_symbol: dict[str, pd.DataFrame], config: RegimeConfig | None = None) -> RegimeBatchResult:
        start_time = time.time()
        results = []
        failed = 0

        for signal in signals:
            symbol = signal.symbol
            if symbol not in data_by_symbol:
                self.logger.warning(f"No data for {symbol} to filter signal")
                failed += 1
                continue

            try:
                res = self.filter_signal(signal, symbol, data_by_symbol[symbol], config)
                results.append(res)
            except Exception as e:
                self.logger.warning(f"Filtering failed for {symbol} signal: {e}")
                failed += 1

        return RegimeBatchResult(
            filter_results=results,
            requested_count=len(signals),
            success_count=len(results),
            failed_count=failed,
            elapsed_seconds=time.time() - start_time
        )
