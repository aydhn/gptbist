import json
from pathlib import Path
from bist_signal_bot.maintenance_automation.models import (
    MaintenanceCadencePolicy, RetentionPolicy, MaintenancePlan, MaintenanceRun,
    MaintenanceActionResult, CleanupCandidate, BackupManifest, MaintenanceRunManifest,
    MaintenanceAutomationReport
)

class MaintenanceAutomationStore:
    def save_cadence_policies(self, policies: list[MaintenanceCadencePolicy]) -> Path: return Path("mock.json")
    def load_cadence_policies(self) -> list[MaintenanceCadencePolicy]: return []
    def save_retention_policies(self, policies: list[RetentionPolicy]) -> Path: return Path("mock.json")
    def load_retention_policies(self) -> list[RetentionPolicy]: return []
    def append_plan(self, plan: MaintenancePlan) -> Path: return Path("mock.jsonl")
    def load_plans(self, limit: int = 1000) -> list[MaintenancePlan]: return []
    def append_run(self, run: MaintenanceRun) -> Path: return Path("mock.jsonl")
    def load_runs(self, limit: int = 1000) -> list[MaintenanceRun]: return []
    def load_latest_run(self) -> MaintenanceRun | None: return None
    def append_results(self, results: list[MaintenanceActionResult]) -> Path: return Path("mock.jsonl")
    def append_cleanup_candidates(self, candidates: list[CleanupCandidate]) -> Path: return Path("mock.jsonl")
    def append_backup_manifest(self, manifest: BackupManifest) -> Path: return Path("mock.jsonl")
    def append_run_manifest(self, manifest: MaintenanceRunManifest) -> Path: return Path("mock.jsonl")
    def save_report(self, report: MaintenanceAutomationReport, markdown_text: str) -> dict: return {"path": Path("mock.md")}
