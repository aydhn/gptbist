import pytest
from bist_signal_bot.research_orchestrator.replay import ResearchRunReplayEngine
from bist_signal_bot.research_orchestrator.models import ResearchRunManifest, ResearchExecutionMode
from datetime import datetime, timezone

def test_replay_dry_run():
    engine = ResearchRunReplayEngine()
    manifest = ResearchRunManifest(
        manifest_id="m1", plan_id="p1", run_id="r1", created_at=datetime.now(timezone.utc),
        execution_mode=ResearchExecutionMode.DRY_RUN
    )
    run = engine.replay_run(manifest, dry_run=True)
    assert run.plan.execution_mode == ResearchExecutionMode.REPLAY
    assert run.manifest.manifest_id == "m1"
