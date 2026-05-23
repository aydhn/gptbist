import pytest
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.deployment.storage import DeploymentStore
from bist_signal_bot.deployment.models import DeploymentProfileType, FirstRunResult, DeploymentStatus, DeploymentProfile, SmokeTestResult, OperatorRunbook
from bist_signal_bot.deployment.profiles import DeploymentProfileManager
import uuid
from datetime import datetime, UTC

def test_deployment_storage_first_run(tmp_path):
    settings = Settings()
    store = DeploymentStore(settings, tmp_path)
    profile = DeploymentProfileManager().get_profile(DeploymentProfileType.RESEARCH_ONLY)

    first_run = FirstRunResult(
        first_run_id=str(uuid.uuid4()),
        profile=profile,
        started_at=datetime.now(UTC),
        status=DeploymentStatus.PASS
    )

    paths = store.save_first_run_result(first_run)
    assert paths["first_run_json"].exists()
    assert paths["latest_json"].exists()

    loaded = store.load_latest_first_run_result()
    assert loaded is not None
    assert loaded.first_run_id == first_run.first_run_id

    recent = store.list_recent_first_runs()
    assert len(recent) == 1

def test_deployment_storage_smoke(tmp_path):
    settings = Settings()
    store = DeploymentStore(settings, tmp_path)

    smoke = SmokeTestResult(
        smoke_id=str(uuid.uuid4()),
        started_at=datetime.now(UTC),
        status=DeploymentStatus.PASS
    )

    paths = store.save_smoke_result(smoke)
    assert paths["smoke_json"].exists()
    assert paths["latest_json"].exists()

    loaded = store.load_latest_smoke_result()
    assert loaded is not None
    assert loaded.smoke_id == smoke.smoke_id

def test_deployment_storage_runbook(tmp_path):
    settings = Settings()
    store = DeploymentStore(settings, tmp_path)

    runbook = OperatorRunbook(
        runbook_id=str(uuid.uuid4()),
        profile_type=DeploymentProfileType.RESEARCH_ONLY,
        created_at=datetime.now(UTC),
        title="Test"
    )

    paths = store.save_runbook(runbook, "# Markdown content")
    assert paths["markdown"].exists()
    assert paths["json"].exists()

def test_deployment_storage_profiles(tmp_path):
    settings = Settings()
    store = DeploymentStore(settings, tmp_path)
    manager = DeploymentProfileManager()
    profiles = manager.default_profiles()

    path = store.save_profiles(profiles)
    assert path.exists()

    loaded = store.load_profiles()
    assert len(loaded) == len(profiles)
