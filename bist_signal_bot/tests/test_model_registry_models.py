import pytest
from datetime import datetime, timezone
from bist_signal_bot.model_registry.models import (
    ModelRecord, ModelKind, ModelRegistryStatus, ModelArtifact, ModelArtifactFormat,
    ModelCard, ModelGovernanceStatus
)

def test_model_record_validation():
    # Empty model name
    with pytest.raises(ValueError, match="model_name cannot be empty"):
        ModelRecord(
            model_id="m1",
            model_name="",
            model_kind=ModelKind.CLASSIFIER,
            version="1.0",
            created_at=datetime.now(timezone.utc),
            status=ModelRegistryStatus.STAGING
        )

    # Missing version
    with pytest.raises(ValueError, match="version cannot be empty"):
        ModelRecord(
            model_id="m1",
            model_name="model1",
            model_kind=ModelKind.CLASSIFIER,
            version="",
            created_at=datetime.now(timezone.utc),
            status=ModelRegistryStatus.STAGING
        )

    # Secret in dataset refs
    with pytest.raises(ValueError, match="dataset_refs must not contain secrets"):
        ModelRecord(
            model_id="m1",
            model_name="model1",
            model_kind=ModelKind.CLASSIFIER,
            version="1.0",
            created_at=datetime.now(timezone.utc),
            status=ModelRegistryStatus.STAGING,
            dataset_refs=["some_token_123"]
        )

def test_model_artifact_validation():
    # Empty checksum
    with pytest.raises(ValueError, match="checksum cannot be empty string if provided"):
        ModelArtifact(
            artifact_id="a1",
            path="/tmp/model.pkl",
            artifact_format=ModelArtifactFormat.PICKLE,
            created_at=datetime.now(timezone.utc),
            checksum=""
        )

    # Secret in path
    with pytest.raises(ValueError, match="artifact path must not contain secrets"):
        ModelArtifact(
            artifact_id="a1",
            path="/tmp/my_secret_model.pkl",
            artifact_format=ModelArtifactFormat.PICKLE,
            created_at=datetime.now(timezone.utc),
            checksum="hash123"
        )

def test_model_card_validation():
    # Missing explicit forbidding in not_intended_use
    with pytest.raises(ValueError, match="not_intended_use must state that 'real order execution' and 'investment advice'"):
        ModelCard(
            card_id="c1",
            model_id="m1",
            model_name="m1",
            version="1.0",
            created_at=datetime.now(timezone.utc),
            intended_use="research",
            not_intended_use="don't use it badly",
            input_features=["f1"],
            training_data_summary="data",
            validation_summary="ok",
            calibration_summary="ok",
            governance_status=ModelGovernanceStatus.PASS
        )
