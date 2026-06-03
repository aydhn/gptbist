import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from bist_signal_bot.maintenance_automation.models import (
    MaintenanceCadencePolicy,
    RetentionPolicy,
    MaintenancePlan,
    MaintenanceRun,
    MaintenanceActionResult,
    CleanupCandidate,
    BackupManifest,
    MaintenanceRunManifest,
    MaintenanceAutomationReport
)

class MaintenanceAutomationStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.policies_dir = self.base_dir / "policies"
        self.retention_dir = self.base_dir / "retention"
        self.plans_dir = self.base_dir / "plans"
        self.runs_dir = self.base_dir / "runs"
        self.results_dir = self.base_dir / "results"
        self.cleanup_dir = self.base_dir / "cleanup"
        self.backups_dir = self.base_dir / "backups"
        self.manifests_dir = self.base_dir / "manifests"
        self.reports_dir = self.base_dir / "reports"

        for d in [self.policies_dir, self.retention_dir, self.plans_dir, self.runs_dir,
                  self.results_dir, self.cleanup_dir, self.backups_dir, self.manifests_dir, self.reports_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _save_json(self, path: Path, data: Any):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _append_jsonl(self, path: Path, data: Any):
        with open(path, 'a') as f:
            f.write(json.dumps(data, default=str) + "\n")

    def save_cadence_policies(self, policies: List[MaintenanceCadencePolicy]) -> Path:
        path = self.policies_dir / "maintenance_cadence_policies.json"
        data = [p.model_dump(mode='json') for p in policies]
        self._save_json(path, data)
        return path

    def load_cadence_policies(self) -> List[MaintenanceCadencePolicy]:
        path = self.policies_dir / "maintenance_cadence_policies.json"
        if not path.exists():
            return []
        with open(path, 'r') as f:
            data = json.load(f)
        return [MaintenanceCadencePolicy.model_validate(d) for d in data]

    def save_retention_policies(self, policies: List[RetentionPolicy]) -> Path:
        path = self.retention_dir / "retention_policies.json"
        data = [p.model_dump(mode='json') for p in policies]
        self._save_json(path, data)
        return path

    def load_retention_policies(self) -> List[RetentionPolicy]:
        path = self.retention_dir / "retention_policies.json"
        if not path.exists():
            return []
        with open(path, 'r') as f:
            data = json.load(f)
        return [RetentionPolicy.model_validate(d) for d in data]

    def append_plan(self, plan: MaintenancePlan) -> Path:
        path = self.plans_dir / "maintenance_plans.jsonl"
        self._append_jsonl(path, plan.model_dump(mode='json'))
        return path

    def load_plans(self, limit: int = 1000) -> List[MaintenancePlan]:
        path = self.plans_dir / "maintenance_plans.jsonl"
        if not path.exists():
            return []
        plans = []
        with open(path, 'r') as f:
            for line in f:
                if line.strip():
                    plans.append(MaintenancePlan.model_validate_json(line))
        return plans[-limit:]

    def append_run(self, run: MaintenanceRun) -> Path:
        path = self.runs_dir / "maintenance_runs.jsonl"
        self._append_jsonl(path, run.model_dump(mode='json'))
        return path

    def load_runs(self, limit: int = 1000) -> List[MaintenanceRun]:
        path = self.runs_dir / "maintenance_runs.jsonl"
        if not path.exists():
            return []
        runs = []
        with open(path, 'r') as f:
            for line in f:
                if line.strip():
                    runs.append(MaintenanceRun.model_validate_json(line))
        return runs[-limit:]

    def load_latest_run(self) -> Optional[MaintenanceRun]:
        runs = self.load_runs(limit=1)
        return runs[0] if runs else None

    def append_results(self, results: List[MaintenanceActionResult]) -> Path:
        path = self.results_dir / "maintenance_action_results.jsonl"
        for r in results:
            self._append_jsonl(path, r.model_dump(mode='json'))
        return path

    def append_cleanup_candidates(self, candidates: List[CleanupCandidate]) -> Path:
        path = self.cleanup_dir / "cleanup_candidates.jsonl"
        for c in candidates:
            self._append_jsonl(path, c.model_dump(mode='json'))
        return path

    def append_backup_manifest(self, manifest: BackupManifest) -> Path:
        path = self.backups_dir / "backup_manifests.jsonl"
        self._append_jsonl(path, manifest.model_dump(mode='json'))
        return path

    def append_run_manifest(self, manifest: MaintenanceRunManifest) -> Path:
        path = self.manifests_dir / "maintenance_run_manifests.jsonl"
        self._append_jsonl(path, manifest.model_dump(mode='json'))
        return path

    def save_report(self, report: MaintenanceAutomationReport, markdown_text: str) -> Dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        report_dir = self.reports_dir / date_str
        report_dir.mkdir(exist_ok=True)

        json_path = report_dir / "maintenance_automation_report.json"
        md_path = report_dir / "maintenance_automation_report.md"

        self._save_json(json_path, report.model_dump(mode='json'))
        with open(md_path, 'w') as f:
            f.write(markdown_text)

        return {"json": json_path, "md": md_path}
