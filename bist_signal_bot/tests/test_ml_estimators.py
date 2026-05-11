import pytest
from bist_signal_bot.ml.training.estimators import EstimatorFactory
from bist_signal_bot.ml.training.models import MLTrainConfig, MLModelType, MLTaskType

def test_estimator_factory_classification():
    factory = EstimatorFactory()

    config = MLTrainConfig(
        model_type=MLModelType.RANDOM_FOREST_CLASSIFIER,
        task_type=MLTaskType.CLASSIFICATION,
        target_col="label"
    )
    est = factory.create_estimator(config)
    assert type(est).__name__ == "RandomForestClassifier"

    config.model_type = MLModelType.LOGISTIC_REGRESSION
    est = factory.create_estimator(config)
    assert type(est).__name__ == "LogisticRegression"

def test_estimator_factory_regression():
    factory = EstimatorFactory()

    config = MLTrainConfig(
        model_type=MLModelType.RANDOM_FOREST_REGRESSOR,
        task_type=MLTaskType.REGRESSION,
        target_col="label"
    )
    est = factory.create_estimator(config)
    assert type(est).__name__ == "RandomForestRegressor"

def test_estimator_factory_incompatible():
    factory = EstimatorFactory()
    config = MLTrainConfig(
        model_type=MLModelType.RANDOM_FOREST_REGRESSOR,
        task_type=MLTaskType.CLASSIFICATION,
        target_col="label"
    )
    with pytest.raises(Exception):
        factory.create_estimator(config)
