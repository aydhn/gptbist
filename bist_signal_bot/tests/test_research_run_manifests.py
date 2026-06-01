import pytest
from bist_signal_bot.research_orchestrator.manifests import ResearchRunManifestBuilder
from bist_signal_bot.research_orchestrator.models import ResearchRun, ResearchRunPlan, ResearchCampaignType, ResearchExecutionMode, ResearchRunStatus
from datetime import datetime, timezone

def test_manifest_builder():
    builder = ResearchRunManifestBuilder()
    plan = ResearchRunPlan(
        plan_id="p1", campaign_type=ResearchCampaignType.CUSTOM, name="p", created_at=datetime.now(timezone.utc),
        execution_mode=ResearchExecutionMode.DRY_RUN, symbol_universe=["ASELS"]
    )
    run = ResearchRun(
        run_id="r1", plan=plan, started_at=datetime.now(timezone.utc), status=ResearchRunStatus.PASS
    )

    manifest = builder.build_manifest(run)
    assert manifest.manifest_id is not None
    assert manifest.input_refs["symbols"] == ["ASELS"]
    assert "symbols" in manifest.checksum_manifest
    assert manifest.config_snapshot_ref is not None
