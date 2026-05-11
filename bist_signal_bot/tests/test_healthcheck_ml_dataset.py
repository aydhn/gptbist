import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.app.healthcheck import check_ml_dataset

def test_healthcheck_ml_fields():
    settings = Settings()
    res = check_ml_dataset(settings)

    assert "enabled" in res
    assert "default_task_type" in res
    assert "dataset_builder_instantiable" in res
    assert "label_builder_capable" in res
    assert "leakage_guard_capable" in res
    assert "mock_tiny_dataset_build_capable" in res
