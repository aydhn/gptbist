import pandas as pd
import logging
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.data_service import MarketDataService
from bist_signal_bot.ml.models import (
    MLDatasetRequest, MLDatasetResult, MLDatasetStatus, DatasetSplitMode,
    MLTaskType, LabelConfig, LabelType, FeatureConfig, FeatureSetLevel, PreprocessingConfig, MLDatasetSchema
)
from bist_signal_bot.ml.feature_builder import MLFeatureBuilder
from bist_signal_bot.ml.labels import LabelBuilder
from bist_signal_bot.ml.preprocessing import MLPreprocessor
from bist_signal_bot.ml.leakage import MLLeakageGuard
from bist_signal_bot.ml.schema import MLSchemaBuilder
from bist_signal_bot.ml.feature_store import FeatureStore
from bist_signal_bot.core.exceptions import MLDatasetError

logger = logging.getLogger(__name__)

class MLDatasetBuilder:
    def __init__(self,
                 data_service,
                 feature_builder: MLFeatureBuilder | None = None,
                 label_builder: LabelBuilder | None = None,
                 preprocessor: MLPreprocessor | None = None,
                 leakage_guard: MLLeakageGuard | None = None,
                 schema_builder: MLSchemaBuilder | None = None,
                 feature_store: FeatureStore | None = None,
                 settings: Settings | None = None,
                 logger_instance: logging.Logger | None = None):
        self.settings = settings or Settings()
        self.logger = logger_instance or logger
        self.data_service = data_service
        self.feature_builder = feature_builder or MLFeatureBuilder(settings=self.settings)
        self.label_builder = label_builder or LabelBuilder(settings=self.settings)
        self.preprocessor = preprocessor or MLPreprocessor()
        self.leakage_guard = leakage_guard or MLLeakageGuard()
        self.schema_builder = schema_builder or MLSchemaBuilder()
        self.feature_store = feature_store or FeatureStore(settings=self.settings)

    def build_for_symbol(self, symbol: str, request: MLDatasetRequest) -> tuple[pd.DataFrame | None, list[str]]:
        issues = []
        try:
            # 1. Fetch data
            data = self.data_service.get_ohlcv(symbol=symbol, timeframe=request.timeframe, period=request.period) #

            if data is None or data.data.empty:
                issues.append(f"{symbol}: No data returned.")
                return None, issues

            df = data.data.copy()

            # 2. Build features
            # 2. Add labels first so it can access 'close'
            df = self.label_builder.add_labels(df, request.label_config)

            # 3. Build features (this may drop raw ohlcv)
            df = self.feature_builder.build_features(df, request.feature_config, symbol, request.timeframe)

            # 4. Leakage guard (basic checks on single symbol before processing)
            # Find feature/label cols
            raw_feature_cols = self.feature_builder.identify_feature_columns(df)
            raw_label_cols = self.schema_builder.identify_label_columns(df)

            # Label should not be in features
            self.leakage_guard.validate_label_not_in_features(raw_feature_cols, raw_label_cols)
            # No future features
            issues.extend(self.leakage_guard.validate_no_future_feature_columns(df, raw_feature_cols))

            # 5. Preprocessing
            df = self.preprocessor.preprocess(df, request.preprocessing_config, raw_feature_cols, raw_label_cols)

            # ensure standard metadata columns exist
            if "symbol" not in df.columns:
                df["symbol"] = symbol
            if "timeframe" not in df.columns:
                df["timeframe"] = request.timeframe
            # Assuming timestamp is index or a column, if it's index move it to column
            if "timestamp" not in df.columns:
                if df.index.name == "timestamp" or "timestamp" in df.index.names:
                    df = df.reset_index()
                elif isinstance(df.index, pd.DatetimeIndex):
                    df = df.reset_index(names=["timestamp"])

            return df, issues

        except Exception as e:
            msg = f"Failed to build dataset for {symbol}: {e}"
            self.logger.error(msg)
            issues.append(msg)
            return None, issues

    def build_dataset(self, request: MLDatasetRequest) -> MLDatasetResult:
        started_at = datetime.now(timezone.utc)
        issues = []
        dfs = []

        request.validate_request()

        # Build per symbol
        for sym in request.symbols:
            df, sym_issues = self.build_for_symbol(sym, request)
            issues.extend(sym_issues)
            if df is not None and not df.empty:
                dfs.append(df)

        if not dfs:
            return MLDatasetResult(
                request=request,
                status=MLDatasetStatus.EMPTY,
                data=pd.DataFrame(),
                schema_=MLDatasetSchema(symbol_col="symbol", timestamp_col="timestamp", feature_cols=[], label_cols=[], metadata_cols=[], excluded_cols=[], generated_at=started_at),
                issues=issues,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc)
            )

        # Concat
        try:
            combined_df = pd.concat(dfs, ignore_index=True)
            if "timestamp" in combined_df.columns and "symbol" in combined_df.columns:
                combined_df.sort_values(by=["timestamp", "symbol"], inplace=True)
                combined_df.reset_index(drop=True, inplace=True)
        except Exception as e:
            issues.append(f"Failed to concatenate dataset: {e}")
            return MLDatasetResult(
                request=request, status=MLDatasetStatus.FAILED, data=pd.DataFrame(),
                schema_=MLDatasetSchema(symbol_col="symbol", timestamp_col="timestamp", feature_cols=[], label_cols=[], metadata_cols=[], excluded_cols=[], generated_at=started_at),
                issues=issues, started_at=started_at, finished_at=datetime.now(timezone.utc)
            )

        # Build Schema
        try:
            schema = self.schema_builder.build_schema(combined_df, request.feature_config, request.label_config)
        except Exception as e:
            issues.append(f"Failed to build schema: {e}")
            return MLDatasetResult(
                request=request, status=MLDatasetStatus.FAILED, data=combined_df,
                schema_=MLDatasetSchema(symbol_col="symbol", timestamp_col="timestamp", feature_cols=[], label_cols=[], metadata_cols=[], excluded_cols=[], generated_at=started_at),
                issues=issues, started_at=started_at, finished_at=datetime.now(timezone.utc)
            )

        # Leakage guard (final check)
        leakage_issues = self.leakage_guard.run_all_checks(combined_df, schema)
        issues.extend(leakage_issues)

        # Split dataset
        train_df, test_df = self.split_dataset(combined_df, request)

        status = MLDatasetStatus.SUCCESS
        if issues:
            status = MLDatasetStatus.PARTIAL_SUCCESS

        # Create Result object early so we can pass to feature_store.save_dataset
        result = MLDatasetResult(
            request=request,
            status=status,
            data=combined_df,
            schema_=schema,
            train_data=train_df,
            test_data=test_df,
            issues=issues,
            row_count=len(combined_df),
            feature_count=len(schema.feature_cols),
            label_count=len(schema.label_cols),
            symbol_count=combined_df["symbol"].nunique() if "symbol" in combined_df.columns else 0,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc)
        )
        result.elapsed_seconds = (result.finished_at - result.started_at).total_seconds()

        # Save
        if request.save:
            try:
                out_files = self.feature_store.save_dataset(result)
            except Exception as e:
                issues.append(f"Failed to save dataset: {e}")
                result.status = MLDatasetStatus.PARTIAL_SUCCESS


        if getattr(self.settings, 'ENABLE_PERFORMANCE_TOOLS', False):
            try:
                from bist_signal_bot.app.performance_app import create_resource_monitor
                monitor = create_resource_monitor(self.settings)
                snap = monitor.snapshot()
                result.metadata["resource_after"] = snap.summary()
                # Estimate memory footprint safely
                if not df.empty:
                    result.metadata["memory_estimate_mb"] = df.memory_usage(deep=True).sum() / (1024 * 1024)
            except Exception:
                pass

        return result

    def split_dataset(self, data: pd.DataFrame, request: MLDatasetRequest) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
        if request.split_mode == DatasetSplitMode.NONE:
            return None, None

        if request.split_mode == DatasetSplitMode.TRAIN_TEST:
            # Time-series based split. Data should already be sorted by timestamp
            split_idx = int(len(data) * request.train_ratio)
            train_df = data.iloc[:split_idx].copy()
            test_df = data.iloc[split_idx:].copy()
            return train_df, test_df

        # Other modes just return basic splits or metadata logic
        self.logger.warning(f"Split mode {request.split_mode.value} not fully implemented in DatasetBuilder. Returning basic train/test split.")
        split_idx = int(len(data) * request.train_ratio)
        return data.iloc[:split_idx].copy(), data.iloc[split_idx:].copy()

    @staticmethod
    def build_default_request(symbols: list[str]) -> MLDatasetRequest:
        s = Settings()
        return MLDatasetRequest(
            symbols=symbols,
            source=getattr(s, 'ML_DEFAULT_SOURCE', 'mock'),
            timeframe=getattr(s, 'ML_DEFAULT_TIMEFRAME', '1d'),
            rows=getattr(s, 'ML_DEFAULT_ROWS', 500),
            task_type=MLTaskType(getattr(s, 'ML_DEFAULT_TASK_TYPE', 'CLASSIFICATION')),
            label_config=LabelConfig(
                label_type=LabelType(getattr(s, 'ML_LABEL_TYPE', 'BINARY_DIRECTION')),
                horizon_bars=getattr(s, 'ML_LABEL_HORIZON_BARS', 5),
                positive_threshold=getattr(s, 'ML_LABEL_POSITIVE_THRESHOLD', 0.02),
                negative_threshold=getattr(s, 'ML_LABEL_NEGATIVE_THRESHOLD', -0.02),
                neutral_class_enabled=getattr(s, 'ML_LABEL_NEUTRAL_CLASS_ENABLED', True),
                volatility_adjust=getattr(s, 'ML_LABEL_VOLATILITY_ADJUST', False),
                cost_adjust=getattr(s, 'ML_LABEL_COST_ADJUST', False)
            ),
            feature_config=FeatureConfig(
                feature_set_level=FeatureSetLevel(getattr(s, 'ML_DEFAULT_FEATURE_LEVEL', 'FULL')),
                include_trend=getattr(s, 'ML_INCLUDE_TREND', True),
                include_momentum=getattr(s, 'ML_INCLUDE_MOMENTUM', True),
                include_volatility=getattr(s, 'ML_INCLUDE_VOLATILITY', True),
                include_volume=getattr(s, 'ML_INCLUDE_VOLUME', True),
                include_patterns=getattr(s, 'ML_INCLUDE_PATTERNS', True),
                include_divergence=getattr(s, 'ML_INCLUDE_DIVERGENCE', True),
                include_mtf=getattr(s, 'ML_INCLUDE_MTF', False),
                include_raw_ohlcv=getattr(s, 'ML_INCLUDE_RAW_OHLCV', False),
                include_returns=getattr(s, 'ML_INCLUDE_RETURNS', True)
            ),
            preprocessing_config=PreprocessingConfig(
                drop_na_labels=getattr(s, 'ML_DROP_NA_LABELS', True),
                drop_na_features=getattr(s, 'ML_DROP_NA_FEATURES', False),
                fill_method=getattr(s, 'ML_FILL_METHOD', 'median'),
                remove_inf=getattr(s, 'ML_REMOVE_INF', True),
                winsorize=getattr(s, 'ML_WINSORIZE', False),
                winsorize_lower_pct=getattr(s, 'ML_WINSORIZE_LOWER_PCT', 0.01),
                winsorize_upper_pct=getattr(s, 'ML_WINSORIZE_UPPER_PCT', 0.99),
                standardize=getattr(s, 'ML_STANDARDIZE', False),
                robust_scale=getattr(s, 'ML_ROBUST_SCALE', False),
                max_missing_feature_pct=getattr(s, 'ML_MAX_MISSING_FEATURE_PCT', 0.50)
            ),
            split_mode=DatasetSplitMode(getattr(s, 'ML_SPLIT_MODE', 'TRAIN_TEST')),
            train_ratio=getattr(s, 'ML_TRAIN_RATIO', 0.70),
            save=getattr(s, 'ML_SAVE_DATASET', False)
        )
