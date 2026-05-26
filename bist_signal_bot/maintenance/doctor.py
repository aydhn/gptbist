import json
import time
from pathlib import Path
from datetime import datetime, timezone
from bist_signal_bot.maintenance.models import MaintenanceDoctorReport, MaintenanceStatus
from bist_signal_bot.maintenance.manifest import BackupManifestBuilder
from bist_signal_bot.config.settings import get_settings

class MaintenanceDoctor:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.settings = get_settings()
        self.required_dirs = [
            "logs", "reports", "scenarios", "stress", "drift", "research_lab",
            "temp", "signals", "cache", "release", "research_ledger", "market_data", "models", "config_registry"
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
