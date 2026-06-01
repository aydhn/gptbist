import uuid
import hashlib
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.research_orchestrator.models import (
    ResearchRun,
    ResearchRunPlan,
    ResearchTaskResult,
    ResearchRunManifest,
    ResearchExecutionMode
)

class ResearchRunManifestBuilder:
    def build_manifest(self, run: ResearchRun) -> ResearchRunManifest:
        manifest_id = str(uuid.uuid4())

        inputs = self.input_refs(run.plan)
        outputs = self.output_refs(run.task_results)

        all_refs = {**inputs, **outputs}
        checksums = self.checksum_refs(all_refs)

        return ResearchRunManifest(
            manifest_id=manifest_id,
            plan_id=run.plan.plan_id,
            run_id=run.run_id,
            created_at=datetime.now(timezone.utc),
            execution_mode=run.plan.execution_mode,
            config_snapshot_ref="config_snapshot_mock",
            input_refs=inputs,
            output_refs=outputs,
            task_result_ids=[r.result_id for r in run.task_results],
            checksum_manifest=checksums,
            environment_summary=self.environment_summary()
        )

    def config_snapshot(self) -> dict[str, Any]:
        return {"redacted": True, "note": "Config snapshot mock"}

    def environment_summary(self) -> dict[str, Any]:
        return {"python_version": "3.12", "os": "Linux", "is_container": True}

    def input_refs(self, plan: ResearchRunPlan) -> dict[str, Any]:
        return {
            "symbols": plan.symbol_universe,
            "strategies": plan.strategy_names,
            "models": plan.model_ids,
            "feature_sets": plan.feature_set_ids
        }

    def output_refs(self, results: list[ResearchTaskResult]) -> dict[str, Any]:
        refs = {}
        for r in results:
            if r.output_ref:
                refs[f"task_{r.task_id}_output"] = r.output_ref
        return refs

    def checksum_refs(self, refs: dict[str, Any]) -> dict[str, str]:
        checksums = {}
        for k, v in refs.items():
            s = str(v).encode('utf-8')
            checksums[k] = hashlib.sha256(s).hexdigest()
        return checksums
