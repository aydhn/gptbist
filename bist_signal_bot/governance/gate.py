import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.governance.models import (
    GovernanceDecision,
    GovernanceDomain,
    GovernanceGateRequest,
    GovernanceGateResult,
    GovernanceStatus,
)
from bist_signal_bot.governance.policy import GovernancePolicyManager
from bist_signal_bot.governance.rules import GovernanceRuleEvaluator

logger = logging.getLogger(__name__)

class GovernanceGate:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or get_settings()

    def check_deployment_profile(self, profile) -> bool:
        if getattr(profile, "real_order_enabled", False):
            return False
        if getattr(profile, "broker_enabled", False):
            return False
        return True

        self.base_dir = base_dir
        self.policy_manager = GovernancePolicyManager(self.settings)
        self.rule_evaluator = GovernanceRuleEvaluator(self.settings)

    def run_gate(self, request: GovernanceGateRequest) -> GovernanceGateResult:
        start_time = datetime.utcnow()
        policy = self.policy_manager.load_policy()

        findings = self.rule_evaluator.evaluate_payload(request.payload, policy, request.domains)

        # Config Registry Integration
        if getattr(self.settings, "ENABLE_CONFIG_REGISTRY", False):
            try:
                from bist_signal_bot.app.config_registry_app import create_config_gate
                cg = create_config_gate(self.settings)

                # Check mapping
                gate_mapping = {
                    "runtime_gate": cg.runtime_gate,
                    "release_gate": cg.release_gate,
                    "scheduler_gate": cg.scheduler_gate,
                    "research_lab_gate": cg.research_lab_gate,
                    "deployment_gate": cg.deployment_gate,
                }

                gate_fn = gate_mapping.get(request.gate_name)
                if gate_fn:
                    cg_res = gate_fn()
                    if cg_res.blocked:
                        from bist_signal_bot.governance.models import GovernanceFinding, GovernanceDecision
                        if findings is None:
                            findings = []
                        findings.append(GovernanceFinding(
                            finding_id=f"cfg_{uuid.uuid4().hex[:8]}",
                            domain=request.domains[0],
                            status=GovernanceStatus.BLOCKED,
                            decision=GovernanceDecision.BLOCK,
                            title="Config Registry Blocked",
                            message=f"Blocked by config registry: {cg_res.warnings}",
                            rule_id="config_registry_gate"
                        ))
            except Exception as e:
                logger.warning(f"Config registry gate integration failed: {e}")




        blocked = False
        warnings = []

        for finding in findings:
            if finding.decision == GovernanceDecision.BLOCK:
                blocked = True
            elif finding.decision == GovernanceDecision.WARN:
                warnings.append(finding.message)

        # Handle allow_warnings setting
        if not request.allow_warnings and warnings:
            blocked = True

        status = GovernanceStatus.BLOCKED if blocked else (GovernanceStatus.WARN if warnings else GovernanceStatus.PASS)
        decision = GovernanceDecision.BLOCK if blocked else GovernanceDecision.ALLOW

        elapsed = (datetime.utcnow() - start_time).total_seconds()

        return GovernanceGateResult(
            gate_id=f"gate_{uuid.uuid4().hex[:8]}",
            request=request,
            status=status,
            decision=decision,
            findings=findings,
            blocked=blocked,
            warnings=warnings,
            elapsed_seconds=elapsed
        )

    def runtime_gate(self, payload: dict[str, Any]) -> GovernanceGateResult:
        request = GovernanceGateRequest(
            gate_name="runtime_gate",
            domains=[GovernanceDomain.RUNTIME, GovernanceDomain.REAL_ORDER_SAFETY],
            payload=payload,
        )
        return self.run_gate(request)

    def release_gate(self, payload: dict[str, Any]) -> GovernanceGateResult:
        request = GovernanceGateRequest(
            gate_name="release_gate",
            domains=[GovernanceDomain.RELEASE_READINESS],
            payload=payload,
        )
        return self.run_gate(request)

    def research_lab_gate(self, payload: dict[str, Any]) -> GovernanceGateResult:
        request = GovernanceGateRequest(
            gate_name="research_lab_gate",
            domains=[GovernanceDomain.RESEARCH_LAB, GovernanceDomain.REAL_ORDER_SAFETY],
            payload=payload,
        )
        return self.run_gate(request)

    def maintenance_gate(self, payload: dict[str, Any]) -> GovernanceGateResult:
        request = GovernanceGateRequest(
            gate_name="maintenance_gate",
            domains=[GovernanceDomain.BACKUP_RESTORE, GovernanceDomain.SECRET_HYGIENE],
            payload=payload,
        )
        return self.run_gate(request)

    def report_gate(self, payload: dict[str, Any]) -> GovernanceGateResult:
        request = GovernanceGateRequest(
            gate_name="report_gate",
            domains=[GovernanceDomain.REPORTS, GovernanceDomain.FINANCIAL_CLAIMS],
            payload=payload,
        )
        return self.run_gate(request)

    def check_whatif_output(self, content: str) -> dict[str, Any]:
        unsafe = ["investment advice", "guaranteed", "sure profit", "live order sent"]
        for u in unsafe:
            if u.lower() in content.lower():
                return {"status": "BLOCK", "reason": f"Unsafe what-if claim: {u}"}
        return {"status": "PASS"}
