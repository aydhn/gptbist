from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.security.models import (
    SecurityAuditReport, SecurityCheckResult, SecurityComponent,
    SecurityCheckStatus, SecurityLevel, SecretFinding, ForbiddenActionFinding
)
from bist_signal_bot.security.secrets import SecretHygieneScanner
from bist_signal_bot.security.kill_switch import KillSwitchManager
from pathlib import Path

class ConfigSecurityAuditor:
    """Audits the application configuration for security vulnerabilities and risks."""

    def __init__(self, kill_switch_manager: KillSwitchManager | None = None):
        self.kill_switch = kill_switch_manager

    def audit_settings(self, settings: Settings) -> SecurityAuditReport:
        checks = []
        warnings = []

        # 1. Kill Switch Check
        if self.kill_switch:
            ks_state = self.kill_switch.load_state()
            checks.append(SecurityCheckResult(
                check_name="kill_switch_status",
                component=SecurityComponent.CONFIG,
                status=SecurityCheckStatus.PASS,
                severity=SecurityLevel.LOW,
                message="Kill switch manager is available.",
                details={"active": ks_state.enabled, "scopes": [s.value for s in ks_state.scopes]}
            ))
        else:
            ks_state = None
            checks.append(SecurityCheckResult(
                check_name="kill_switch_status",
                component=SecurityComponent.CONFIG,
                status=SecurityCheckStatus.WARN,
                severity=SecurityLevel.HIGH,
                message="Kill switch manager is not available/configured.",
                recommendations=["Enable SECURITY_KILL_SWITCH_ENABLED in settings."]
            ))

        # 2. Secret Hygiene Check
        secret_findings = SecretHygieneScanner.scan_settings(settings)
        if secret_findings:
            checks.append(SecurityCheckResult(
                check_name="secret_hygiene",
                component=SecurityComponent.SECRETS,
                status=SecurityCheckStatus.FAIL,
                severity=SecurityLevel.STRICT,
                message=f"Found {len(secret_findings)} secret leaks in configuration.",
                recommendations=["Remove secrets from config/code. Use .env file securely."]
            ))
        else:
            checks.append(SecurityCheckResult(
                check_name="secret_hygiene",
                component=SecurityComponent.SECRETS,
                status=SecurityCheckStatus.PASS,
                severity=SecurityLevel.HIGH,
                message="No plain-text secrets found in loaded settings."
            ))

        # 3. Paper Trading Warnings
        if getattr(settings, "RUNTIME_USE_PAPER", False) and getattr(settings, "SECURITY_WARN_IF_PAPER_DEFAULT_ACTIVE", True):
            warnings.append("RUNTIME_USE_PAPER is active by default. Ensure this is intentional.")

        if getattr(settings, "SCANNER_ALLOW_PAPER_EXECUTION", False) and getattr(settings, "SECURITY_WARN_IF_SCANNER_PAPER_ENABLED", True):
            warnings.append("SCANNER_ALLOW_PAPER_EXECUTION is active. High risk of unattended mass paper orders.")

        # 4. Telegram Warning
        if getattr(settings, "RUNTIME_SEND_TELEGRAM", False) and getattr(settings, "SECURITY_WARN_IF_RUNTIME_TELEGRAM_ACTIVE", False):
            warnings.append("RUNTIME_SEND_TELEGRAM is active. Ensure notifications are secure.")

        # 5. External Models
        if getattr(settings, "SECURITY_ALLOW_EXTERNAL_MODEL_PATH", False):
            checks.append(SecurityCheckResult(
                check_name="external_model_paths",
                component=SecurityComponent.ML_MODEL_REGISTRY,
                status=SecurityCheckStatus.WARN,
                severity=SecurityLevel.HIGH,
                message="Loading ML models from external paths is allowed.",
                recommendations=["Set SECURITY_ALLOW_EXTERNAL_MODEL_PATH=False to enforce loading only from local secure paths."]
            ))
        else:
            checks.append(SecurityCheckResult(
                check_name="external_model_paths",
                component=SecurityComponent.ML_MODEL_REGISTRY,
                status=SecurityCheckStatus.PASS,
                severity=SecurityLevel.HIGH,
                message="External ML models blocked."
            ))

        score = self.score_checks(checks)
        status = SecurityCheckStatus.PASS
        if any(c.status == SecurityCheckStatus.FAIL for c in checks):
            status = SecurityCheckStatus.FAIL
        elif any(c.status == SecurityCheckStatus.WARN for c in checks):
            status = SecurityCheckStatus.WARN

        report = SecurityAuditReport(
            status=status,
            overall_score=score,
            checks=checks,
            secret_findings=secret_findings,
            forbidden_action_findings=[], # This is static analysis, handle via scan_source_text separately
            kill_switch_state=ks_state,
            warnings=warnings
        )
        report.metadata["recommendations"] = self.build_recommendations(report)
        return report

    def score_checks(self, checks: list[SecurityCheckResult]) -> float:
        if not checks:
            return 100.0

        total_weight = 0.0
        earned = 0.0

        weight_map = {
            SecurityLevel.LOW: 1.0,
            SecurityLevel.MEDIUM: 2.0,
            SecurityLevel.HIGH: 3.0,
            SecurityLevel.STRICT: 5.0
        }

        for check in checks:
            w = weight_map.get(check.severity, 1.0)
            total_weight += w
            if check.status == SecurityCheckStatus.PASS:
                earned += w
            elif check.status == SecurityCheckStatus.WARN:
                earned += w * 0.5

        return round((earned / total_weight) * 100.0, 2) if total_weight > 0 else 100.0

    def build_recommendations(self, report: SecurityAuditReport) -> list[str]:
        recs = []
        for check in report.checks:
            recs.extend(check.recommendations)
        if report.warnings:
            recs.extend(["Review and address all configuration warnings."])
        return list(set(recs))
