import pytest
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.deployment.runbook import OperatorRunbookBuilder
from bist_signal_bot.deployment.models import DeploymentProfileType
from bist_signal_bot.deployment.profiles import DeploymentProfileManager

def test_operator_runbook_builder():
    settings = Settings()
    builder = OperatorRunbookBuilder(settings)
    profile = DeploymentProfileManager().get_profile(DeploymentProfileType.RESEARCH_ONLY)

    runbook = builder.build_runbook(profile)
    assert len(runbook.sections) == 12
    assert "RESEARCH_ONLY" in runbook.title

    md = builder.render_markdown(runbook)
    assert "# Operator Runbook - RESEARCH_ONLY" in md
    assert "No real order was sent." in md

def test_operator_runbook_write(tmp_path):
    settings = Settings()
    builder = OperatorRunbookBuilder(settings)
    profile = DeploymentProfileManager().get_profile(DeploymentProfileType.RESEARCH_ONLY)
    runbook = builder.build_runbook(profile)

    output_path = builder.write_runbook(runbook, tmp_path)
    assert output_path.exists()
    assert "# Operator Runbook" in output_path.read_text(encoding="utf-8")
