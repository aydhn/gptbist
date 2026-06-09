import pytest
from datetime import datetime, timezone
from bist_signal_bot.model_registry.models import ModelRecord, ModelKind, ModelRegistryStatus, ModelGovernanceAssessment, ModelGovernanceStatus
from bist_signal_bot.model_registry.reporting import format_model_record_text, governance_assessment_to_dict

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

def test_governance_assessment_to_dict_basic():
    assessment = ModelGovernanceAssessment(
        assessment_id="test_assessment_1",
        model_id="test_model_1",
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        status=ModelGovernanceStatus.FAIL,
        blocking_reasons=["Reason 1", "Reason 2"]
    )
    result = governance_assessment_to_dict(assessment)
    expected = {
        "assessment_id": "test_assessment_1",
        "model_id": "test_model_1",
        "status": "FAIL",
        "blocking_reasons": ["Reason 1", "Reason 2"],
        "created_at": "2023-01-01T12:00:00+00:00"
    }
    assert result == expected

def test_governance_assessment_to_dict_no_blocking_reasons():
    assessment = ModelGovernanceAssessment(
        assessment_id="test_assessment_2",
        model_id="test_model_2",
        created_at=datetime(2023, 2, 1, 12, 0, 0, tzinfo=timezone.utc),
        status=ModelGovernanceStatus.PASS,
        blocking_reasons=[]
    )
    result = governance_assessment_to_dict(assessment)
    expected = {
        "assessment_id": "test_assessment_2",
        "model_id": "test_model_2",
        "status": "PASS",
        "blocking_reasons": [],
        "created_at": "2023-02-01T12:00:00+00:00"
    }
    assert result == expected

def test_model_registry_report_to_dict():
    from bist_signal_bot.model_registry.models import ModelRegistryReport, ModelRecord, ExperimentRun, ModelArtifact, ModelCard, ModelDriftFinding, ExperimentStatus, ModelDriftType, ModelGovernanceStatus, ModelArtifactFormat

    report = ModelRegistryReport(
        report_id="report-123",
        generated_at=datetime(2023, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
        models=[ModelRecord(model_id="m1", model_name="m", model_kind=ModelKind.CLASSIFIER, version="1.0", status=ModelRegistryStatus.ACTIVE_RESEARCH, created_at=datetime.now())],
        experiments=[ExperimentRun(run_id="e1", experiment_name="e", model_name="m", model_kind=ModelKind.CLASSIFIER, status=ExperimentStatus.COMPLETED, started_at=datetime.now())],
        artifacts=[ModelArtifact(artifact_id="a1", model_id="m1", path="path", artifact_format=ModelArtifactFormat.PICKLE, created_at=datetime.now())],
        cards=[ModelCard(card_id="c1", model_id="m1", model_name="m", version="1.0", created_at=datetime.now(), intended_use="test", not_intended_use="not for real order execution or investment advice", input_features=["f1"], training_data_summary="test", validation_summary="test", calibration_summary="test", governance_status=ModelGovernanceStatus.PASS)],
        drift_findings=[ModelDriftFinding(drift_id="d1", model_id="m1", drift_type=ModelDriftType.FEATURE_DRIFT, baseline_window="w1", current_window="w2", status=ModelGovernanceStatus.PASS, message="msg")],
        key_findings=["Finding 1", "Finding 2"]
    )

    from bist_signal_bot.model_registry.reporting import model_registry_report_to_dict
    result = model_registry_report_to_dict(report)

    assert result == {
        "report_id": "report-123",
        "generated_at": "2023-05-01T10:00:00+00:00",
        "models_count": 1,
        "experiments_count": 1,
        "artifacts_count": 1,
        "cards_count": 1,
        "drift_findings": 1,
        "key_findings": ["Finding 1", "Finding 2"]
    }

def test_model_registry_report_to_dict_empty():
    from bist_signal_bot.model_registry.models import ModelRegistryReport

    report = ModelRegistryReport(
        report_id="report-empty",
        generated_at=datetime(2023, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    )

    from bist_signal_bot.model_registry.reporting import model_registry_report_to_dict
    result = model_registry_report_to_dict(report)

    assert result == {
        "report_id": "report-empty",
        "generated_at": "2023-06-01T12:00:00+00:00",
        "models_count": 0,
        "experiments_count": 0,
        "artifacts_count": 0,
        "cards_count": 0,
        "drift_findings": 0,
        "key_findings": []
    }
