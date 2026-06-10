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

def test_validation_summary_to_dict_basic():
    from bist_signal_bot.model_registry.models import ModelValidationSummary, ModelGovernanceStatus
    from bist_signal_bot.model_registry.reporting import validation_summary_to_dict

    summary = ModelValidationSummary(
        validation_id="val-123",
        model_id="m1",
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        validation_method="cross-val",
        status=ModelGovernanceStatus.PASS,
        leakage_status=ModelGovernanceStatus.PASS,
        feature_quality_score=0.95,
        metrics={"accuracy": 0.99, "f1": 0.98}
    )

    result = validation_summary_to_dict(summary)
    assert result == {
        "validation_id": "val-123",
        "model_id": "m1",
        "method": "cross-val",
        "status": "PASS",
        "leakage_status": "PASS",
        "feature_quality": 0.95,
        "metrics": {"accuracy": 0.99, "f1": 0.98}
    }

def test_validation_summary_to_dict_missing_optionals():
    from bist_signal_bot.model_registry.models import ModelValidationSummary, ModelGovernanceStatus
    from bist_signal_bot.model_registry.reporting import validation_summary_to_dict

    summary = ModelValidationSummary(
        validation_id="val-124",
        model_id="m2",
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        validation_method="train-test-split",
        status=ModelGovernanceStatus.FAIL,
        leakage_status=ModelGovernanceStatus.FAIL
    )

    result = validation_summary_to_dict(summary)
    assert result == {
        "validation_id": "val-124",
        "model_id": "m2",
        "method": "train-test-split",
        "status": "FAIL",
        "leakage_status": "FAIL",
        "feature_quality": None,
        "metrics": {}
    }

def test_model_card_to_dict_basic():
    from bist_signal_bot.model_registry.models import ModelCard, ModelGovernanceStatus
    from bist_signal_bot.model_registry.reporting import model_card_to_dict
    from datetime import datetime, timezone

    card = ModelCard(
        card_id="card-123",
        model_id="m1",
        model_name="my_model",
        version="v1.0",
        governance_status=ModelGovernanceStatus.PASS,
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        intended_use="Testing",
        not_intended_use="Not for real order execution or investment advice",
        input_features=["f1", "f2"],
        training_data_summary="test data",
        validation_summary="looks good",
        calibration_summary="calibrated"
    )

    result = model_card_to_dict(card)

    assert result == {
        "card_id": "card-123",
        "model_id": "m1",
        "model_name": "my_model",
        "version": "v1.0",
        "governance_status": "PASS",
        "created_at": "2023-01-01T12:00:00+00:00"
    }

def test_model_card_to_dict_full():
    from bist_signal_bot.model_registry.models import ModelCard, ModelGovernanceStatus
    from bist_signal_bot.model_registry.reporting import model_card_to_dict
    from datetime import datetime, timezone

    card = ModelCard(
        card_id="card-full",
        model_id="m-full",
        model_name="my_full_model",
        version="v1.1",
        governance_status=ModelGovernanceStatus.FAIL,
        created_at=datetime(2023, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
        intended_use="Testing full fields",
        not_intended_use="not for real order execution or investment advice",
        input_features=["f1", "f2", "f3"],
        training_data_summary="full test data",
        validation_summary="failed validation",
        calibration_summary="uncalibrated",
        known_limitations=["Limit 1", "Limit 2"],
        risk_notes=["Risk 1"],
        supported_explanation_methods=["shap", "lime"],
        top_feature_importance={"f1": 0.8, "f2": 0.2},
        explanation_caveats=["Caveat 1"],
        unsupported_method_warnings=["Warning 1"]
    )

    result = model_card_to_dict(card)

    assert result == {
        "card_id": "card-full",
        "model_id": "m-full",
        "model_name": "my_full_model",
        "version": "v1.1",
        "governance_status": "FAIL",
        "created_at": "2023-01-02T12:00:00+00:00"
    }

def test_format_model_card_markdown():
    from bist_signal_bot.model_registry.models import ModelCard, ModelGovernanceStatus
    from bist_signal_bot.model_registry.reporting import format_model_card_markdown
    from datetime import datetime, timezone

    card = ModelCard(
        card_id="card-123",
        model_id="model-456",
        model_name="Test Model",
        version="1.0",
        created_at=datetime(2023, 5, 1, tzinfo=timezone.utc),
        intended_use="Test intended use",
        not_intended_use="This is not intended for real order execution or investment advice",
        input_features=["feat1", "feat2"],
        training_data_summary="Trained on random data",
        validation_summary="Passed validation",
        calibration_summary="Well calibrated",
        known_limitations=["limitation 1", "limitation 2"],
        risk_notes=["risk 1"],
        governance_status=ModelGovernanceStatus.PASS,
        supported_explanation_methods=["SHAP"],
        top_feature_importance={"feat1": 0.8, "feat2": 0.2},
        explanation_caveats=["Caveat 1"],
        unsupported_method_warnings=["Warning 1"]
    )

    markdown = format_model_card_markdown(card)

    assert "Model Card: Test Model" in markdown
    assert "card-123" in markdown
    assert "model-456" in markdown
    assert "1.0" in markdown
    assert "Test intended use" in markdown
    assert "This is not intended for real order execution or investment advice" in markdown
    assert "feat1" in markdown
    assert "feat2" in markdown
    assert "Trained on random data" in markdown
    assert "Passed validation" in markdown
    assert "Well calibrated" in markdown
    assert "limitation 1" in markdown
    assert "risk 1" in markdown
    assert "PASS" in markdown

def test_lineage_edge_to_dict():
    from bist_signal_bot.model_registry.models import ModelLineageEdge
    from bist_signal_bot.model_registry.reporting import lineage_edge_to_dict
    from datetime import datetime, timezone

    edge = ModelLineageEdge(
        edge_id="edge_123",
        from_object_id="obj_1",
        to_object_id="obj_2",
        relation="DERIVES_FROM",
        process_name="training_job",
        created_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        warnings=["warning 1"],
        metadata={"key": "value"}
    )

    result = lineage_edge_to_dict(edge)

    assert result == {
        "edge_id": "edge_123",
        "from": "obj_1",
        "to": "obj_2",
        "relation": "DERIVES_FROM",
        "process": "training_job"
    }

def test_lineage_edge_to_dict_no_process():
    from bist_signal_bot.model_registry.models import ModelLineageEdge
    from bist_signal_bot.model_registry.reporting import lineage_edge_to_dict
    from datetime import datetime, timezone

    edge = ModelLineageEdge(
        edge_id="edge_456",
        from_object_id="obj_A",
        to_object_id="obj_B",
        relation="USES",
        created_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
    )

    result = lineage_edge_to_dict(edge)

    assert result == {
        "edge_id": "edge_456",
        "from": "obj_A",
        "to": "obj_B",
        "relation": "USES",
        "process": None
    }

def test_artifact_to_dict_basic():
    from bist_signal_bot.model_registry.models import ModelArtifact, ModelArtifactFormat
    from bist_signal_bot.model_registry.reporting import artifact_to_dict
    from datetime import datetime, timezone

    artifact = ModelArtifact(
        artifact_id="art-123",
        model_id="m1",
        path="/path/to/model.pkl",
        artifact_format=ModelArtifactFormat.PICKLE,
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        size_bytes=1024,
        loadable=True
    )

    result = artifact_to_dict(artifact)

    assert result == {
        "artifact_id": "art-123",
        "model_id": "m1",
        "path": "/path/to/model.pkl",
        "format": "PICKLE",
        "created_at": "2023-01-01T12:00:00+00:00",
        "size_bytes": 1024,
        "loadable": True
    }

def test_artifact_to_dict_missing_optionals():
    from bist_signal_bot.model_registry.models import ModelArtifact, ModelArtifactFormat
    from bist_signal_bot.model_registry.reporting import artifact_to_dict
    from datetime import datetime, timezone

    artifact = ModelArtifact(
        artifact_id="art-124",
        path="/path/to/model.json",
        artifact_format=ModelArtifactFormat.JSON,
        created_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    )

    result = artifact_to_dict(artifact)

    assert result == {
        "artifact_id": "art-124",
        "model_id": None,
        "path": "/path/to/model.json",
        "format": "JSON",
        "created_at": "2023-01-01T12:00:00+00:00",
        "size_bytes": None,
        "loadable": None
    }

def test_format_experiment_run_text_finished_with_metrics():
    from bist_signal_bot.model_registry.models import ExperimentRun, ExperimentStatus, ModelKind
    from bist_signal_bot.model_registry.reporting import format_experiment_run_text
    from datetime import datetime, timezone

    run = ExperimentRun(
        run_id="run-123",
        experiment_name="test_exp",
        model_name="test_model",
        model_kind=ModelKind.CLASSIFIER,
        status=ExperimentStatus.COMPLETED,
        started_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        finished_at=datetime(2023, 1, 1, 12, 0, 5, tzinfo=timezone.utc),
        metrics={"accuracy": 0.95, "f1": 0.90}
    )

    result = format_experiment_run_text(run)
    assert "Experiment: test_exp | Model: test_model" in result
    assert "Run ID: run-123" in result
    assert "Status: COMPLETED" in result
    assert "Duration: 5.0s" in result
    assert "Metrics:" in result
    assert "  accuracy: 0.9500" in result
    assert "  f1: 0.9000" in result

def test_format_experiment_run_text_running_no_metrics():
    from bist_signal_bot.model_registry.models import ExperimentRun, ExperimentStatus, ModelKind
    from bist_signal_bot.model_registry.reporting import format_experiment_run_text
    from datetime import datetime, timezone

    run = ExperimentRun(
        run_id="run-124",
        experiment_name="test_exp_2",
        model_name="test_model_2",
        model_kind=ModelKind.REGRESSOR,
        status=ExperimentStatus.RUNNING,
        started_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    )

    result = format_experiment_run_text(run)
    assert "Experiment: test_exp_2 | Model: test_model_2" in result
    assert "Run ID: run-124" in result
    assert "Status: RUNNING" in result
    assert "Duration: Runnings" in result
    assert "Metrics:" not in result

def test_promotion_request_to_dict():
    from bist_signal_bot.model_registry.models import ModelPromotionRequest, ModelPromotionStage, ModelGovernanceStatus
    from bist_signal_bot.model_registry.reporting import promotion_request_to_dict
    from datetime import datetime, timezone

    request = ModelPromotionRequest(
        promotion_id="promo-123",
        model_id="m1",
        requested_stage=ModelPromotionStage.ACTIVE_RESEARCH,
        current_stage=ModelPromotionStage.STAGING,
        requested_at=datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        requested_by="analyst_1",
        reason="Good performance in staging",
        validation_status=ModelGovernanceStatus.PASS,
        calibration_status=ModelGovernanceStatus.PASS,
        leakage_status=ModelGovernanceStatus.PASS,
        governance_decision=ModelGovernanceStatus.PASS,
        approved=True,
        warnings=[],
        disclaimer="Model promotion is research registry metadata only. It is not live deployment approval or permission to trade. No real order was sent."
    )

    result = promotion_request_to_dict(request)

    assert result == {
        "promotion_id": "promo-123",
        "model_id": "m1",
        "requested_stage": "ACTIVE_RESEARCH",
        "current_stage": "STAGING",
        "approved": True,
        "reason": "Good performance in staging",
        "governance_decision": "PASS"
    }

def test_calibration_summary_to_dict():
    from bist_signal_bot.model_registry.models import ModelCalibrationSummary, ModelGovernanceStatus
    from bist_signal_bot.model_registry.reporting import calibration_summary_to_dict
    from datetime import datetime, timezone

    summary = ModelCalibrationSummary(
        calibration_id="calib-1",
        model_id="mod-1",
        created_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        calibration_method="platt",
        status=ModelGovernanceStatus.PASS,
        reliability_score=0.95,
        expected_calibration_error=0.05
    )
    res = calibration_summary_to_dict(summary)
    assert res == {
        "calibration_id": "calib-1",
        "model_id": "mod-1",
        "method": "platt",
        "status": "PASS",
        "reliability_score": 0.95,
        "ece": 0.05
    }

def test_calibration_summary_to_dict_nulls():
    from bist_signal_bot.model_registry.models import ModelCalibrationSummary, ModelGovernanceStatus
    from bist_signal_bot.model_registry.reporting import calibration_summary_to_dict
    from datetime import datetime, timezone

    summary = ModelCalibrationSummary(
        calibration_id="calib-2",
        model_id="mod-2",
        created_at=datetime(2023, 1, 1, tzinfo=timezone.utc),
        calibration_method="isotonic",
        status=ModelGovernanceStatus.FAIL,
        reliability_score=None,
        expected_calibration_error=None
    )
    res = calibration_summary_to_dict(summary)
    assert res == {
        "calibration_id": "calib-2",
        "model_id": "mod-2",
        "method": "isotonic",
        "status": "FAIL",
        "reliability_score": None,
        "ece": None
    }

def test_drift_finding_to_dict():
    from bist_signal_bot.model_registry.models import ModelDriftFinding, ModelDriftType, ModelGovernanceStatus
    from bist_signal_bot.model_registry.reporting import drift_finding_to_dict

    finding = ModelDriftFinding(
        drift_id="drift-123",
        model_id="mod-1",
        drift_type=ModelDriftType.FEATURE_DRIFT,
        baseline_window="2023-01",
        current_window="2023-02",
        baseline_value=0.5,
        current_value=0.8,
        drift_score=0.9,
        status=ModelGovernanceStatus.FAIL,
        message="Significant data drift detected"
    )

    result = drift_finding_to_dict(finding)

    assert result == {
        "drift_id": "drift-123",
        "model_id": "mod-1",
        "drift_type": "FEATURE_DRIFT",
        "score": 0.9,
        "status": "FAIL",
        "message": "Significant data drift detected"
    }

def test_drift_finding_to_dict_null_score():
    from bist_signal_bot.model_registry.models import ModelDriftFinding, ModelDriftType, ModelGovernanceStatus
    from bist_signal_bot.model_registry.reporting import drift_finding_to_dict

    finding = ModelDriftFinding(
        drift_id="drift-124",
        model_id="mod-2",
        drift_type=ModelDriftType.PERFORMANCE_DECAY,
        baseline_window="2023-01",
        current_window="2023-02",
        baseline_value=0.5,
        current_value=0.8,
        drift_score=None,
        status=ModelGovernanceStatus.PASS,
        message="No significant decay detected"
    )

    result = drift_finding_to_dict(finding)

    assert result == {
        "drift_id": "drift-124",
        "model_id": "mod-2",
        "drift_type": "PERFORMANCE_DECAY",
        "score": None,
        "status": "PASS",
        "message": "No significant decay detected"
    }
