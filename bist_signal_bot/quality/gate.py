import logging
import time
import uuid
from datetime import datetime
from typing import Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.quality.models import (
    QualityTool,
    QualityRunConfig, QualityRunResult, QualityCheckResult,
    QualityCheckStatus, QualitySuite, QualityGateLevel,
    TestRunSummary, CoverageSummary, StaticAnalysisSummary
)
from bist_signal_bot.quality.test_runner import QualityTestRunner
from bist_signal_bot.quality.coverage import CoverageRunner
from bist_signal_bot.quality.static_analysis import StaticAnalysisRunner
from bist_signal_bot.quality.type_checking import TypeCheckRunner
from bist_signal_bot.quality.import_checks import ImportCheckRunner
from bist_signal_bot.quality.security_checks import QualitySecurityRunner
from bist_signal_bot.quality.regression import RegressionSmokeRunner
from bist_signal_bot.quality.storage import QualityReportStore
try:
    from bist_signal_bot.core.audit import AuditTrailManager, AuditEventType
except ImportError:
    class AuditTrailManager:
        def __init__(self, settings=None):
            pass
        def log_event(self, *args, **kwargs):
            pass

class QualityGateRunner:
    def __init__(self,
                 test_runner: Optional[QualityTestRunner] = None,
                 coverage_runner: Optional[CoverageRunner] = None,
                 static_runner: Optional[StaticAnalysisRunner] = None,
                 type_runner: Optional[TypeCheckRunner] = None,
                 import_runner: Optional[ImportCheckRunner] = None,
                 security_runner: Optional[QualitySecurityRunner] = None,
                 regression_runner: Optional[RegressionSmokeRunner] = None,
                 storage: Optional[QualityReportStore] = None,
                 settings: Optional[Settings] = None,
                 logger: Optional[logging.Logger] = None):

        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)

        self.test_runner = test_runner or QualityTestRunner(settings=self.settings, logger=self.logger)
        self.coverage_runner = coverage_runner or CoverageRunner()
        self.static_runner = static_runner or StaticAnalysisRunner()
        self.type_runner = type_runner or TypeCheckRunner()
        self.import_runner = import_runner or ImportCheckRunner()
        self.security_runner = security_runner or QualitySecurityRunner(settings=self.settings)
        self.regression_runner = regression_runner or RegressionSmokeRunner()
        self.storage = storage or QualityReportStore(settings=self.settings, logger=self.logger)
        self.audit = AuditTrailManager(settings=self.settings)

    def build_default_config(self, suite: Optional[QualitySuite] = None) -> QualityRunConfig:
        config = QualityRunConfig()

        if suite:
            config.suite = suite

        # Defaults based on Settings could be applied here
        # e.g., config.gate_level = getattr(self.settings, "QUALITY_GATE_LEVEL", QualityGateLevel.STANDARD)

        return config

    def run(self, config: Optional[QualityRunConfig] = None) -> QualityRunResult:
        run_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        start_time = time.time()

        cfg = config or self.build_default_config()

        self.logger.info(f"Starting Quality Gate Run {run_id} with suite {cfg.suite.value} at gate level {cfg.gate_level.value}")

        self.audit.log_event(
            event_type="QUALITY_RUN_STARTED", # using string literal for flexibility, in real implementation it should be an Enum
            entity_id=run_id,
            metadata={"suite": cfg.suite.value, "gate_level": cfg.gate_level.value}
        )

        checks = []
        test_summary = None
        coverage_summary = None
        static_summary = None

        # 1. Import Checks
        if cfg.run_import_checks:
            checks.extend(self.import_runner.run_import_checks())

        # 2. Security Checks
        if cfg.run_security_checks:
            checks.extend(self.security_runner.run_security_checks())

        # 3. Tests
        if cfg.run_tests:
            test_res = self.test_runner.run_pytest(cfg.suite, cfg.timeout_seconds)
            checks.append(test_res)
            # Basic parsing if needed
            test_summary = self.test_runner.parse_pytest_summary(
                test_res.stdout_tail or "", test_res.elapsed_seconds
            )

        # 4. Coverage
        if cfg.run_coverage:
            cov_res = self.coverage_runner.run_coverage(cfg.suite, cfg.coverage_threshold_pct, cfg.timeout_seconds)
            checks.append(cov_res)
            coverage_summary = self.coverage_runner.parse_coverage_output(
                cov_res.stdout_tail or "", cfg.coverage_threshold_pct
            )

        # 5. Static Analysis
        if cfg.run_static:
            ruff_res = self.static_runner.run_ruff()
            black_res = self.static_runner.run_black_check()
            checks.extend([ruff_res, black_res])
            static_summary = StaticAnalysisSummary(
                ruff_status=ruff_res.status,
                black_status=black_res.status
            )

        # 6. Type Checking
        if cfg.run_type_check:
            mypy_res = self.type_runner.run_mypy()
            checks.append(mypy_res)
            if static_summary:
                static_summary.mypy_status = mypy_res.status
            else:
                static_summary = StaticAnalysisSummary(mypy_status=mypy_res.status)

        # 7. Regression Smoke
        regression_cmds = []
        if cfg.run_regression_smoke:
            regression_cmds = self.regression_runner.default_commands()
            checks.extend(self.regression_runner.run_smoke_commands(regression_cmds))

        # 8. Evaluate Gate
        overall_status = self.evaluate_gate(checks, cfg)

        elapsed = time.time() - start_time

        result = QualityRunResult(
            run_id=run_id,
            config=cfg,
            status=overall_status,
            checks=checks,
            test_summary=test_summary,
            coverage_summary=coverage_summary,
            static_summary=static_summary,
            regression_commands=regression_cmds,
            started_at=started_at,
            finished_at=datetime.utcnow(),
            elapsed_seconds=elapsed
        )

        # 9. Storage
        if cfg.save_report:
            try:
                self.storage.save_result(result)
                self.audit.log_event(
                     event_type="QUALITY_REPORT_SAVED",
                     entity_id=run_id,
                     metadata={"output_files": result.output_files}
                 )
            except Exception as e:
                self.logger.error(f"Failed to save quality report: {e}")

        # 10. Audit result
        event_type = "QUALITY_RUN_COMPLETED" if result.passed() else "QUALITY_RUN_FAILED"
        self.audit.log_event(
             event_type=event_type,
             entity_id=run_id,
             metadata={
                 "status": result.status.value,
                 "failed_count": len(result.failed_checks()),
                 "elapsed_seconds": elapsed,
                 "no_real_order_sent": True
             }
         )

        return result

    def evaluate_gate(self, checks: list[QualityCheckResult], config: QualityRunConfig) -> QualityCheckStatus:
        if not checks:
            return QualityCheckStatus.PASS
        statuses = [c.status for c in checks]

        if QualityCheckStatus.ERROR in statuses:
            return QualityCheckStatus.ERROR

        if QualityCheckStatus.FAIL in statuses:
            return QualityCheckStatus.FAIL

        if QualityCheckStatus.WARN in statuses:
            if config.fail_on_warning:
                return QualityCheckStatus.FAIL
            return QualityCheckStatus.WARN

        # Release Gate Enforcement
        if config.gate_level == QualityGateLevel.RELEASE:
            tools_run = {c.tool for c in checks}
            # For RELEASE, we enforce these runs happened and passed (or were warned and warning is allowed)
            if config.run_coverage:
                 cov_checks = [c for c in checks if c.tool == QualityTool.COVERAGE]
                 if not cov_checks or cov_checks[0].status == QualityCheckStatus.SKIP:
                     return QualityCheckStatus.FAIL

            if config.run_security_checks:
                if QualityTool.SECURITY_GUARD not in tools_run:
                    return QualityCheckStatus.FAIL

            if config.run_regression_smoke:
                 if QualityTool.REGRESSION_SMOKE not in tools_run:
                     return QualityCheckStatus.FAIL

            if config.run_import_checks:
                 if QualityTool.IMPORT_CHECK not in tools_run:
                     return QualityCheckStatus.FAIL

        # Strict Gate Enforcement
        if config.gate_level == QualityGateLevel.STRICT:
            if QualityCheckStatus.SKIP in statuses:
                 # Check if skipping static analysis tools in strict mode
                 skip_tools = [c.tool for c in checks if c.status == QualityCheckStatus.SKIP]
                 if any(t in [QualityTool.MYPY, QualityTool.RUFF, QualityTool.BLACK] for t in skip_tools):
                     return QualityCheckStatus.WARN # or FAIL based on precise requirements

        # All passed or skipped (and relaxed)
        # Scenario integration check
        if getattr(config, "run_regression_smoke", False):
            for check in checks:
                if check.check_type == QualityCheckType.REGRESSION_SMOKE:
                     if isinstance(check.details, dict) and check.details.get("scenario_smoke") == "FAILED":
                         return QualityCheckStatus.FAIL
        return QualityCheckStatus.PASS
