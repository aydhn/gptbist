import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from bist_signal_bot.core.exceptions import GoldenRegressionError
from bist_signal_bot.scenarios.models import GoldenSnapshot, GoldenComparisonResult, ScenarioResult, ScenarioStatus

class GoldenSnapshotManager:
    def __init__(self, golden_dir: Path):
        self.golden_dir = golden_dir
        self.golden_dir.mkdir(parents=True, exist_ok=True)

    def _get_snapshot_path(self, scenario_id: str) -> Path:
        p = self.golden_dir / scenario_id
        p.mkdir(parents=True, exist_ok=True)
        return p / "snapshot.json"

    def normalize_result(self, result: ScenarioResult) -> Dict[str, Any]:
        data = result.model_dump(mode='json')
        # Remove timestamps and highly variable fields
        if "started_at" in data: del data["started_at"]
        if "finished_at" in data: del data["finished_at"]
        if "elapsed_seconds" in data: del data["elapsed_seconds"]
        if "run_id" in data: del data["run_id"]

        for step in data.get("step_results", []):
            if "started_at" in step: del step["started_at"]
            if "finished_at" in step: del step["finished_at"]
            if "elapsed_seconds" in step: del step["elapsed_seconds"]
            if "stdout_tail" in step: del step["stdout_tail"]
            if "stderr_tail" in step: del step["stderr_tail"]

        # Make paths relative if any (simplified)
        for fix in data.get("fixtures", []):
            if "generated_at" in fix: del fix["generated_at"]
            if fix.get("path"):
                fix["path"] = "RELATIVE_PATH"

        return data

    def load_snapshot(self, scenario_id: str) -> Optional[GoldenSnapshot]:
        path = self._get_snapshot_path(scenario_id)
        if not path.exists():
            return None
        try:
            with open(path, "r") as f:
                return GoldenSnapshot(**json.load(f))
        except Exception:
            return None

    def save_snapshot(self, result: ScenarioResult, confirm: bool = False) -> GoldenSnapshot:
        if not confirm:
            raise GoldenRegressionError("Golden snapshot update requires explicit confirmation.")

        snapshot = GoldenSnapshot(
            snapshot_id=str(uuid.uuid4()),
            scenario_id=result.scenario.scenario_id,
            summary=result.summary(),
            normalized_output=self.normalize_result(result)
        )

        path = self._get_snapshot_path(result.scenario.scenario_id)
        with open(path, "w") as f:
            json.dump(snapshot.model_dump(mode='json'), f, indent=2)

        return snapshot

    def compare_to_snapshot(self, result: ScenarioResult, ignored_fields: Optional[List[str]] = None) -> GoldenComparisonResult:
        snapshot = self.load_snapshot(result.scenario.scenario_id)
        if not snapshot:
            return GoldenComparisonResult(
                scenario_id=result.scenario.scenario_id,
                status=ScenarioStatus.SKIPPED,
                matched=False,
                differences=[{"error": "No existing snapshot found."}]
            )

        actual_norm = self.normalize_result(result)
        diffs = self.diff_dict(snapshot.normalized_output, actual_norm)

        # Filter ignored fields (very simplified implementation)
        if ignored_fields:
            diffs = [d for d in diffs if not any(d.get("path", "").startswith(i) for i in ignored_fields)]

        matched = len(diffs) == 0
        return GoldenComparisonResult(
            scenario_id=result.scenario.scenario_id,
            snapshot_id=snapshot.snapshot_id,
            status=ScenarioStatus.SUCCESS if matched else ScenarioStatus.FAILED,
            matched=matched,
            differences=diffs,
            ignored_fields=ignored_fields or []
        )

    def diff_dict(self, expected: Dict[str, Any], actual: Dict[str, Any], path: str = "") -> List[Dict[str, Any]]:
        # Basic diff implementation
        diffs = []
        for k, v in expected.items():
            current_path = f"{path}.{k}" if path else k
            if k not in actual:
                diffs.append({"path": current_path, "type": "missing_in_actual", "expected": v})
            elif isinstance(v, dict) and isinstance(actual[k], dict):
                diffs.extend(self.diff_dict(v, actual[k], current_path))
            elif isinstance(v, list) and isinstance(actual[k], list):
                if len(v) != len(actual[k]):
                     diffs.append({"path": current_path, "type": "list_length_mismatch", "expected": len(v), "actual": len(actual[k])})
                # Deep list compare omitted for simplicity
            elif v != actual[k]:
                diffs.append({"path": current_path, "type": "value_mismatch", "expected": v, "actual": actual[k]})

        for k in actual:
            current_path = f"{path}.{k}" if path else k
            if k not in expected:
                 diffs.append({"path": current_path, "type": "extra_in_actual", "actual": actual[k]})
        return diffs
