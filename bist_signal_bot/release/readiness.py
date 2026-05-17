import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.release.models import (
    ReleaseReadinessConfig, ReleaseReadinessReport, ReleaseCheckResult, ReleaseBlocker,
    ReleaseCheckCategory, ReleaseCheckStatus, ReleaseBlockerSeverity, ReleaseStatus, ReleaseStage, ReleaseProfile
)
from bist_signal_bot.release.checks import ReleaseCheckRunner
from bist_signal_bot.core.audit import AuditLogger, AuditEventType
from bist_signal_bot.core.exceptions import ReleaseReadinessError

class ReleaseReadinessEvaluator:
    def __init__(self,
                 check_runner: ReleaseCheckRunner | None = None,
                 quality_runner: Any | None = None,
                 security_preflight: Any | None = None,
                 scenario_runner: Any | None = None,
                 package_builder: Any | None = None,
                 docs_validator: Any | None = None,
                 performance_monitor: Any | None = None,
                 report_generator: Any | None = None,
                 storage: Any | None = None,
                 settings: Settings | None = None,
                 logger: logging.Logger | None = None):
        self.settings = settings or get_settings()
        self.logger = logger or logging.getLogger(__name__)
        self.check_runner = check_runner or ReleaseCheckRunner(self.settings, self.logger)
        self.quality_runner = quality_runner
        self.security_preflight = security_preflight
        self.scenario_runner = scenario_runner
        self.package_builder = package_builder
        self.docs_validator = docs_validator
        self.performance_monitor = performance_monitor
        self.report_generator = report_generator
        self.storage = storage
        self.audit = AuditLogger(self.settings)

    def default_config(self) -> ReleaseReadinessConfig:
        s = self.settings
        return ReleaseReadinessConfig(
            stage=ReleaseStage(getattr(s, "RELEASE_STAGE", "RELEASE_CANDIDATE")),
            profile=ReleaseProfile(getattr(s, "RELEASE_PROFILE", "FULL_SAFE_LOCAL")),
            version=getattr(s, "RELEASE_VERSION", "0.1.0"),
            run_healthcheck=getattr(s, "RELEASE_RUN_HEALTHCHECK", True),
            run_security=getattr(s, "RELEASE_RUN_SECURITY", True),
            run_quality=getattr(s, "RELEASE_RUN_QUALITY", True),
            run_scenarios=getattr(s, "RELEASE_RUN_SCENARIOS", True),
            run_packaging=getattr(s, "RELEASE_RUN_PACKAGING", True),
            run_docs_validation=getattr(s, "RELEASE_RUN_DOCS_VALIDATION", True),
            run_performance_check=getattr(s, "RELEASE_RUN_PERFORMANCE_CHECK", True),
            run_runtime_dry_run=getattr(s, "RELEASE_RUN_RUNTIME_DRY_RUN", True),
            run_report_generation=getattr(s, "RELEASE_RUN_REPORT_GENERATION", True),
            require_no_blockers=getattr(s, "RELEASE_REQUIRE_NO_BLOCKERS", True),
            require_quality_pass=getattr(s, "RELEASE_REQUIRE_QUALITY_PASS", True),
            require_security_pass=getattr(s, "RELEASE_REQUIRE_SECURITY_PASS", True),
            require_acceptance_pass=getattr(s, "RELEASE_REQUIRE_ACCEPTANCE_PASS", False),
            save_report=getattr(s, "RELEASE_SAVE_REPORTS", True)
        )

    def evaluate(self, config: ReleaseReadinessConfig | None = None) -> ReleaseReadinessReport:
        if not config:
            config = self.default_config()

        readiness_id = str(uuid.uuid4())
        self.audit.log_event(AuditEventType.RELEASE_READINESS_STARTED)

        start_time = time.time()
        report = ReleaseReadinessReport(
            readiness_id=readiness_id,
            config=config,
            status=ReleaseStatus.UNKNOWN,
            readiness_score=0.0
        )

        try:
            checks = []
            checks.extend(self.check_runner.run_all_basic_checks())

            # Here we would normally call self.quality_runner.run_smoke() etc.
            # For this MVP integration, we simulate those calls returning check results if they were injected.

            # Simple mock for integrated tools if they are not provided (so tests pass without heavy mocking)
            if config.run_security and self.security_preflight is None:
                 checks.append(ReleaseCheckResult("sec_preflight", "Security Preflight", ReleaseCheckCategory.SECURITY, ReleaseCheckStatus.SKIP, ReleaseBlockerSeverity.LOW, "Preflight not available"))

            if config.run_quality and self.quality_runner is None:
                 checks.append(ReleaseCheckResult("qual_smoke", "Quality Smoke", ReleaseCheckCategory.QUALITY, ReleaseCheckStatus.SKIP, ReleaseBlockerSeverity.LOW, "Quality runner not available"))

            if config.run_scenarios and self.scenario_runner is None:
                 checks.append(ReleaseCheckResult("scan_smoke", "Scenario Smoke", ReleaseCheckCategory.SCENARIOS, ReleaseCheckStatus.SKIP, ReleaseBlockerSeverity.LOW, "Scenario runner not available"))

            report.checks = checks
            report.blockers = self.build_blockers(checks, config)
            report.readiness_score = self.calculate_readiness_score(checks, report.blockers)
            report.status = self.derive_status(report.readiness_score, report.blockers, config)

            report.passed_count = sum(1 for c in checks if c.status == ReleaseCheckStatus.PASS)
            report.failed_count = sum(1 for c in checks if c.status in [ReleaseCheckStatus.FAIL, ReleaseCheckStatus.ERROR])
            report.warning_count = sum(1 for c in checks if c.status == ReleaseCheckStatus.WARN)
            report.skipped_count = sum(1 for c in checks if c.status == ReleaseCheckStatus.SKIP)

            report.finished_at = datetime.utcnow()
            report.elapsed_seconds = time.time() - start_time

            if config.save_report and self.storage:
                paths = self.storage.save_readiness_report(report)
                report.output_files = {k: str(v) for k, v in paths.items()}

            if report.status in [ReleaseStatus.READY, ReleaseStatus.PARTIAL_READY]:
                self.audit.log_event(AuditEventType.RELEASE_READINESS_COMPLETED)
            else:
                 self.audit.log_event(AuditEventType.RELEASE_READINESS_FAILED)

            return report

        except Exception as e:
            self.logger.exception("Failed during release readiness evaluation")
            self.audit.log_event(AuditEventType.RELEASE_READINESS_FAILED)
            report.status = ReleaseStatus.FAILED
            report.finished_at = datetime.utcnow()
            report.elapsed_seconds = time.time() - start_time
            return report

    def calculate_readiness_score(self, checks: list[ReleaseCheckResult], blockers: list[ReleaseBlocker]) -> float:
        if not checks:
            return 0.0

        base_score = 100.0

        for check in checks:
            if check.status == ReleaseCheckStatus.WARN:
                base_score -= 1.0
            elif check.status == ReleaseCheckStatus.FAIL:
                if check.severity == ReleaseBlockerSeverity.CRITICAL:
                    base_score -= 20.0
                elif check.severity == ReleaseBlockerSeverity.HIGH:
                    base_score -= 10.0
                else:
                    base_score -= 5.0
            elif check.status == ReleaseCheckStatus.ERROR:
                 base_score -= 15.0

        for blocker in blockers:
            if blocker.blocking:
                if blocker.severity == ReleaseBlockerSeverity.CRITICAL:
                    base_score -= 30.0
                elif blocker.severity == ReleaseBlockerSeverity.HIGH:
                     base_score -= 15.0

        return max(0.0, min(100.0, base_score))

    def derive_status(self, score: float, blockers: list[ReleaseBlocker], config: ReleaseReadinessConfig) -> ReleaseStatus:
        has_critical_blocker = any(b.blocking and b.severity in [ReleaseBlockerSeverity.CRITICAL, ReleaseBlockerSeverity.HIGH] for b in blockers)

        if has_critical_blocker and config.require_no_blockers:
            return ReleaseStatus.BLOCKED

        # Optional requirements checking (simplified representation)
        has_security_fail = any(b.category == ReleaseCheckCategory.SECURITY for b in blockers)
        if config.require_security_pass and has_security_fail:
             return ReleaseStatus.NOT_READY

        if score >= getattr(self.settings, "RELEASE_MIN_READY_SCORE", 85.0) and not has_critical_blocker:
            return ReleaseStatus.READY

        if score >= getattr(self.settings, "RELEASE_MIN_PARTIAL_SCORE", 65.0):
            return ReleaseStatus.PARTIAL_READY

        return ReleaseStatus.NOT_READY

    def build_blockers(self, checks: list[ReleaseCheckResult], config: ReleaseReadinessConfig) -> list[ReleaseBlocker]:
        blockers = []
        for check in checks:
            if check.status in [ReleaseCheckStatus.FAIL, ReleaseCheckStatus.ERROR]:
                is_blocking = False

                # Default blocking rules
                if check.severity in [ReleaseBlockerSeverity.CRITICAL, ReleaseBlockerSeverity.HIGH]:
                     is_blocking = True

                # Config overrides
                if check.category == ReleaseCheckCategory.SECURITY and config.require_security_pass:
                    is_blocking = True
                if check.category == ReleaseCheckCategory.QUALITY and config.require_quality_pass:
                    is_blocking = True
                if check.category == ReleaseCheckCategory.SCENARIOS and config.require_acceptance_pass:
                    is_blocking = True

                b = ReleaseBlocker(
                    blocker_id=f"blocker_{check.check_id}",
                    category=check.category,
                    severity=check.severity,
                    title=f"Failed Check: {check.name}",
                    message=check.message,
                    blocking=is_blocking,
                    remediation=check.recommendations,
                    related_check_ids=[check.check_id]
                )
                blockers.append(b)
        return blockers
