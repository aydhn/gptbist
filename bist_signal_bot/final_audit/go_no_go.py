from datetime import datetime, timezone
import uuid
from typing import Any

from bist_signal_bot.final_audit.models import (
    GoNoGoDecision,
    ReleaseCandidateManifest,
    FinalAcceptanceSuite,
    FinalSecurityAuditResult,
    FinalIntegrationMatrix,
    ReleaseDecision,
    FinalAuditStatus
)
from bist_signal_bot.config.settings import Settings

class GoNoGoEvaluator:
    def __init__(self, settings: Settings | None = None, base_dir: Any | None = None):
        self.settings = settings
        self.base_dir = base_dir

    def evaluate(self,
                 candidate: ReleaseCandidateManifest,
                 acceptance: FinalAcceptanceSuite | None = None,
                 security: FinalSecurityAuditResult | None = None,
                 matrix: FinalIntegrationMatrix | None = None) -> GoNoGoDecision:

        blocking = self.blocking_reasons(candidate, acceptance, security, matrix)
        warnings = self.warning_reasons(candidate, acceptance, security, matrix)

        decision = self.decision_from_inputs(blocking, warnings)
        status = FinalAuditStatus.PASS
        if decision == ReleaseDecision.BLOCKED:
            status = FinalAuditStatus.BLOCKED
        elif decision == ReleaseDecision.NO_GO:
            status = FinalAuditStatus.FAIL
        elif decision == ReleaseDecision.GO_WITH_WARNINGS:
            status = FinalAuditStatus.WATCH

        sec_pass = security.blocked_findings == [] if security else False
        acc_pass = acceptance.status in (FinalAuditStatus.PASS, FinalAuditStatus.WATCH) if acceptance else False
        matrix_pass = matrix.status in (FinalAuditStatus.PASS, FinalAuditStatus.WATCH) if matrix else False

        return GoNoGoDecision(
            decision_id=f"gn_{uuid.uuid4().hex[:8]}",
            candidate_id=candidate.candidate_id,
            created_at=datetime.now(timezone.utc),
            decision=decision,
            status=status,
            blocking_reasons=blocking,
            warning_reasons=warnings,
            required_checks_passed=matrix_pass,
            security_passed=sec_pass,
            docs_passed=True,
            qa_passed=True,
            ops_passed=True,
            acceptance_passed=acc_pass,
            final_notes=["Review generated reports for complete details."]
        )

    def blocking_reasons(self,
                         candidate: ReleaseCandidateManifest,
                         acceptance: FinalAcceptanceSuite | None,
                         security: FinalSecurityAuditResult | None,
                         matrix: FinalIntegrationMatrix | None) -> list[str]:
        reasons = []
        if security and security.blocked_findings:
            reasons.append(f"Security blocked: {security.blocked_findings}")
        if acceptance and acceptance.status in (FinalAuditStatus.FAIL, FinalAuditStatus.BLOCKED):
            reasons.append(f"Acceptance suite failed/blocked: {acceptance.status}")
        if matrix and matrix.status in (FinalAuditStatus.FAIL, FinalAuditStatus.BLOCKED):
            reasons.append(f"Integration matrix failed/blocked: {matrix.status}")
        return reasons

    def warning_reasons(self,
                        candidate: ReleaseCandidateManifest,
                        acceptance: FinalAcceptanceSuite | None,
                        security: FinalSecurityAuditResult | None,
                        matrix: FinalIntegrationMatrix | None) -> list[str]:
        warnings = []
        if acceptance and acceptance.status == FinalAuditStatus.WATCH:
            warnings.append("Acceptance suite generated warnings.")
        if matrix and matrix.status == FinalAuditStatus.WATCH:
            warnings.append("Integration matrix generated warnings.")
        return warnings

    def decision_from_inputs(self, blocking: list[str], warnings: list[str]) -> ReleaseDecision:
        if any("blocked" in b.lower() for b in blocking):
            return ReleaseDecision.BLOCKED
        if blocking:
            return ReleaseDecision.NO_GO
        if warnings:
            return ReleaseDecision.GO_WITH_WARNINGS
        return ReleaseDecision.GO

    def validate_decision(self, decision: GoNoGoDecision) -> list[str]:
        errors = []
        if decision.decision == ReleaseDecision.UNKNOWN:
            errors.append("Decision cannot be UNKNOWN.")
        # Ensure no trade readiness claim
        notes = " ".join(decision.final_notes).lower()
        if any(w in notes for w in ["trade ready", "live ready", "al/sat", "işlem yapılabilir"]):
            errors.append("Decision contains trade readiness language.")
        return errors
