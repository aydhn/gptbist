import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.final_audit.models import (
    FinalAuditCheckResult,
    FinalAcceptanceSuite,
    FinalIntegrationMatrix,
    FinalSecurityAuditResult,
    ReleaseCandidateManifest,
    HardeningFreezeManifest,
    GoNoGoDecision,
    FinalRiskRegisterItem,
    FinalAuditReport
)
from bist_signal_bot.storage.paths import get_final_audit_dir
from bist_signal_bot.config.settings import Settings

class FinalAuditStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir
        self.audit_dir = get_final_audit_dir(settings)

        self.checks_path = self.audit_dir / "checks" / "final_audit_checks.jsonl"
        self.acceptance_path = self.audit_dir / "acceptance" / "final_acceptance_suites.jsonl"
        self.integration_path = self.audit_dir / "integration" / "final_integration_matrices.jsonl"
        self.security_path = self.audit_dir / "security" / "final_security_audits.jsonl"
        self.candidate_path = self.audit_dir / "candidates" / "release_candidate_manifests.jsonl"
        self.freeze_path = self.audit_dir / "freeze" / "hardening_freeze_manifests.jsonl"
        self.go_no_go_path = self.audit_dir / "go_no_go" / "go_no_go_decisions.jsonl"
        self.risk_path = self.audit_dir / "risks" / "final_risk_register.jsonl"
        self.reports_dir = self.audit_dir / "reports"

        self._ensure_dirs()

    def _ensure_dirs(self):
        self.checks_path.parent.mkdir(parents=True, exist_ok=True)
        self.acceptance_path.parent.mkdir(parents=True, exist_ok=True)
        self.integration_path.parent.mkdir(parents=True, exist_ok=True)
        self.security_path.parent.mkdir(parents=True, exist_ok=True)
        self.candidate_path.parent.mkdir(parents=True, exist_ok=True)
        self.freeze_path.parent.mkdir(parents=True, exist_ok=True)
        self.go_no_go_path.parent.mkdir(parents=True, exist_ok=True)
        self.risk_path.parent.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def append_checks(self, checks: list[FinalAuditCheckResult]) -> Path:
        with open(self.checks_path, "a", encoding="utf-8") as f:
            for check in checks:
                f.write(check.model_dump_json() + "\n")
        return self.checks_path

    def append_acceptance_suite(self, suite: FinalAcceptanceSuite) -> Path:
        with open(self.acceptance_path, "a", encoding="utf-8") as f:
            f.write(suite.model_dump_json() + "\n")
        return self.acceptance_path

    def load_latest_acceptance_suite(self) -> FinalAcceptanceSuite | None:
        if not self.acceptance_path.exists():
            return None
        with open(self.acceptance_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                return FinalAcceptanceSuite.model_validate_json(lines[-1])
        return None

    def append_integration_matrix(self, matrix: FinalIntegrationMatrix) -> Path:
        with open(self.integration_path, "a", encoding="utf-8") as f:
            f.write(matrix.model_dump_json() + "\n")
        return self.integration_path

    def load_latest_integration_matrix(self) -> FinalIntegrationMatrix | None:
        if not self.integration_path.exists():
            return None
        with open(self.integration_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                return FinalIntegrationMatrix.model_validate_json(lines[-1])
        return None

    def append_security_audit(self, result: FinalSecurityAuditResult) -> Path:
        with open(self.security_path, "a", encoding="utf-8") as f:
            f.write(result.model_dump_json() + "\n")
        return self.security_path

    def load_latest_security_audit(self) -> FinalSecurityAuditResult | None:
        if not self.security_path.exists():
            return None
        with open(self.security_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                return FinalSecurityAuditResult.model_validate_json(lines[-1])
        return None

    def append_release_candidate(self, candidate: ReleaseCandidateManifest) -> Path:
        with open(self.candidate_path, "a", encoding="utf-8") as f:
            f.write(candidate.model_dump_json() + "\n")
        return self.candidate_path

    def load_latest_release_candidate(self) -> ReleaseCandidateManifest | None:
        if not self.candidate_path.exists():
            return None
        with open(self.candidate_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                return ReleaseCandidateManifest.model_validate_json(lines[-1])
        return None

    def append_freeze_manifest(self, freeze: HardeningFreezeManifest) -> Path:
        with open(self.freeze_path, "a", encoding="utf-8") as f:
            f.write(freeze.model_dump_json() + "\n")
        return self.freeze_path

    def load_latest_freeze_manifest(self) -> HardeningFreezeManifest | None:
        if not self.freeze_path.exists():
            return None
        with open(self.freeze_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                return HardeningFreezeManifest.model_validate_json(lines[-1])
        return None

    def append_go_no_go(self, decision: GoNoGoDecision) -> Path:
        with open(self.go_no_go_path, "a", encoding="utf-8") as f:
            f.write(decision.model_dump_json() + "\n")
        return self.go_no_go_path

    def load_latest_go_no_go(self) -> GoNoGoDecision | None:
        if not self.go_no_go_path.exists():
            return None
        with open(self.go_no_go_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                return GoNoGoDecision.model_validate_json(lines[-1])
        return None

    def append_risk_register(self, items: list[FinalRiskRegisterItem]) -> Path:
        with open(self.risk_path, "a", encoding="utf-8") as f:
            for item in items:
                f.write(item.model_dump_json() + "\n")
        return self.risk_path

    def save_report(self, report: FinalAuditReport, markdown_text: str) -> dict[str, Path]:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        report_dir = self.reports_dir / date_str
        report_dir.mkdir(parents=True, exist_ok=True)

        md_path = report_dir / "final_audit_report.md"
        json_path = report_dir / "final_audit_report.json"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        with open(json_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

        return {"markdown": md_path, "json": json_path}
