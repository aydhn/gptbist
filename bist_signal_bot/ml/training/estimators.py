from typing import Any
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from sklearn.dummy import DummyClassifier, DummyRegressor

from bist_signal_bot.ml.training.models import MLTrainConfig, MLModelType, MLTaskType
from bist_signal_bot.core.exceptions import MLEstimatorError, MLTrainingValidationError

class EstimatorFactory:
    def create_estimator(self, config: MLTrainConfig) -> Any:
        self.validate_model_task_compatibility(config.model_type, config.task_type)

        random_state = config.random_seed
        params = config.model_params or {}

        if config.model_type == MLModelType.DUMMY_CLASSIFIER:
            strategy = params.get("strategy", "prior")
            return DummyClassifier(strategy=strategy, random_state=random_state)

        elif config.model_type == MLModelType.LOGISTIC_REGRESSION:
            max_iter = params.get("max_iter", 1000)
            class_weight = config.class_weight or params.get("class_weight", None)
            return LogisticRegression(max_iter=max_iter, class_weight=class_weight, random_state=random_state, n_jobs=-1 if params.get("n_jobs") != 1 else 1)

        elif config.model_type == MLModelType.RANDOM_FOREST_CLASSIFIER:
            n_estimators = params.get("n_estimators", 100)
            max_depth = params.get("max_depth", None)
            min_samples_leaf = params.get("min_samples_leaf", 1)
            class_weight = config.class_weight or params.get("class_weight", None)
            return RandomForestClassifier(
                n_estimators=n_estimators, max_depth=max_depth, min_samples_leaf=min_samples_leaf,
                class_weight=class_weight, random_state=random_state, n_jobs=-1 if params.get("n_jobs") != 1 else 1
            )

        elif config.model_type == MLModelType.GRADIENT_BOOSTING_CLASSIFIER:
            n_estimators = params.get("n_estimators", 100)
            max_depth = params.get("max_depth", 3)
            learning_rate = params.get("learning_rate", 0.1)
            return GradientBoostingClassifier(
                n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, random_state=random_state
            )

        elif config.model_type == MLModelType.EXTRA_TREES_CLASSIFIER:
            n_estimators = params.get("n_estimators", 100)
            class_weight = config.class_weight or params.get("class_weight", None)
            return ExtraTreesClassifier(
                n_estimators=n_estimators, class_weight=class_weight, random_state=random_state, n_jobs=-1 if params.get("n_jobs") != 1 else 1
            )

        elif config.model_type == MLModelType.DUMMY_REGRESSOR:
            strategy = params.get("strategy", "mean")
            return DummyRegressor(strategy=strategy)

        elif config.model_type == MLModelType.RIDGE_REGRESSION:
            alpha = params.get("alpha", 1.0)
            return Ridge(alpha=alpha, random_state=random_state)

        elif config.model_type == MLModelType.RANDOM_FOREST_REGRESSOR:
            n_estimators = params.get("n_estimators", 100)
            max_depth = params.get("max_depth", None)
            return RandomForestRegressor(
                n_estimators=n_estimators, max_depth=max_depth, random_state=random_state, n_jobs=-1 if params.get("n_jobs") != 1 else 1
            )

        elif config.model_type == MLModelType.GRADIENT_BOOSTING_REGRESSOR:
            n_estimators = params.get("n_estimators", 100)
            max_depth = params.get("max_depth", 3)
            learning_rate = params.get("learning_rate", 0.1)
            return GradientBoostingRegressor(
                n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, random_state=random_state
            )

        elif config.model_type == MLModelType.EXTRA_TREES_REGRESSOR:
            n_estimators = params.get("n_estimators", 100)
            return ExtraTreesRegressor(
                n_estimators=n_estimators, random_state=random_state, n_jobs=-1 if params.get("n_jobs") != 1 else 1
            )

        raise MLEstimatorError(f"Unsupported model type: {config.model_type}")

    def validate_model_task_compatibility(self, model_type: MLModelType, task_type: MLTaskType) -> None:
        if task_type == MLTaskType.CLASSIFICATION:
            if "REGRESSOR" in model_type.value or "REGRESSION" in model_type.value and "LOGISTIC" not in model_type.value:
                raise MLTrainingValidationError(f"Model type {model_type} not compatible with task {task_type}")
        elif task_type == MLTaskType.REGRESSION:
            if "CLASSIFIER" in model_type.value or "LOGISTIC" in model_type.value:
                raise MLTrainingValidationError(f"Model type {model_type} not compatible with task {task_type}")

    def default_model_for_task(self, task_type: MLTaskType) -> MLModelType:
        if task_type == MLTaskType.CLASSIFICATION:
            return MLModelType.RANDOM_FOREST_CLASSIFIER
        elif task_type == MLTaskType.REGRESSION:
            return MLModelType.RANDOM_FOREST_REGRESSOR
        return MLModelType.RANDOM_FOREST_CLASSIFIER
