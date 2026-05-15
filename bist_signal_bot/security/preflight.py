from typing import Any
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.security.models import KillSwitchScope, SecurityAuditReport
from bist_signal_bot.security.secrets import SecretHygieneScanner
from bist_signal_bot.security.forbidden_actions import ForbiddenActionGuard
from bist_signal_bot.security.claims_guard import UnsafeClaimGuard
from bist_signal_bot.security.kill_switch import KillSwitchManager
from bist_signal_bot.security.path_guard import PathGuard
from bist_signal_bot.security.config_audit import ConfigSecurityAuditor
from bist_signal_bot.core.exceptions import SecurityPreflightError

class SecurityPreflightRunner:
    """Runs a series of security and safety checks before operational execution."""

    def __init__(
        self,
        settings: Settings,
        secret_scanner: SecretHygieneScanner | None = None,
        forbidden_guard: ForbiddenActionGuard | None = None,
        claim_guard: UnsafeClaimGuard | None = None,
        kill_switch: KillSwitchManager | None = None,
        path_guard: PathGuard | None = None
    ):
        self.settings = settings
        self.secret_scanner = secret_scanner or SecretHygieneScanner()
        self.forbidden_guard = forbidden_guard or ForbiddenActionGuard()
        self.claim_guard = claim_guard or UnsafeClaimGuard()
        self.kill_switch = kill_switch
        self.path_guard = path_guard

    def run_runtime_preflight(self) -> SecurityAuditReport:
        if self.kill_switch and self.kill_switch.is_active(KillSwitchScope.RUNTIME):
            raise SecurityPreflightError("Kill switch is active for RUNTIME scope. Preflight aborted.")

        if getattr(self.settings, "SECURITY_CONFIG_AUDIT_ENABLED", True):
            auditor = ConfigSecurityAuditor(self.kill_switch)
            report = auditor.audit_settings(self.settings)

            if getattr(self.settings, "SECURITY_FAIL_ON_SECRET_LEAK", True):
                if report.secret_findings:
                    raise SecurityPreflightError(f"Security Preflight Failed: Found {len(report.secret_findings)} secret leaks in configuration.")
            return report
        return SecurityAuditReport(status="SKIP", overall_score=100.0)

    def run_notification_preflight(self, payload: Any) -> None:
        if not getattr(self.settings, "SECURITY_NOTIFICATION_PREFLIGHT_ENABLED", True):
            return

        if self.kill_switch and self.kill_switch.is_active(KillSwitchScope.TELEGRAM):
            raise SecurityPreflightError("Kill switch is active for TELEGRAM scope. Notification blocked.")

        if getattr(self.settings, "SECURITY_FAIL_ON_SECRET_LEAK", True):
            self.secret_scanner.validate_no_secret_leak(payload, context="Notification Payload")

    def run_report_preflight(self, payload: Any) -> None:
        if not getattr(self.settings, "SECURITY_REPORT_PREFLIGHT_ENABLED", True):
            return

        if getattr(self.settings, "SECURITY_FAIL_ON_SECRET_LEAK", True):
            self.secret_scanner.validate_no_secret_leak(payload, context="Report Payload")

        if getattr(self.settings, "SECURITY_BLOCK_UNSAFE_CLAIMS", True):
             # Deep validation
             self.claim_guard.validate_payload(payload)

    def run_model_load_preflight(self, path: Path) -> None:
        if not getattr(self.settings, "SECURITY_MODEL_LOAD_PREFLIGHT_ENABLED", True):
            return

        if self.kill_switch and self.kill_switch.is_active(KillSwitchScope.ML):
            raise SecurityPreflightError("Kill switch is active for ML scope. Model loading blocked.")

        if self.path_guard:
            allow_external = getattr(self.settings, "SECURITY_ALLOW_EXTERNAL_MODEL_PATH", False)
            self.path_guard.validate_model_path(path, allow_external=allow_external)

    def run_cli_preflight(self, command_name: str, payload: dict[str, Any] | None = None) -> SecurityAuditReport:
        if not getattr(self.settings, "SECURITY_CLI_PREFLIGHT_ENABLED", True):
            return SecurityAuditReport(status="SKIP", overall_score=100.0)

        self.forbidden_guard.assert_no_html_scraping(command_name)
        self.forbidden_guard.assert_no_real_order_action(command_name)
        self.forbidden_guard.assert_no_paid_api(command_name)

        if payload and getattr(self.settings, "SECURITY_FAIL_ON_SECRET_LEAK", True):
            self.secret_scanner.validate_no_secret_leak(payload, context=f"CLI Command: {command_name}")

        return self.run_runtime_preflight()

    def run_optional_quality_checks(self):
        # Allow integration of quality reports if needed in preflight flow
        pass
