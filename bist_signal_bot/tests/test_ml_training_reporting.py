import pytest
from bist_signal_bot.ml.training.reporting import format_ml_train_text, format_ml_train_markdown
from bist_signal_bot.ml.training.models import MLTrainResult, MLTrainConfig, MLTrainStatus, MLModelType, MLTaskType, MLClassificationMetrics

def test_reporting_formats():
    config = MLTrainConfig(
        model_type=MLModelType.RANDOM_FOREST_CLASSIFIER,
        task_type=MLTaskType.CLASSIFICATION,
        target_col="label_1"
    )
    metrics = MLClassificationMetrics(accuracy=0.9, f1=0.85, roc_auc=0.95)

    import datetime
    res = MLTrainResult(
        status=MLTrainStatus.SUCCESS,
        config=config,
        classification_metrics=metrics,
        prepared_data_summary={"train_rows": 100, "test_rows": 20},
        started_at=datetime.datetime.now(datetime.timezone.utc),
        finished_at=datetime.datetime.now(datetime.timezone.utc),
        disclaimer="Test Disclaimer"
    )

    txt = format_ml_train_text(res)
    assert "Accuracy: 0.9000" in txt
    assert "Test Disclaimer" in txt

    md = format_ml_train_markdown(res)
    assert "**Accuracy:** 0.9000" in md
