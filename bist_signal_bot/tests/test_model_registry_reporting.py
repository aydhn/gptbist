import pytest
from datetime import datetime, timezone
from bist_signal_bot.model_registry.models import ModelRecord, ModelKind, ModelRegistryStatus
from bist_signal_bot.model_registry.reporting import format_model_record_text

def test_format_model_record_text_basic():
    model = ModelRecord(
        model_id="test_model_1",
        model_name="my_model",
        model_kind=ModelKind.CLASSIFIER,
        version="1.0.0",
        status=ModelRegistryStatus.ACTIVE_RESEARCH,
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    result = format_model_record_text(model)
    expected = (
        "Model: my_model (v1.0.0)\n"
        "ID: test_model_1\n"
        "Kind: CLASSIFIER\n"
        "Status: ACTIVE_RESEARCH\n"
        "Created: 2023-01-01T12:00:00+00:00\n"
        "Disclaimer: Model record is local research metadata only. It is not investment advice or permission to trade. No real order was sent."
    )
    assert result == expected

def test_format_model_record_text_with_feature_version():
    model = ModelRecord(
        model_id="test_model_2",
        model_name="my_model_2",
        model_kind=ModelKind.CLASSIFIER,
        version="1.0.1",
        status=ModelRegistryStatus.ARCHIVED,
        created_at=datetime(2023, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
        feature_set_version="v2.5"
    )
    result = format_model_record_text(model)
    expected = (
        "Model: my_model_2 (v1.0.1)\n"
        "ID: test_model_2\n"
        "Kind: CLASSIFIER\n"
        "Status: ARCHIVED\n"
        "Created: 2023-02-01T12:00:00+00:00\n"
        "Feature Version: v2.5\n"
        "Disclaimer: Model record is local research metadata only. It is not investment advice or permission to trade. No real order was sent."
    )
    assert result == expected

def test_format_model_record_text_with_warnings():
    model = ModelRecord(
        model_id="test_model_3",
        model_name="my_model_3",
        model_kind=ModelKind.CLASSIFIER,
        version="2.0",
        status=ModelRegistryStatus.ACTIVE_RESEARCH,
        created_at=datetime(2023, 3, 1, 12, 0, 0, tzinfo=timezone.utc),
        warnings=["Low accuracy", "Data drift detected"]
    )
    result = format_model_record_text(model)
    expected = (
        "Model: my_model_3 (v2.0)\n"
        "ID: test_model_3\n"
        "Kind: CLASSIFIER\n"
        "Status: ACTIVE_RESEARCH\n"
        "Created: 2023-03-01T12:00:00+00:00\n"
        "Warnings:\n"
        "  - Low accuracy\n"
        "  - Data drift detected\n"
        "Disclaimer: Model record is local research metadata only. It is not investment advice or permission to trade. No real order was sent."
    )
    assert result == expected

def test_format_model_record_text_with_both():
    model = ModelRecord(
        model_id="test_model_4",
        model_name="my_model_4",
        model_kind=ModelKind.CLASSIFIER,
        version="2.1",
        status=ModelRegistryStatus.ACTIVE_RESEARCH,
        created_at=datetime(2023, 4, 1, 12, 0, 0, tzinfo=timezone.utc),
        feature_set_version="v3.0",
        warnings=["Some warning"]
    )
    result = format_model_record_text(model)
    expected = (
        "Model: my_model_4 (v2.1)\n"
        "ID: test_model_4\n"
        "Kind: CLASSIFIER\n"
        "Status: ACTIVE_RESEARCH\n"
        "Created: 2023-04-01T12:00:00+00:00\n"
        "Feature Version: v3.0\n"
        "Warnings:\n"
        "  - Some warning\n"
        "Disclaimer: Model record is local research metadata only. It is not investment advice or permission to trade. No real order was sent."
    )
    assert result == expected
