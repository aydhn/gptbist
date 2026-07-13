
import json
from pathlib import Path
from datetime import datetime

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_data_dir
from bist_signal_bot.storage.jsonl import append_to_jsonl, read_jsonl

from bist_signal_bot.ops.models import (
    OpsHealthSnapshot,
    StoreIntegrityResult,
    StalenessFinding,
    OpsIncident,
    OpsStatus,
    OpsRunbook,
    BackupManifest,
    RestorePlan,
    RetentionFinding,
    MigrationCheckResult,
    OperationalReadinessResult,
    OpsReport
)

class OpsStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings
        if base_dir is None:
            from bist_signal_bot.storage.paths import get_ops_dir
            self.ops_dir = get_ops_dir(settings)
        else:
            self.ops_dir = base_dir / (settings.OPS_DIR_NAME if settings and hasattr(settings, "OPS_DIR_NAME") else "ops")
            self.ops_dir.mkdir(parents=True, exist_ok=True)

        self.health_path = self.ops_dir / "health" / "ops_health_snapshots.jsonl"
        self.integrity_path = self.ops_dir / "store_integrity" / "store_integrity_results.jsonl"
        self.staleness_path = self.ops_dir / "staleness" / "staleness_findings.jsonl"
        self.incidents_path = self.ops_dir / "incidents" / "ops_incidents.jsonl"
        self.runbooks_path = self.ops_dir / "runbooks" / "ops_runbooks.json"
        self.backups_path = self.ops_dir / "backups" / "backup_manifests.jsonl"
        self.restore_path = self.ops_dir / "restore" / "restore_plans.jsonl"
        self.retention_path = self.ops_dir / "retention" / "retention_findings.jsonl"
        self.migrations_path = self.ops_dir / "migrations" / "migration_check_results.jsonl"
        self.readiness_path = self.ops_dir / "readiness" / "operational_readiness_results.jsonl"
        self.reports_dir = self.ops_dir / "reports"

        for path in [self.health_path, self.integrity_path, self.staleness_path,
                     self.incidents_path, self.backups_path, self.restore_path,
                     self.retention_path, self.migrations_path, self.readiness_path]:
            path.parent.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.runbooks_path.parent.mkdir(parents=True, exist_ok=True)


    def append_health_snapshot(self, snapshot: OpsHealthSnapshot) -> Path:
        append_to_jsonl(self.health_path, snapshot.model_dump(mode="json"))
        return self.health_path

    def load_latest_health_snapshot(self) -> OpsHealthSnapshot | None:
        if not self.health_path.exists(): return None
        records = read_jsonl(self.health_path)
        if not records: return None
        return OpsHealthSnapshot(**records[-1])

    def append_store_integrity(self, result: StoreIntegrityResult) -> Path:
        append_to_jsonl(self.integrity_path, result.model_dump(mode="json"))
        return self.integrity_path

    def load_latest_store_integrity(self) -> StoreIntegrityResult | None:
        if not self.integrity_path.exists(): return None
        records = read_jsonl(self.integrity_path)
        if not records: return None
        return StoreIntegrityResult(**records[-1])

    def append_staleness_findings(self, findings: list[StalenessFinding]) -> Path:
        for finding in findings:
            append_to_jsonl(self.staleness_path, finding.model_dump(mode="json"))
        return self.staleness_path

    def append_incident(self, incident: OpsIncident) -> Path:
        append_to_jsonl(self.incidents_path, incident.model_dump(mode="json"))
        return self.incidents_path

    def load_incidents(self, status: OpsStatus | None = None, limit: int = 1000) -> list[OpsIncident]:
        if not self.incidents_path.exists(): return []
        records = read_jsonl(self.incidents_path)
        incidents = [OpsIncident(**r) for r in records]
        latest_incidents = {}
        for inc in incidents: latest_incidents[inc.incident_id] = inc
        result = list(latest_incidents.values())
        if status: result = [inc for inc in result if inc.status == status]
        result.sort(key=lambda x: x.detected_at, reverse=True)
        return result[:limit]

    def get_incident(self, incident_id: str) -> OpsIncident | None:
        for inc in self.load_incidents():
            if inc.incident_id == incident_id: return inc
        return None

    def save_runbooks(self, runbooks: list[OpsRunbook]) -> Path:
        data = [r.model_dump(mode="json") for r in runbooks]
        with open(self.runbooks_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return self.runbooks_path

    def load_runbooks(self) -> list[OpsRunbook]:
        if not self.runbooks_path.exists(): return []
        try:
            with open(self.runbooks_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [OpsRunbook(**r) for r in data]
        except Exception: return []

    def append_backup_manifest(self, manifest: BackupManifest) -> Path:
        append_to_jsonl(self.backups_path, manifest.model_dump(mode="json"))
        return self.backups_path

    def load_latest_backup(self) -> BackupManifest | None:
        if not self.backups_path.exists(): return None
        records = read_jsonl(self.backups_path)
        if not records: return None
        return BackupManifest(**records[-1])

    def append_restore_plan(self, plan: RestorePlan) -> Path:
        append_to_jsonl(self.restore_path, plan.model_dump(mode="json"))
        return self.restore_path

    def append_retention_findings(self, findings: list[RetentionFinding]) -> Path:
        for finding in findings:
            append_to_jsonl(self.retention_path, finding.model_dump(mode="json"))
        return self.retention_path

    def append_migration_check(self, result: MigrationCheckResult) -> Path:
        append_to_jsonl(self.migrations_path, result.model_dump(mode="json"))
        return self.migrations_path

    def append_readiness(self, result: OperationalReadinessResult) -> Path:
        append_to_jsonl(self.readiness_path, result.model_dump(mode="json"))
        return self.readiness_path

    def load_latest_readiness(self) -> OperationalReadinessResult | None:
        if not self.readiness_path.exists(): return None
        records = read_jsonl(self.readiness_path)
        if not records: return None
        return OperationalReadinessResult(**records[-1])

    def save_report(self, report: OpsReport, markdown_text: str) -> dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        report_dir = self.reports_dir / date_str
        report_dir.mkdir(parents=True, exist_ok=True)
        md_path = report_dir / "ops_report.md"
        with open(md_path, "w", encoding="utf-8") as f: f.write(markdown_text)
        json_path = report_dir / "ops_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
        return {"markdown": md_path, "json": json_path}
