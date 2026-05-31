import pandas as pd
import logging
import time
from datetime import datetime, timezone
from typing import Any
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.ml.training.registry import MLModelRegistry
from bist_signal_bot.ml.training.models import MLModelArtifact, MLTaskType
from bist_signal_bot.ml.inference.models import (
    MLInferenceInput, MLInferenceResult, MLSignalFilterResult, MLInferenceBatchResult,
    MLInferenceConfig, MLFilterDecision, MLPredictionDirection, MLFeatureAlignmentStatus, MLInferenceMode, MLScoreBlendMode
)
from bist_signal_bot.ml.inference.feature_alignment import MLFeatureAligner
from bist_signal_bot.ml.inference.scoring import MLPredictionScorer
from bist_signal_bot.security.path_guard import PathGuard

from bist_signal_bot.ml.inference.filtering import MLSignalFilter
from bist_signal_bot.signals.models import SignalCandidate
from bist_signal_bot.core.exceptions import MLInferenceError

logger = logging.getLogger(__name__)

# ContextFusion can collect from this engine's outputs
class MLInferenceEngine:
    def __init__(self,
                 model_registry: MLModelRegistry,
                 dataset_builder=None, # Typed any to prevent circular
                 feature_builder=None,
                 aligner: MLFeatureAligner | None = None,
                 scorer: MLPredictionScorer | None = None,
                 signal_filter: MLSignalFilter | None = None,
                 settings: Settings | None = None,
                 logger: logging.Logger | None = None):
        self.model_registry = model_registry
        self.path_guard = PathGuard([model_registry.base_dir])
        self.dataset_builder = dataset_builder
        self.feature_builder = feature_builder
        self.aligner = aligner or MLFeatureAligner()
        self.scorer = scorer or MLPredictionScorer()
        self.settings = settings or Settings()
        self.signal_filter = signal_filter or MLSignalFilter(scorer=self.scorer, settings=self.settings)
        self.logger = logger or logging.getLogger(__name__)

    @classmethod
    def from_settings(cls, settings: Settings) -> "MLInferenceEngine":
        registry = MLModelRegistry(settings=settings)
        # Import dynamically here to avoid circular imports. Usually feature_builder and dataset_builder are available.
        from bist_signal_bot.ml.feature_builder import MLFeatureBuilder
        from bist_signal_bot.ml.dataset_builder import MLDatasetBuilder
        from bist_signal_bot.data.data_service import MarketDataService

        fb = MLFeatureBuilder(settings=settings)
        try:
            ds = MarketDataService(settings=settings)
            db = MLDatasetBuilder(data_service=ds, settings=settings)
        except Exception:
            db = None

        return cls(model_registry=registry, dataset_builder=db, feature_builder=fb, settings=settings)

    def build_default_config(self, model_id: str | None = None) -> MLInferenceConfig:
        cfg = MLInferenceConfig(
            enabled=self.settings.ENABLE_ML_INFERENCE,
            model_id=model_id or getattr(self.settings, "ML_INFERENCE_DEFAULT_MODEL_ID", None),
            mode=MLInferenceMode(getattr(self.settings, "ML_INFERENCE_MODE", "SCORE_AND_FILTER")),
            blend_mode=MLScoreBlendMode(getattr(self.settings, "ML_SCORE_BLEND_MODE", "WEIGHTED_AVERAGE")),
            ml_score_weight=getattr(self.settings, "ML_SCORE_WEIGHT", 0.35),
            strategy_score_weight=getattr(self.settings, "ML_STRATEGY_SCORE_WEIGHT", 0.65),
            min_probability_positive=getattr(self.settings, "ML_MIN_PROBABILITY_POSITIVE", 0.55),
            max_probability_negative=getattr(self.settings, "ML_MAX_PROBABILITY_NEGATIVE", 0.60),
            min_prediction_score=getattr(self.settings, "ML_MIN_PREDICTION_SCORE", 50.0),
            reject_on_missing_features=getattr(self.settings, "ML_REJECT_ON_MISSING_FEATURES", True),
            allow_extra_features=getattr(self.settings, "ML_ALLOW_EXTRA_FEATURES", True),
            latest_only=getattr(self.settings, "ML_LATEST_ONLY", True),
        )
        return cfg

    def load_artifact(self, config: MLInferenceConfig) -> tuple[Any, Any, dict[str, Any]]:
        if config.model_id:
            return self.model_registry.load_model(config.model_id)
        elif config.model_path:
            return self.model_registry.load_model_by_path(Path(config.model_path))
        raise MLInferenceError("Neither model_id nor model_path provided in config.")

    def build_live_features(self, symbol: str, data: pd.DataFrame, artifact: dict[str, Any], timeframe: str) -> pd.DataFrame:
        df = data.copy()

        required_features = artifact.get("feature_cols", [])
        if not required_features:
            raise MLInferenceError("Model artifact missing feature_cols")

        # If it doesn't already contain the features, try to build them.
        missing = [f for f in required_features if f not in df.columns]

        # Determine if we should attempt building. In practice, building from OHLCV is needed
        # if the dataframe is just basic raw data and missing features.
        if missing and self.feature_builder:
            from bist_signal_bot.ml.models import FeatureConfig, FeatureSetLevel
            # Build a default feature config as a fallback.
            # In a real scenario, this might need to be parsed from the artifact.
            fconfig = FeatureConfig(feature_set_level=FeatureSetLevel.FULL)
            df = self.feature_builder.build_features(df, config=fconfig, symbol=symbol, timeframe=timeframe)

        # Drop any leakage columns.
        leaky = ["label_", "target_", "future_", "fwd", "shifted_minus", "lead"]
        cols_to_drop = [c for c in df.columns if any(l in c.lower() for l in leaky)]
        df.drop(columns=cols_to_drop, inplace=True, errors='ignore')

        return df

    def predict(self, input_data: MLInferenceInput) -> MLInferenceResult:
        start_time = time.time()
        generated_at = datetime.now(timezone.utc)
        reasons = []
        warnings = []

        try:
            if not input_data.config.enabled:
                return self._create_disabled_result(input_data, start_time, generated_at)

            estimator, preprocessor, artifact_dict = self.load_artifact(input_data.config)
            model_id = input_data.config.model_id or input_data.config.model_path or "unknown"

            # Governance Check
            if getattr(self.settings, "RUNTIME_MODEL_REGISTRY_ENABLED", False):
                try:
                    gov_engine = create_model_governance_engine(self.settings)
                    assessment = gov_engine.assess_model(model_id)
                    if assessment.status == ModelGovernanceStatus.BLOCKED or \
                       (assessment.status == ModelGovernanceStatus.FAIL and getattr(self.settings, "RUNTIME_INFERENCE_BLOCK_GOVERNANCE_FAIL", False)):
                        reasons.append(f"Model {model_id} governance blocked/failed")
                        from bist_signal_bot.ml.inference.models import MLFeatureAlignmentResult, MLFeatureAlignmentStatus
                        dummy_align = MLFeatureAlignmentResult(status=MLFeatureAlignmentStatus.FAILED)
                        res = self._create_error_result(input_data, dummy_align, reasons, warnings, start_time, generated_at)
                        res.governance_status = assessment.status
                        return res

                    # Warning logic
                    if assessment.status == ModelGovernanceStatus.WATCH and getattr(self.settings, "RUNTIME_INFERENCE_WARN_ON_MODEL_DRIFT", True):
                        warnings.append(f"Model {model_id} is on WATCH status")
                except Exception as e:
                    self.logger.warning(f"Failed to check model governance: {e}")


            # 1. Prepare features
            df_live = self.build_live_features(input_data.symbol, input_data.data, artifact_dict, input_data.timeframe)
            if input_data.config.latest_only:
                df_live = df_live.tail(1).reset_index(drop=True)

            # 2. Align features
            feature_cols = artifact_dict.get("feature_cols", [])
            alignment = self.aligner.align_features(
                df_live,
                feature_cols,
                allow_extra_features=input_data.config.allow_extra_features,
                reject_on_missing=input_data.config.reject_on_missing_features
            )
            warnings.extend(alignment.issues)

            if alignment.status in [MLFeatureAlignmentStatus.FAILED, MLFeatureAlignmentStatus.MISSING_FEATURES]:
                reasons.append("Feature alignment failed or missing features rejected.")
                return self._create_error_result(input_data, alignment, reasons, warnings, start_time, generated_at)

            df_aligned = alignment.aligned_data

            # 3. Transform via preprocessor if any
            if preprocessor:
                try:
                    df_aligned = preprocessor.transform_live(df_aligned)
                except AttributeError:
                    df_aligned.replace([float("inf"), -float("inf")], float("nan"), inplace=True)
                    df_aligned = pd.DataFrame(preprocessor.transform(df_aligned), columns=feature_cols, index=df_aligned.index)

            # 4. Predict
            predictions = estimator.predict(df_aligned)
            pred_val = predictions[-1]

            probabilities = None
            if hasattr(estimator, "predict_proba"):
                try:
                    probabilities = estimator.predict_proba(df_aligned)
                except:
                    pass

            prob_pos = None
            prob_neg = None
            if probabilities is not None and len(probabilities) > 0:
                if probabilities.shape[1] >= 2:
                    prob_neg = float(probabilities[-1][0])
                    prob_pos = float(probabilities[-1][1])

            # Convert to dictionary simulating MLPredictionItem
            task_type = artifact_dict.get("task_type", "CLASSIFICATION")
            pred_item = {
                "prediction_type": "REGRESSION_VALUE" if task_type == "REGRESSION" else "CLASS_LABEL",
                "predicted_value": pred_val,
                "probability_positive": prob_pos,
                "probability_negative": prob_neg,
            }

            # 5. Score
            score, direction, score_reasons = self.scorer.prediction_to_score(pred_item)
            reasons.extend(score_reasons)

            res = MLInferenceResult(
                symbol=input_data.symbol,
                governance_status=assessment.status if 'assessment' in locals() else None,
                validation_status=assessment.validation_status if 'assessment' in locals() else None,
                calibration_status=assessment.calibration_status if 'assessment' in locals() else None,
                model_id=model_id,
                prediction_direction=direction,
                prediction_value=pred_val,
                prediction_score=score,
                probability_positive=prob_pos,
                probability_negative=prob_neg,
                probability_neutral=None,
                filter_decision=MLFilterDecision.PASS,
                alignment=alignment,
                reasons=reasons,
                warnings=warnings,
                generated_at=generated_at,
                elapsed_seconds=time.time() - start_time
            )

            # 6. Apply Filter if signal exists
            if input_data.signal:
                filter_res = self.signal_filter.filter_signal(input_data.signal, res, input_data.config)
                return filter_res.inference_result

            return res

        except Exception as e:
            self.logger.exception(f"ML Inference Engine prediction failed: {e}")
            reasons.append(str(e))
            from bist_signal_bot.ml.inference.models import MLFeatureAlignmentResult, MLFeatureAlignmentStatus
            dummy_align = MLFeatureAlignmentResult(status=MLFeatureAlignmentStatus.FAILED)
            return self._create_error_result(input_data, dummy_align, reasons, warnings, start_time, generated_at)

    def filter_signal(self, signal: SignalCandidate, symbol: str, data: pd.DataFrame, config: MLInferenceConfig, timeframe: str = "1d") -> MLSignalFilterResult:
        input_data = MLInferenceInput(
            symbol=symbol,
            data=data,
            signal=signal,
            config=config,
            timeframe=timeframe
        )
        inf_res = self.predict(input_data)
        return self.signal_filter.filter_signal(signal, inf_res, config)

    def predict_batch(self, inputs: list[MLInferenceInput]) -> MLInferenceBatchResult:
        # Placeholder for real batching logic that does bulk transforms and predictions.
        # For local registry fallback, iterating handles memory gracefully for tiny models.
        results = []
        sigs = []
        for inp in inputs:
            res = self.predict(inp)
            results.append(res)
            if inp.signal:
                sigs.append(inp.signal)

        if sigs:
            # We run it through apply_to_batch which handles matching
            return self.signal_filter.apply_to_batch(sigs, results, inputs[0].config)

        return MLInferenceBatchResult(
            results=results,
            requested_count=len(inputs),
            passed_count=len([r for r in results if r.filter_decision == MLFilterDecision.PASS]),
            error_count=len([r for r in results if r.filter_decision == MLFilterDecision.ERROR]),
            rejected_count=len([r for r in results if r.filter_decision == MLFilterDecision.REJECT]),
            generated_at=datetime.now(timezone.utc),
            elapsed_seconds=sum([r.elapsed_seconds for r in results])
        )

    def _create_disabled_result(self, input_data, start_time, generated_at):
        from bist_signal_bot.ml.inference.models import MLFeatureAlignmentResult, MLFeatureAlignmentStatus
        alignment = MLFeatureAlignmentResult(status=MLFeatureAlignmentStatus.ALIGNED)
        return MLInferenceResult(
            symbol=input_data.symbol,
            model_id="disabled",
            prediction_direction=MLPredictionDirection.UNKNOWN,
            prediction_score=50.0,
            filter_decision=MLFilterDecision.SKIPPED,
            alignment=alignment,
            reasons=["Inference disabled"],
            generated_at=generated_at,
            elapsed_seconds=time.time() - start_time
        )

    def _create_error_result(self, input_data, alignment, reasons, warnings, start_time, generated_at):
        return MLInferenceResult(
            symbol=input_data.symbol,
            model_id=input_data.config.model_id or "error",
            prediction_direction=MLPredictionDirection.UNKNOWN,
            prediction_score=0.0,
            filter_decision=MLFilterDecision.ERROR,
            alignment=alignment,
            reasons=reasons,
            warnings=warnings,
            generated_at=generated_at,
            elapsed_seconds=time.time() - start_time
        )
