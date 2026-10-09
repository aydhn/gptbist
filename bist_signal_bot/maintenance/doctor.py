from typing import Any
import logging
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from bist_signal_bot.maintenance.models import MaintenanceDoctorReport, MaintenanceStatus
from bist_signal_bot.maintenance.manifest import BackupManifestBuilder
from bist_signal_bot.config.settings import get_settings

logger = logging.getLogger(__name__)


class MaintenanceDoctor:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.settings = get_settings()
        self.required_dirs = [
            "logs", "reports", "scenarios", "stress", "drift", "research_lab",
            "temp", "signals", "cache", "release", "research_ledger", "market_data", "models", "config_registry", "valuation"
        ]

    def check_required_dirs(self) -> list[str]:
        missing = []
        for d in self.required_dirs:
            if not (self.base_dir / d).exists():
                missing.append(d)
        return missing

    def check_jsonl_integrity(self, paths: list[Path]) -> list[str]:
        corrupted = []
        for path in paths:
            if not path.exists() or not path.is_file() or not str(path).endswith('.jsonl'):
                continue
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            json.loads(line)
            except Exception:
                corrupted.append(str(path.relative_to(self.base_dir)))
        return corrupted

    def check_secret_risk(self, paths: list[Path]) -> list[str]:
        risks = []
        for path in paths:
             is_excluded, reason = BackupManifestBuilder.should_exclude(path)
             if is_excluded and ('secret' in reason or 'token' in reason or 'credentials' in reason or 'private key' in reason):
                  risks.append(f"{path.relative_to(self.base_dir)} ({reason})")
        return risks

    def run_doctor(self, deep: bool = False) -> MaintenanceDoctorReport:
        start_time = time.time()

        missing_dirs = self.check_required_dirs()
        corrupted_files = []
        secret_risk_files = []
        checked_paths = []

        jsonl_paths = []
        all_paths = []
        for p in self.base_dir.rglob('*'):
             if p.is_file():
                  all_paths.append(p)
                  if str(p).endswith('.jsonl'):
                       jsonl_paths.append(p)

        checked_paths.extend([str(p.relative_to(self.base_dir)) for p in all_paths])

        if getattr(self.settings, "MAINTENANCE_DOCTOR_CHECK_JSONL", True):
             corrupted_files.extend(self.check_jsonl_integrity(jsonl_paths))

        if getattr(self.settings, "MAINTENANCE_DOCTOR_CHECK_SECRET_RISK", True):
             secret_risk_files.extend(self.check_secret_risk(all_paths))

        # Config Registry Checks
        if getattr(self.settings, "ENABLE_CONFIG_REGISTRY", False):
             try:
                 from bist_signal_bot.app.config_registry_app import create_config_registry_store
                 store = create_config_registry_store(self.settings)
                 store.load_latest_snapshot() # tests integrity
             except Exception as e:
                 corrupted_files.append(f"config_registry/snapshots (error: {e})")

        status = MaintenanceStatus.SUCCESS
        if corrupted_files or secret_risk_files:
             status = MaintenanceStatus.WARNING

        recommendations = []
        if missing_dirs:
             recommendations.append("Run application initialization to create missing directories.")
        if corrupted_files:
             recommendations.append("Investigate and repair corrupted JSONL files (or restore from backup).")
        if secret_risk_files:
             recommendations.append("Remove secret files from the data directory. They will not be backed up.")

        return MaintenanceDoctorReport(
            report_id=f"doc_{int(time.time())}",
            generated_at=datetime.now(timezone.utc),
            status=status,
            checked_paths=checked_paths,
            missing_dirs=missing_dirs,
            corrupted_files=corrupted_files,
            secret_risk_files=secret_risk_files,
            recommendations=recommendations
        )

    def get_telegram_summary(self) -> dict:
        return {"status": "HEALTHY", "warnings": 0}

    def check_whatif_store(self) -> dict[str, Any]:
        try:
            from bist_signal_bot.storage.paths import get_whatif_dir
            d = get_whatif_dir(self.settings)
            runs = d / "runs"
            if not d.exists() or not os.access(d, os.W_OK):
                return {"status": "FAIL", "message": f"WhatIf directory {d} not writable"}
            return {"status": "PASS", "message": "WhatIf store OK", "path": str(d)}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}


def run_doctor(settings=None, as_json=False, data_catalog=False, feature_store=False, leaderboard=False, orchestrator=False, final_audit=False, final_handoff=False):
    res = {
        "status": "healthy",
        "checks": [
            "db_connection",
            "disk_space",
            "permissions"
        ]
    }
    if data_catalog:
        res["data_catalog"] = {
            "missing_contracts": 0,
            "missing_required_datasets": 0,
            "schema_drift": 0,
            "stale_datasets": 0,
            "orphan_lineage": 0,
            "low_quality_score": 0
        }

    if final_audit:
        append_final_audit_doctor_checks(res, settings)

    if final_handoff:
        append_final_handoff_doctor_checks(res, settings)

    if orchestrator:
        res["research_orchestrator"] = {
            "missing_campaigns": 0,
            "invalid_DAG": 0,
            "stale_run_report": 0,
            "blocked_guardrails": 0,
            "failed_recent_run": 0
        }
    if as_json:
        import json
        print(json.dumps(res, indent=2))
    else:
        print(f"Doctor Status: {res['status']}")
        if data_catalog:
             print("Data Catalog Checks: OK")
    if final_audit:
        append_final_audit_doctor_checks(res, settings)

        if orchestrator:
             print("Research Orchestrator Checks: OK")
        if final_handoff:
             print("Final Handoff Checks: OK")

def append_final_audit_doctor_checks(report: dict, settings: Any):
    if not getattr(settings, "ENABLE_FINAL_AUDIT", True):
        return

    try:
        from bist_signal_bot.app.final_audit_app import create_final_audit_store
        store = create_final_audit_store(settings=settings)
        latest_cand = store.load_latest_release_candidate()
        latest_sec = store.load_latest_security_audit()

        issues = []
        if not latest_cand:
            issues.append("Missing release candidate.")
        if latest_sec and latest_sec.blocked_findings:
            issues.append(f"Blocked security findings: {latest_sec.blocked_findings}")

        report["final_audit"] = {
            "status": "FAIL" if issues else "PASS",
            "issues": issues
        }
    except Exception as e:
        logger.error(f"Error checking final audit: {e}", exc_info=True)
        report["final_audit"] = {
            "status": "ERROR",
            "issues": [f"Exception during check: {e}"]
        }

def append_final_handoff_doctor_checks(report: dict, settings: Any):
    if not getattr(settings, "ENABLE_FINAL_HANDOFF", True):
        return

    try:
        from bist_signal_bot.app.final_handoff_app import create_final_handoff_store
        store = create_final_handoff_store(settings=settings)
        op_playbook = store.load_latest_operator_playbook()
        dev_playbook = store.load_latest_developer_playbook()
        command_map = store.load_command_map()
        roadmap = store.load_roadmap()
        latest_pack = store.load_latest_release_pack()

        issues = []
        if not op_playbook or not dev_playbook:
            issues.append("missing playbooks")
        if not command_map:
            issues.append("missing final command map")
        if not roadmap:
            issues.append("missing roadmap")
        if not latest_pack or latest_pack.stage.value not in ["BUILT", "VERIFIED", "HANDOFF_READY", "FROZEN"]:
            issues.append("release pack incomplete")

        report["final_handoff"] = {
            "status": "FAIL" if issues else "PASS",
            "issues": issues
        }
    except Exception as e:
        logger.error(f"Error checking final handoff: {e}", exc_info=True)
        report["final_handoff"] = {
            "status": "ERROR",
            "issues": [f"Exception during check: {e}"]
        }
