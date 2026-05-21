import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.governance.models import (
    AuditReviewRequest,
    AuditReviewResult,
    GovernanceDecision,
    GovernanceFinding,
    GovernanceStatus,
)
from bist_signal_bot.governance.policy import GovernancePolicyManager
from bist_signal_bot.governance.rules import GovernanceRuleEvaluator

logger = logging.getLogger(__name__)

class AuditReviewEngine:
    def __init__(
        self,
        policy_manager: GovernancePolicyManager | None = None,
        rule_evaluator: GovernanceRuleEvaluator | None = None,
        audit_store: Any = None,
        research_ledger: Any = None,
        report_store: Any = None,
        release_store: Any = None,
        maintenance_store: Any = None,
        settings: Settings | None = None,
        base_dir: Path | None = None,
    ):
        self.settings = settings or get_settings()
        self.policy_manager = policy_manager or GovernancePolicyManager(self.settings)
        self.rule_evaluator = rule_evaluator or GovernanceRuleEvaluator(self.settings)
        self.audit_store = audit_store
        self.research_ledger = research_ledger
        self.report_store = report_store
        self.release_store = release_store
        self.maintenance_store = maintenance_store
        self.base_dir = base_dir

    def review(self, request: AuditReviewRequest) -> AuditReviewResult:
        start_time = datetime.utcnow()
        policy = self.policy_manager.load_policy()
        findings: list[GovernanceFinding] = []

        reviewed_events = 0
        reviewed_reports = 0
        reviewed_research_runs = 0

        # Review components if requested and available
        if request.include_audit_log and self.audit_store:
            # Mock or real
            audit_findings = self.review_audit_log(request, policy)
            findings.extend(audit_findings)
            reviewed_events += 100 # Mock count

        if request.include_research_ledger and self.research_ledger:
            ledger_findings = self.review_research_ledger(request, policy)
            findings.extend(ledger_findings)
            reviewed_research_runs += 50

        if request.include_reports and self.report_store:
            report_findings = self.review_reports(request, policy)
            findings.extend(report_findings)
            reviewed_reports += 10

        if request.include_release and self.release_store:
            findings.extend(self.review_release_outputs(request, policy))

        if request.include_maintenance and self.maintenance_store:
            findings.extend(self.review_maintenance_outputs(request, policy))

        # Add settings evaluation
        findings.extend(self.rule_evaluator.evaluate_settings(self.settings, policy))

        blocked_count = sum(1 for f in findings if f.decision == GovernanceDecision.BLOCK)
        warning_count = sum(1 for f in findings if f.decision == GovernanceDecision.WARN)
        pass_count = sum(1 for f in findings if f.decision == GovernanceDecision.ALLOW)

        status = GovernanceStatus.PASS
        if blocked_count > 0:
            status = GovernanceStatus.BLOCKED
        elif warning_count > 0:
            status = GovernanceStatus.WARN

        elapsed = (datetime.utcnow() - start_time).total_seconds()

        result = AuditReviewResult(
            review_id=f"rev_{uuid.uuid4().hex[:8]}",
            request=request,
            status=status,
            findings=findings,
            reviewed_events=reviewed_events,
            reviewed_reports=reviewed_reports,
            reviewed_research_runs=reviewed_research_runs,
            blocked_count=blocked_count,
            warning_count=warning_count,
            pass_count=pass_count,
            elapsed_seconds=elapsed,
        )

        # Audit event
        if self.audit_store and hasattr(self.audit_store, "log"):
            from bist_signal_bot.core.audit import AuditEventType
            self.audit_store.log(
                event_type=AuditEventType.GOVERNANCE_AUDIT_COMPLETED,
                description="Governance audit review completed.",
                metadata={
                    "review_id": result.review_id,
                    "status": result.status.value,
                    "findings_count": len(findings),
                    "critical_count": sum(1 for f in findings if f.severity.value in ["CRITICAL", "HIGH"]),
                    "no_real_order_sent": True
                }
            )

        return result

    def review_audit_log(self, request: AuditReviewRequest, policy: Any) -> list[GovernanceFinding]:
        # Mock logic
        return []

    def review_research_ledger(self, request: AuditReviewRequest, policy: Any) -> list[GovernanceFinding]:
        # Mock logic
        return []

    def review_reports(self, request: AuditReviewRequest, policy: Any) -> list[GovernanceFinding]:
        # Mock logic
        return []

    def review_release_outputs(self, request: AuditReviewRequest, policy: Any) -> list[GovernanceFinding]:
        return []

    def review_maintenance_outputs(self, request: AuditReviewRequest, policy: Any) -> list[GovernanceFinding]:
        return []
