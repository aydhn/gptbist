import pytest
from datetime import datetime, timezone
from bist_signal_bot.data_catalog.gates import DataQualityGateEngine
from bist_signal_bot.data_catalog.models import (
    DataQualityAssessment, DataQualityStatus, DataQualityFinding, SchemaDriftFinding, SchemaDriftType
)
from bist_signal_bot.config.settings import Settings

def test_data_quality_gate_blocks_on_fail():
    settings = Settings()
    engine = DataQualityGateEngine(settings)

    assessment = DataQualityAssessment(
        assessment_id="1",
        dataset_id="ds1",
        created_at=datetime.now(timezone.utc),
        quality_score=30.0,
        status=DataQualityStatus.FAIL,
        findings=[
             DataQualityFinding(
                 finding_id="1",
                 dataset_id="ds1",
                 rule_name="required_columns",
                 status=DataQualityStatus.FAIL,
                 severity="HIGH",
                 message="Missing column"
             )
        ]
    )

    result = engine.run_gate(assessment=assessment)
    assert result.status == DataQualityStatus.BLOCKED
    assert len(result.blocking_findings) > 0

def test_data_quality_gate_blocks_on_drift():
    settings = Settings()
    engine = DataQualityGateEngine(settings)

    assessment = DataQualityAssessment(
        assessment_id="1",
        dataset_id="ds1",
        created_at=datetime.now(timezone.utc),
        quality_score=90.0,
        status=DataQualityStatus.PASS
    )

    drift = [
        SchemaDriftFinding(
            drift_id="1",
            dataset_id="ds1",
            drift_type=SchemaDriftType.MISSING_COLUMN,
            severity="HIGH",
            message="Required column missing"
        )
    ]

    result = engine.run_gate(assessment=assessment, drift_findings=drift)
    assert result.status == DataQualityStatus.BLOCKED
    assert len(result.blocking_findings) > 0
