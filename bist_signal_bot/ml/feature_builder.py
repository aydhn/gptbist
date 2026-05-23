import pandas as pd
import numpy as np
import logging
from bist_signal_bot.ml.models import FeatureConfig, FeatureSetLevel
from bist_signal_bot.config.settings import Settings

# Placeholder imports assuming the feature builders exist from previous phases
from bist_signal_bot.features.trend_features import TrendFeatureBuilder
from bist_signal_bot.features.momentum_features import MomentumFeatureBuilder
from bist_signal_bot.features.volatility_features import VolatilityFeatureBuilder
from bist_signal_bot.features.volume_features import VolumeFeatureBuilder
from bist_signal_bot.features.pattern_features import PatternFeatureBuilder
from bist_signal_bot.features.divergence_features import DivergenceFeatureBuilder
from bist_signal_bot.features.multi_timeframe_features import MultiTimeframeFeatureBuilder
from bist_signal_bot.regime.engine import RegimeEngine
from bist_signal_bot.regime.models import RegimeConfig

logger = logging.getLogger(__name__)

class MLFeatureBuilder:
    def __init__(self,
                 trend_builder: TrendFeatureBuilder | None = None,
                 momentum_builder: MomentumFeatureBuilder | None = None,
                 volatility_builder: VolatilityFeatureBuilder | None = None,
                 volume_builder: VolumeFeatureBuilder | None = None,
                 pattern_builder: PatternFeatureBuilder | None = None,
                 divergence_builder: DivergenceFeatureBuilder | None = None,
                 mtf_builder: MultiTimeframeFeatureBuilder | None = None,
                 regime_engine: RegimeEngine | None = None,
                 settings: Settings | None = None):
        self.settings = settings or Settings()
        self.trend_builder = trend_builder or TrendFeatureBuilder(settings=self.settings)
        self.momentum_builder = momentum_builder or MomentumFeatureBuilder(settings=self.settings)
        self.volatility_builder = volatility_builder or VolatilityFeatureBuilder(settings=self.settings)
        self.volume_builder = volume_builder or VolumeFeatureBuilder(settings=self.settings)
        self.pattern_builder = pattern_builder or PatternFeatureBuilder(settings=self.settings)
        self.divergence_builder = divergence_builder or DivergenceFeatureBuilder(settings=self.settings)
        self.mtf_builder = mtf_builder or MultiTimeframeFeatureBuilder(settings=self.settings)
        self.regime_engine = regime_engine or RegimeEngine(settings=self.settings)

    def build_features(self, data: pd.DataFrame, config: FeatureConfig, symbol: str, timeframe: str) -> pd.DataFrame:
        df = data.copy()

        # Inject Optional Profiler
        profiler = None
        if getattr(self.settings, 'ENABLE_PERFORMANCE_PROFILING', False):
            from bist_signal_bot.app.performance_app import create_local_profiler
            profiler = create_local_profiler(self.settings)

        # Add returns first
        if config.include_returns:
            span = profiler.timer.start_span("returns_features") if profiler else None
            df = self.add_return_features(df)
            if span: profiler.timer.finish_span(span.span_id)

        # Add basic feature modules if requested
        if config.include_trend:
            span = profiler.timer.start_span("trend_features") if profiler else None
            try:
                df = self.trend_builder.add_features(df, level=config.feature_set_level.value.lower())
            except Exception as e:
                logger.warning(f"Failed to add trend features: {e}")
            if span: profiler.timer.finish_span(span.span_id)

        if config.include_momentum:
            span = profiler.timer.start_span("momentum_features") if profiler else None
            try:
                df = self.momentum_builder.add_features(df, level=config.feature_set_level.value.lower())
            except Exception as e:
                logger.warning(f"Failed to add momentum features: {e}")
            if span: profiler.timer.finish_span(span.span_id)

        if config.include_volatility:
            try:
                df = self.volatility_builder.add_features(df, level=config.feature_set_level.value.lower())
            except Exception as e:
                logger.warning(f"Failed to add volatility features: {e}")

        if config.include_volume:
            try:
                df = self.volume_builder.add_features(df, level=config.feature_set_level.value.lower())
            except Exception as e:
                logger.warning(f"Failed to add volume features: {e}")

        if config.include_patterns:
            try:
                df = self.pattern_builder.add_features(df, level=config.feature_set_level.value.lower())
            except Exception as e:
                logger.warning(f"Failed to add pattern features: {e}")

        if config.include_divergence:
            try:
                df = self.divergence_builder.add_features(df, level=config.feature_set_level.value.lower())
            except Exception as e:
                logger.warning(f"Failed to add divergence features: {e}")

        if config.include_mtf:
            try:
                df = self.mtf_builder.add_features(df, symbol=symbol, base_timeframe=timeframe)
            except Exception as e:
                logger.warning(f"Failed to add MTF features: {e}")

        if getattr(config, "include_regime", False):
            try:
                regime_config = RegimeConfig()
                regime_df = self.regime_engine.add_regime_features(df, regime_config)
                rename_cols = {col: f"feat_{col}" for col in regime_df.columns if col.startswith("regime_")}
                regime_df.rename(columns=rename_cols, inplace=True)
                cols_to_keep = [c for c in regime_df.columns if c not in df.columns]
                df = pd.concat([df, regime_df[cols_to_keep]], axis=1)
            except Exception as e:
                logger.warning(f"Failed to add regime features: {e}")

        # ensure standard names
        df = self.standardize_feature_column_names(df)

        # remove raw ohlcv if requested
        if not config.include_raw_ohlcv:
            cols_to_drop = [c for c in ["open", "high", "low", "close", "volume"] if c in df.columns]
            df.drop(columns=cols_to_drop, inplace=True, errors="ignore")

        # Add metadata columns if not present
        if "symbol" not in df.columns:
            df["symbol"] = symbol
        if "timeframe" not in df.columns:
            df["timeframe"] = timeframe

        return df

    def add_return_features(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()

        # historical returns
        if "close" in df.columns:
            df["feat_return_1"] = df["close"].pct_change(1)
            df["feat_log_return_1"] = np.log(df["close"] / df["close"].shift(1))
            df["feat_return_5"] = df["close"].pct_change(5)
            df["feat_return_20"] = df["close"].pct_change(20)

        if "open" in df.columns and "close" in df.columns:
            df["feat_close_to_open_return"] = (df["open"] - df["close"].shift(1)) / df["close"].shift(1)

        if "high" in df.columns and "low" in df.columns and "open" in df.columns:
            df["feat_intraday_range_pct"] = (df["high"] - df["low"]) / df["open"]

        return df

    def standardize_feature_column_names(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        rename_map = {}

        exclude_from_feat_prefix = [
            "symbol", "timestamp", "timeframe", "open", "high", "low", "close", "volume"
        ]

        for col in df.columns:
            if col in exclude_from_feat_prefix:
                continue
            if col.startswith("label_") or col.startswith("target_") or col.startswith("future_"):
                continue
            if not col.startswith("feat_"):
                # it's a feature from an indicator builder that doesn't use feat_ prefix
                rename_map[col] = f"feat_{col}"

        if rename_map:
            df.rename(columns=rename_map, inplace=True)

        return df

    def identify_feature_columns(self, data: pd.DataFrame) -> list[str]:
        exclude = ["symbol", "timestamp", "timeframe", "open", "high", "low", "close", "volume"]
        feats = []
        for col in data.columns:
            if col in exclude:
                continue
            if col.startswith("label_") or col.startswith("target_") or col.startswith("future_"):
                continue
            feats.append(col)
        return feats

    def build_feature_set_name(self, config: FeatureConfig) -> str:
        parts = [config.feature_set_level.value.lower()]
        if config.include_trend: parts.append("trend")
        if config.include_momentum: parts.append("mom")
        if config.include_volatility: parts.append("vol")
        if config.include_volume: parts.append("volm")
        if config.include_patterns: parts.append("pat")
        if config.include_divergence: parts.append("div")
        if config.include_mtf: parts.append("mtf")
        if getattr(config, "include_regime", False): parts.append("reg")
        return "_".join(parts)
