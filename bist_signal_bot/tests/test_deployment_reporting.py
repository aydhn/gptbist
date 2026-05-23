import pytest
from bist_signal_bot.deployment.reporting import format_first_run_text, format_operator_runbook_markdown, format_deployment_report_markdown
from bist_signal_bot.deployment.models import DeploymentProfileType, FirstRunResult, DeploymentStatus, OperatorRunbook
from bist_signal_bot.deployment.profiles import DeploymentProfileManager
import uuid
from datetime import datetime, UTC

def test_deployment_reporting_first_run():
    profile = DeploymentProfileManager().get_profile(DeploymentProfileType.RESEARCH_ONLY)
    first_run = FirstRunResult(
        first_run_id=str(uuid.uuid4()),
        profile=profile,
        started_at=datetime.now(UTC),
        status=DeploymentStatus.PASS
    )

    text = format_first_run_text(first_run)
    assert "First Run Wizard Report" in text
    assert "RESEARCH_ONLY" in text

def test_deployment_reporting_runbook():
    runbook = OperatorRunbook(
        runbook_id=str(uuid.uuid4()),
        profile_type=DeploymentProfileType.RESEARCH_ONLY,
        created_at=datetime.now(UTC),
        title="Test Title",
        sections=[{"title": "Sec", "content": "Cont"}]
    )

    md = format_operator_runbook_markdown(runbook)
    assert "# Test Title" in md
    assert "## Sec" in md
    assert "Cont" in md

def test_deployment_reporting_markdown():
    profile = DeploymentProfileManager().get_profile(DeploymentProfileType.RESEARCH_ONLY)
    first_run = FirstRunResult(
        first_run_id=str(uuid.uuid4()),
        profile=profile,
        started_at=datetime.now(UTC),
        status=DeploymentStatus.PASS
    )
    md = format_deployment_report_markdown(first_run)
    assert "# Deployment Report" in md
    assert "First Run Wizard Report" in md
    assert "No real order was sent." in md
