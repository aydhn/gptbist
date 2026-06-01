from typing import Any
import uuid
from datetime import datetime, timezone

from bist_signal_bot.research_orchestrator.models import (
    ResearchRunManifest,
    ResearchRun,
    ResearchRunPlan,
    ResearchRunStatus,
    ResearchExecutionMode
)

class ResearchRunReplayEngine:
    def replay_run(self, manifest: ResearchRunManifest, dry_run: bool = True) -> ResearchRun:
        # Mock replay
        return ResearchRun(
            run_id=str(uuid.uuid4()),
            plan=ResearchRunPlan(
                plan_id=str(uuid.uuid4()),
                campaign_type="CUSTOM",
                name="Replay Plan",
                created_at=datetime.now(timezone.utc),
                execution_mode=ResearchExecutionMode.REPLAY
            ),
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            status=ResearchRunStatus.PASS,
            manifest=manifest
        )

    def load_manifest(self, manifest_id_or_path: str) -> ResearchRunManifest | None:
        return None

    def compare_runs(self, run_a: ResearchRun, run_b: ResearchRun) -> dict[str, Any]:
        return {"match": True, "differences": []}

    def replay_plan(self, plan: ResearchRunPlan, dry_run: bool = True) -> ResearchRun:
        return ResearchRun(
            run_id=str(uuid.uuid4()),
            plan=plan,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            status=ResearchRunStatus.PASS
        )

    def replayable(self, manifest: ResearchRunManifest) -> list[str]:
        return []
