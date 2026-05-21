import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.governance.models import (
    GovernanceDecision,
    GovernanceDomain,
    GovernanceFinding,
    GovernancePolicy,
    GovernanceRule,
    GovernanceRuleType,
    GovernanceSeverity,
    GovernanceStatus,
)


class GovernanceRuleEvaluator:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings

    def finding_from_rule(
        self, rule: GovernanceRule, status: GovernanceStatus, message: str, evidence_refs: list[str]
    ) -> GovernanceFinding:
        decision = GovernanceDecision.ALLOW
        if status in (GovernanceStatus.FAIL, GovernanceStatus.BLOCKED):
            decision = GovernanceDecision.BLOCK if rule.blocking else GovernanceDecision.WARN
        elif status == GovernanceStatus.WARN:
            decision = GovernanceDecision.WARN

        return GovernanceFinding(
            finding_id=f"fnd_{uuid.uuid4().hex[:8]}",
            rule_id=rule.rule_id,
            domain=rule.domain,
            severity=rule.severity,
            status=status,
            decision=decision,
            title=f"Rule: {rule.name}",
            message=message,
            evidence_refs=evidence_refs,
            remediation=rule.remediation,
            created_at=datetime.utcnow(),
            metadata={"rule_type": rule.rule_type.value},
        )

    def evaluate_payload(
        self, payload: dict[str, Any], policy: GovernancePolicy, domains: list[GovernanceDomain] | None = None
    ) -> list[GovernanceFinding]:
        findings = []
        for rule in policy.rules:
            if not rule.enabled:
                # Disabled blocking rules generate a warning internally,
                # but we don't necessarily want to flood the findings for disabled rules
                # unless they are blocking and we are trying to run them.
                if rule.blocking:
                    findings.append(
                        self.finding_from_rule(
                            rule,
                            GovernanceStatus.WARN,
                            f"Blocking rule '{rule.name}' is disabled.",
                            []
                        )
                    )
                continue

            if domains and rule.domain not in domains:
                continue

            if rule.rule_type == GovernanceRuleType.CONFIRM_REQUIRED:
                expected_setting = rule.expected_setting
                if expected_setting in payload:
                    val = payload.get(expected_setting)
                    if val != rule.expected_value:
                        findings.append(
                            self.finding_from_rule(
                                rule,
                                GovernanceStatus.FAIL,
                                f"Required confirmation '{expected_setting}' not provided.",
                                [str(payload)]
                            )
                        )
                else:
                    findings.append(
                        self.finding_from_rule(
                            rule,
                            GovernanceStatus.FAIL,
                            f"Required field '{expected_setting}' is missing.",
                            [str(payload)]
                        )
                    )
        return findings

    def evaluate_text(self, text: str, policy: GovernancePolicy) -> list[GovernanceFinding]:
        findings = []
        if not text:
            return findings

        for rule in policy.rules:
            if not rule.enabled:
                continue

            if rule.rule_type == GovernanceRuleType.REQUIRED_DISCLAIMER:
                if rule.expected_setting and rule.expected_setting.lower() not in text.lower():
                    status = GovernanceStatus.FAIL if rule.blocking else GovernanceStatus.WARN
                    findings.append(
                        self.finding_from_rule(
                            rule,
                            status,
                            f"Missing required disclaimer: {rule.expected_setting}",
                            []
                        )
                    )

            elif rule.rule_type == GovernanceRuleType.FORBIDDEN_PATTERN:
                if rule.pattern:
                    match = re.search(rule.pattern, text)
                    if match:
                        findings.append(
                            self.finding_from_rule(
                                rule,
                                GovernanceStatus.BLOCKED if rule.blocking else GovernanceStatus.WARN,
                                f"Forbidden pattern detected: {match.group(0)}",
                                []
                            )
                        )

            elif rule.rule_type == GovernanceRuleType.SECRET_SCAN:
                # Basic mock check for typical token patterns in text
                secret_pattern = r"(?i)(token|secret|password|api_key|apikey)[\s=:]+[\"']?[A-Za-z0-9\-_]{20,}[\"']?"
                match = re.search(secret_pattern, text)
                if match:
                    findings.append(
                        self.finding_from_rule(
                            rule,
                            GovernanceStatus.BLOCKED,
                            "Potential secret leak detected in text.",
                            []
                        )
                    )

        return findings

    def evaluate_settings(self, settings: Settings, policy: GovernancePolicy) -> list[GovernanceFinding]:
        findings = []
        for rule in policy.rules:
            if not rule.enabled:
                continue

            if rule.rule_type == GovernanceRuleType.REQUIRED_SETTING:
                if rule.expected_setting and hasattr(settings, rule.expected_setting):
                    val = getattr(settings, rule.expected_setting)
                    if val != rule.expected_value:
                        findings.append(
                            self.finding_from_rule(
                                rule,
                                GovernanceStatus.BLOCKED if rule.blocking else GovernanceStatus.WARN,
                                f"Setting '{rule.expected_setting}' has value '{val}' (expected: '{rule.expected_value}').",
                                []
                            )
                        )
        return findings

    def evaluate_paths(self, paths: list[Path], policy: GovernancePolicy) -> list[GovernanceFinding]:
        findings = []
        for rule in policy.rules:
            if not rule.enabled:
                continue

            if rule.rule_type == GovernanceRuleType.PATH_SAFETY:
                # E.g., ensure paths are within allowed data dir
                pass # Extensible

        return findings

    def evaluate_audit_event(self, event: dict[str, Any], policy: GovernancePolicy) -> list[GovernanceFinding]:
        findings = []
        # Basic check to see if an event has a forbidden pattern in its message or details
        text_content = json.dumps(event)
        findings.extend(self.evaluate_text(text_content, policy))
        return findings
