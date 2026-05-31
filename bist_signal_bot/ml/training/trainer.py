from typing import Any
import logging
import pandas as pd
from datetime import datetime, timezone
import time

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.ml.models import MLDatasetSchema
from bist_signal_bot.ml.training.models import (
    MLTrainInput, MLTrainResult, MLTrainStatus, MLModelArtifact, MLFeatureImportance,
    MLPreparedData, MLFeatureImportanceType, MLModelType, MLTaskType
)
from bist_signal_bot.app.model_registry_app import create_experiment_tracker, create_model_artifact_manager
from bist_signal_bot.model_registry.models import ModelKind, ModelArtifactFormat
from bist_signal_bot.ml.training.splits import MLTimeSeriesSplitter
from bist_signal_bot.ml.training.preprocessing import MLTrainingPreprocessor
from bist_signal_bot.ml.training.estimators import EstimatorFactory
from bist_signal_bot.ml.training.evaluation import MLModelEvaluator
from bist_signal_bot.ml.training.registry import MLModelRegistry
from bist_signal_bot.ml.leakage import MLLeakageGuard
from bist_signal_bot.ml.training.storage import MLTrainingReportStore
from bist_signal_bot.core.exceptions import MLTrainingError, MLLeakageError

logger = logging.getLogger(__name__)

class MLModelTrainer:
    def __init__(self,
                 estimator_factory: EstimatorFactory | None = None,
                 splitter: MLTimeSeriesSplitter | None = None,
                 evaluator: MLModelEvaluator | None = None,
                 registry: MLModelRegistry | None = None,
                 report_store: MLTrainingReportStore | None = None,
                 settings: Settings | None = None,
                 logger: logging.Logger | None = None):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)
        self.estimator_factory = estimator_factory or EstimatorFactory()
        self.splitter = splitter or MLTimeSeriesSplitter()
        self.evaluator = evaluator or MLModelEvaluator()
        self.registry = registry or MLModelRegistry(self.settings)
        self.report_store = report_store or MLTrainingReportStore(self.settings)
        self.leakage_guard = MLLeakageGuard()

    def load_dataset_from_input(self, train_input: MLTrainInput) -> tuple[pd.DataFrame, MLDatasetSchema | None]:
        if train_input.data is not None:
            return train_input.data, train_input.schema_
        elif train_input.dataset_result is not None:
            return train_input.dataset_result.data, train_input.dataset_result.schema_
        elif train_input.dataset_path is not None:
            from bist_signal_bot.ml.feature_store import FeatureStore
            fs = FeatureStore(self.settings)
            df = fs.load_dataset(Path(train_input.dataset_path))
            # try to load schema if exists
            schema = None
            schema_path = Path(train_input.dataset_path).parent / "schema.json"
            if schema_path.exists():
                import json
                try:
                    with open(schema_path, "r", encoding="utf-8") as f:
                        schema = MLDatasetSchema(**json.load(f))
                except:
                    pass
            return df, schema
        raise MLTrainingError("No valid data source provided in train_input")

    def prepare_data(self, train_input: MLTrainInput) -> MLPreparedData:
        data, schema = self.load_dataset_from_input(train_input)
        config = train_input.config

        feature_cols = config.feature_cols
        if not feature_cols and schema:
            feature_cols = schema.feature_cols
        if not feature_cols:
            feature_cols = [c for c in data.columns if c.startswith("feat_")]
            if not feature_cols:
                raise MLTrainingError("Could not determine feature_cols")

        if config.target_col not in data.columns:
            raise MLTrainingError(f"Target column {config.target_col} not found in dataset")

        # Leakage guard
        issues = self.leakage_guard.validate_no_future_feature_columns(data, feature_cols)
        if issues:
            self.logger.warning("Leakage guard warnings: " + "; ".join(issues))
            # we don't necessarily abort, just log

        if schema:
            self.leakage_guard.validate_label_not_in_features(feature_cols, schema.label_cols)
        else:
            if config.target_col in feature_cols:
                raise MLLeakageError(f"CRITICAL LEAKAGE: Target column {config.target_col} is in feature_cols")

        # Drop NaN labels
        before_drop = len(data)
        data = data.dropna(subset=[config.target_col])
        if len(data) < before_drop:
            self.logger.info(f"Dropped {before_drop - len(data)} rows due to NaN labels")

        # Split
        train_data, test_data = self.splitter.train_test_split(data, config.train_ratio, timestamp_col="timestamp" if "timestamp" in data.columns else None)

        # Limit train rows
        if config.max_train_rows and config.max_train_rows > 0:
            train_data = self.splitter.limit_train_rows(train_data, config.max_train_rows)

        self.splitter.validate_temporal_order(train_data, test_data)

        X_train_raw, y_train = self.splitter.split_features_target(train_data, feature_cols, config.target_col)
        X_test_raw, y_test = self.splitter.split_features_target(test_data, feature_cols, config.target_col)

        preprocessor = MLTrainingPreprocessor(scaler=config.scaler, imputer=config.imputer)
        X_train = preprocessor.fit_transform_train(X_train_raw)
        X_test = preprocessor.transform_test(X_test_raw)

        return MLPreparedData(
            X_train=X_train,
            X_test=X_test,
            y_train=y_train,
            y_test=y_test,
            feature_cols=feature_cols,
            target_col=config.target_col,
            train_index=X_train.index,
            test_index=X_test.index,
            preprocessor=preprocessor
        )

    def extract_feature_importance(self, estimator: Any, feature_cols: list[str]) -> list[MLFeatureImportance]:
        importances = []
        if hasattr(estimator, "feature_importances_"):
            vals = estimator.feature_importances_
            itype = MLFeatureImportanceType.MODEL_NATIVE
        elif hasattr(estimator, "coef_"):
            vals = estimator.coef_
            if len(vals.shape) > 1:
                vals = vals[0]
            # take absolute value for coefficient ranking
            vals = abs(vals)
            itype = MLFeatureImportanceType.COEFFICIENT
        else:
            return []

        if len(vals) != len(feature_cols):
            self.logger.warning("Feature importance length mismatch")
            return []

        for f, v in zip(feature_cols, vals):
            importances.append(MLFeatureImportance(feature=f, importance=float(v), importance_type=itype, rank=0))

        importances.sort(key=lambda x: abs(x.importance), reverse=True)
        for i, imp in enumerate(importances):
            imp.rank = i + 1

        return importances

    def train(self, train_input: MLTrainInput) -> MLTrainResult:
        started_at = datetime.now(timezone.utc)
        start_time = time.time()
        issues = []
        output_files = {}

        try:

            # Experiment Tracking Start
            exp_tracker = None
            run_id = None
            if getattr(self.settings, "ENABLE_MODEL_REGISTRY", False):
                try:
                    exp_tracker = create_experiment_tracker(self.settings)
                    run = exp_tracker.start_run(
                        experiment_name=config.model_type,
                        model_name=config.model_type,
                        model_kind=ModelKind.CLASSIFIER if config.task_type.value == "CLASSIFICATION" else ModelKind.REGRESSOR,
                        parameters=config.model_dump() if hasattr(config, "model_dump") else config.dict(),
                    )
                    run_id = run.run_id
                except Exception as e:
                    self.logger.warning(f"Failed to start experiment run: {e}")
                train_input.validate_input()
            config = train_input.config
            config.validate_config()

            prepared = self.prepare_data(train_input)

            estimator = self.estimator_factory.create_estimator(config)
            estimator.fit(prepared.X_train, prepared.y_train)

            y_pred = estimator.predict(prepared.X_test)
            y_proba = None
            if hasattr(estimator, "predict_proba"):
                try:
                    y_proba = estimator.predict_proba(prepared.X_test)
                except:
                    pass

            clf_metrics = None
            reg_metrics = None
            if config.task_type == MLTaskType.CLASSIFICATION:
                clf_metrics = self.evaluator.evaluate_classification(prepared.y_test, y_pred, y_proba)
                # add train class dist
                clf_metrics.class_distribution_train = {str(k): int(v) for k, v in prepared.y_train.value_counts().to_dict().items()}
            else:
                reg_metrics = self.evaluator.evaluate_regression(prepared.y_test, y_pred)

            feature_importances = self.extract_feature_importance(estimator, prepared.feature_cols)

            artifact = MLModelArtifact(
                model_id="", # to be set by registry
                model_type=config.model_type,
                task_type=config.task_type,
                target_col=config.target_col,
                feature_cols=prepared.feature_cols,
                model_path="",
                metadata_path="",
                created_at=datetime.now(timezone.utc),
                train_rows=len(prepared.X_train),
                test_rows=len(prepared.X_test),
                metrics_summary=clf_metrics.model_dump() if clf_metrics else reg_metrics.model_dump() if reg_metrics else {}
            )

            ds_name = None
            if train_input.dataset_path:
                from pathlib import Path
                ds_name = Path(train_input.dataset_path).parent.name

            artifact.model_id = self.registry.create_model_id(ds_name, config.model_type, started_at)

            res = MLTrainResult(
                status=MLTrainStatus.SUCCESS,
                config=config,
                artifact=artifact,
                classification_metrics=clf_metrics,
                regression_metrics=reg_metrics,
                feature_importance=feature_importances,
                prepared_data_summary={"train_rows": len(prepared.X_train), "test_rows": len(prepared.X_test)},
                issues=issues,
                output_files=output_files,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                elapsed_seconds=time.time() - start_time
            )

            if config.save_model:
                artifact = self.registry.save_model(estimator, prepared.preprocessor, artifact, res)
                res.artifact = artifact

            if config.save_report:
                saved_files = self.report_store.save_train_result(res)
                res.output_files.update({str(k): str(v) for k,v in saved_files.items()})


            # Experiment Tracking Complete
            if exp_tracker and run_id:
                try:
                    metrics = res.classification_metrics.model_dump() if res.classification_metrics else res.regression_metrics.model_dump() if res.regression_metrics else {}
                    exp_tracker.complete_run(run_id, metrics)
                except Exception as e:
                    self.logger.warning(f"Failed to complete experiment run: {e}")

            # Artifact Registration
            if getattr(self.settings, "ENABLE_MODEL_REGISTRY", False) and config.save_model and hasattr(res, "artifact") and res.artifact.model_path:
                try:
                    art_mgr = create_model_artifact_manager(self.settings)
                    from pathlib import Path
                    art_mgr.register_artifact(
                        path=Path(res.artifact.model_path),
                        model_id=res.artifact.model_id,
                        artifact_format=ModelArtifactFormat.PICKLE, # Assuming pickle for now
                        confirm=True
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to register model artifact: {e}")

            from bist_signal_bot.core.audit import AuditLogger, AuditEventType, AuditEvent
            from bist_signal_bot.storage.paths import get_metadata_dir
            audit = AuditLogger(self.settings)
            audit.log_event(AuditEvent(
                event_type=AuditEventType.ML_TRAINING_COMPLETED,
                message=f"Model trained successfully: {artifact.model_id}",
                metadata=res.summary()
            ))

            return res

        except Exception as e:
            self.logger.exception(f"ML Training failed: {e}")
            return MLTrainResult(
                status=MLTrainStatus.FAILED,
                config=train_input.config,
                issues=[str(e)],
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                elapsed_seconds=time.time() - start_time
            )
