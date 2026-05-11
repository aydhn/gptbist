import logging
import pandas as pd
from datetime import datetime, timezone
import time
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.ml.models import MLDatasetSchema
from bist_signal_bot.ml.training.models import (
    MLPredictionRequest, MLPredictionResult, MLPredictionItem, MLPredictionType, MLModelType, MLTaskType
)
from bist_signal_bot.ml.training.registry import MLModelRegistry
from bist_signal_bot.core.exceptions import MLPredictionError

logger = logging.getLogger(__name__)

class MLPredictor:
    def __init__(self,
                 registry: MLModelRegistry,
                 dataset_builder=None, # avoid circular import if typed MLDatasetBuilder
                 settings: Settings | None = None,
                 logger: logging.Logger | None = None):
        self.registry = registry
        self.dataset_builder = dataset_builder
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)

    def predict_from_dataset(self, model_id: str | None, model_path: str | None, dataset: pd.DataFrame, schema: MLDatasetSchema | None = None) -> MLPredictionResult:
        start_time = time.time()
        generated_at = datetime.now(timezone.utc)
        issues = []

        try:
            if model_id:
                estimator, preprocessor, artifact_or_dict = self.registry.load_model(model_id)
                if hasattr(artifact_or_dict, "model_dump"):
                    artifact_dict = artifact_or_dict.model_dump()
                else:
                    artifact_dict = artifact_or_dict
            elif model_path:
                estimator, preprocessor, artifact_dict = self.registry.load_model_by_path(Path(model_path))
                model_id = artifact_dict.get("model_id", "unknown")
            else:
                raise MLPredictionError("Either model_id or model_path must be provided")

            feature_cols = artifact_dict.get("feature_cols", [])
            if not feature_cols:
                raise MLPredictionError("Model artifact has no feature_cols")

            missing = [c for c in feature_cols if c not in dataset.columns]
            if missing:
                raise MLPredictionError(f"Dataset is missing required feature columns: {missing[:5]}...")

            df = dataset.copy()
            if preprocessor:
                # the preprocessor has transform_live method which internally checks feature_cols
                try:
                    df_feats = preprocessor.transform_live(df)
                except AttributeError:
                    # fallback if preprocessor is just sklearn object
                    df_feats = df[feature_cols].copy()
                    df_feats.replace([float("inf"), -float("inf")], float("nan"), inplace=True)
                    df_feats = pd.DataFrame(preprocessor.transform(df_feats), columns=feature_cols, index=df.index)
            else:
                df_feats = df[feature_cols].copy()

            predictions = estimator.predict(df_feats)
            probabilities = None
            if hasattr(estimator, "predict_proba"):
                try:
                    probabilities = estimator.predict_proba(df_feats)
                except:
                    pass

            task_type = MLTaskType(artifact_dict.get("task_type", MLTaskType.UNKNOWN))
            ptype = MLPredictionType.REGRESSION_VALUE if task_type == MLTaskType.REGRESSION else MLPredictionType.CLASS_LABEL

            items = []
            for i in range(len(dataset)):
                row = dataset.iloc[i]
                sym = row.get("symbol", "UNKNOWN")
                ts = row.get("timestamp", None)

                pred_val = float(predictions[i]) if isinstance(predictions[i], (int, float)) else str(predictions[i])

                prob_pos = None
                prob_neg = None
                if probabilities is not None:
                    # simplistic assumption for binary classification [neg, pos]
                    if probabilities.shape[1] >= 2:
                        prob_neg = float(probabilities[i][0])
                        prob_pos = float(probabilities[i][1])

                items.append(MLPredictionItem(
                    symbol=sym,
                    timestamp=pd.to_datetime(ts) if pd.notna(ts) else None,
                    prediction_type=ptype,
                    predicted_value=pred_val,
                    probability_positive=prob_pos,
                    probability_negative=prob_neg,
                    raw_prediction=pred_val
                ))

            res = MLPredictionResult(
                model_id=model_id,
                predictions=items,
                row_count=len(items),
                generated_at=generated_at,
                elapsed_seconds=time.time() - start_time,
                issues=issues
            )
            return res

        except Exception as e:
            self.logger.exception(f"Prediction failed: {e}")
            return MLPredictionResult(
                model_id=model_id or "error",
                predictions=[],
                row_count=0,
                generated_at=generated_at,
                elapsed_seconds=time.time() - start_time,
                issues=[str(e)]
            )

    def predict_for_symbols(self, request: MLPredictionRequest) -> MLPredictionResult:
        start_time = time.time()
        generated_at = datetime.now(timezone.utc)

        if request.dataset_path:
            from bist_signal_bot.ml.feature_store import FeatureStore
            fs = FeatureStore(self.settings)
            df = fs.load_dataset(Path(request.dataset_path))
            # Optional: handle latest row filtering if requested
            if getattr(self.settings, "ML_PREDICTION_LATEST_ONLY", True):
                if "timestamp" in df.columns and "symbol" in df.columns:
                    df = df.sort_values("timestamp").groupby("symbol").tail(1).reset_index(drop=True)
            return self.predict_from_dataset(request.model_id, request.model_path, df)

        elif self.dataset_builder:
            from bist_signal_bot.ml.models import MLDatasetRequest, MLTaskType, LabelConfig, LabelType, FeatureConfig, FeatureSetLevel, DatasetSplitMode, PreprocessingConfig
            # create a minimal request just to get features.
            # since we don't need labels for prediction, we can configure a dummy label or handle it
            req = MLDatasetRequest(
                symbols=request.symbols,
                source=request.source,
                timeframe=request.timeframe,
                rows=request.rows or getattr(self.settings, "ML_PREDICTION_MAX_ROWS", 50),
                task_type=MLTaskType.UNKNOWN,
                label_config=LabelConfig(label_type=LabelType.FORWARD_RETURN, horizon_bars=1), # dummy
                feature_config=FeatureConfig(feature_set_level=FeatureSetLevel.BASIC), # ideally read from artifact!
                preprocessing_config=PreprocessingConfig(drop_na_labels=False), # IMPORTANT: do not drop na labels for live
                split_mode=DatasetSplitMode.NONE,
                save=False
            )

            # Note: A real implementation would parse the model artifact to get the exact FeatureConfig used.
            # We assume dataset_builder.build_dataset will produce the features.
            ds_result = self.dataset_builder.build_dataset(req)
            if ds_result.status.value == "FAILED":
                return MLPredictionResult(
                    model_id=request.model_id or "error",
                    predictions=[],
                    row_count=0,
                    generated_at=generated_at,
                    elapsed_seconds=time.time() - start_time,
                    issues=["Feature generation failed"] + ds_result.issues
                )

            df = ds_result.data
            if getattr(self.settings, "ML_PREDICTION_LATEST_ONLY", True):
                if "timestamp" in df.columns and "symbol" in df.columns:
                    df = df.sort_values("timestamp").groupby("symbol").tail(1).reset_index(drop=True)

            return self.predict_from_dataset(request.model_id, request.model_path, df, ds_result.schema_)

        else:
            raise MLPredictionError("Neither dataset_path nor dataset_builder provided")
