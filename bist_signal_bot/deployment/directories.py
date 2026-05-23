import uuid
from pathlib import Path
from typing import List, Dict, Any
from bist_signal_bot.deployment.models import EnvironmentCheckResult, EnvironmentCheckType, DeploymentStatus, DeploymentDecision
from bist_signal_bot.config.settings import Settings

class DeploymentDirectoryManager:
    def __init__(self, settings: Settings, base_dir: Path):
        self.settings = settings
        self.base_dir = base_dir

    def required_directories(self) -> List[Path]:
        return [
            self.base_dir / "data",
            self.base_dir / "logs",
            self.base_dir / "reports",
            self.base_dir / getattr(self.settings, "CACHE_DIR", "cache"),
            self.base_dir / getattr(self.settings, "ML_MODELS_DIR_NAME", "ml/models"),
            self.base_dir / getattr(self.settings, "RESEARCH_DIR_NAME", "research"),
            self.base_dir / getattr(self.settings, "SIGNALS_DIR_NAME", "signals"),
            self.base_dir / getattr(self.settings, "REVIEW_DIR_NAME", "review"),
            self.base_dir / getattr(self.settings, "KNOWLEDGE_DIR_NAME", "knowledge"),
            self.base_dir / getattr(self.settings, "SCHEDULER_DIR_NAME", "scheduler"),
            self.base_dir / getattr(self.settings, "TELEGRAM_CENTER_DIR_NAME", "telegram_center"),
            self.base_dir / getattr(self.settings, "GOVERNANCE_DIR_NAME", "governance"),
            self.base_dir / getattr(self.settings, "MAINTENANCE_DIR_NAME", "maintenance"),
            self.base_dir / getattr(self.settings, "RESEARCH_LAB_DIR_NAME", "research_lab"),
            self.base_dir / getattr(self.settings, "PORTFOLIO_RESEARCH_DIR_NAME", "portfolio_research"),
            self.base_dir / "stress",
            self.base_dir / getattr(self.settings, "DRIFT_DIR_NAME", "drift"),
            self.base_dir / getattr(self.settings, "BACKUP_DIR_NAME", "backups")
        ]

    def init_directories(self, confirm: bool = False, dry_run: bool = True) -> List[EnvironmentCheckResult]:
        results = []
        dirs = self.required_directories()

        for d in dirs:
            if d.exists():
                results.append(EnvironmentCheckResult(
                    check_id=str(uuid.uuid4()),
                    check_type=EnvironmentCheckType.FILESYSTEM,
                    status=DeploymentStatus.PASS,
                    decision=DeploymentDecision.CONTINUE,
                    title=f"Directory Exists",
                    message=f"Directory {d} already exists."
                ))
            else:
                if dry_run:
                    results.append(EnvironmentCheckResult(
                        check_id=str(uuid.uuid4()),
                        check_type=EnvironmentCheckType.FILESYSTEM,
                        status=DeploymentStatus.SKIPPED,
                        decision=DeploymentDecision.SKIP,
                        title=f"Directory Creation Dry-Run",
                        message=f"Would create directory {d}."
                    ))
                elif confirm:
                    try:
                        d.mkdir(parents=True, exist_ok=True)
                        results.append(EnvironmentCheckResult(
                            check_id=str(uuid.uuid4()),
                            check_type=EnvironmentCheckType.FILESYSTEM,
                            status=DeploymentStatus.PASS,
                            decision=DeploymentDecision.CONTINUE,
                            title=f"Directory Created",
                            message=f"Created directory {d}."
                        ))
                    except Exception as e:
                        results.append(EnvironmentCheckResult(
                            check_id=str(uuid.uuid4()),
                            check_type=EnvironmentCheckType.FILESYSTEM,
                            status=DeploymentStatus.FAIL,
                            decision=DeploymentDecision.BLOCK,
                            title=f"Directory Creation Failed",
                            message=f"Failed to create {d}: {e}"
                        ))
                else:
                     results.append(EnvironmentCheckResult(
                        check_id=str(uuid.uuid4()),
                        check_type=EnvironmentCheckType.FILESYSTEM,
                        status=DeploymentStatus.WARN,
                        decision=DeploymentDecision.REQUIRE_CONFIRM,
                        title=f"Directory Creation Requires Confirm",
                        message=f"Directory {d} missing, run with confirm=True to create."
                    ))
        return results

    def verify_directories(self) -> List[EnvironmentCheckResult]:
        results = []
        for d in self.required_directories():
            status = DeploymentStatus.PASS if d.exists() else DeploymentStatus.FAIL
            results.append(EnvironmentCheckResult(
                check_id=str(uuid.uuid4()),
                check_type=EnvironmentCheckType.FILESYSTEM,
                status=status,
                decision=DeploymentDecision.CONTINUE if status == DeploymentStatus.PASS else DeploymentDecision.WARN_CONTINUE,
                title="Directory Verification",
                message=f"Directory {d} {'exists' if d.exists() else 'is missing'}."
            ))
        return results

    def directory_permissions_report(self) -> Dict[str, Any]:
        report = {}
        for d in self.required_directories():
            report[str(d)] = {
                "exists": d.exists(),
                "writable": os.access(d, os.W_OK) if d.exists() else False
            }
        return report
