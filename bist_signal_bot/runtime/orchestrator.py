import uuid
import logging
from datetime import datetime
from typing import Optional, Any, Dict, List

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import RuntimeValidationError, RuntimeLockError
from bist_signal_bot.runtime.models import (
    RuntimePipelineConfig, RuntimePipelineResult, RuntimeTrigger, RuntimePipelineStatus,
    RuntimeJobType, RuntimeJobConfig, RuntimeState, RuntimeJobResult, SessionPolicy
)
from bist_signal_bot.runtime.locks import RuntimeLockManager
from bist_signal_bot.runtime.state import RuntimeStateStore
from bist_signal_bot.runtime.jobs import RuntimeJobRunner
from bist_signal_bot.runtime.pipelines import RuntimePipelineBuilder
from bist_signal_bot.runtime.storage import RuntimeReportStore
from bist_signal_bot.security.preflight import SecurityPreflightRunner
from bist_signal_bot.security.kill_switch import KillSwitchManager
from bist_signal_bot.security.models import KillSwitchScope
from bist_signal_bot.core.exceptions import KillSwitchActiveError, SecurityPreflightError
from bist_signal_bot.storage.paths import get_data_dir

# For auditing, we normally import from core.audit, handled inside methods
class RuntimeOrchestrator:
    def __init__(
        self,
        security_preflight: Optional[SecurityPreflightRunner] = None,
        kill_switch: Optional[KillSwitchManager] = None,
        scanner_engine: Optional[Any] = None,
        paper_engine: Optional[Any] = None,
        regime_engine: Optional[Any] = None,
        ml_inference_engine: Optional[Any] = None,
        healthcheck_runner: Optional[Any] = None,
        lock_manager: Optional[RuntimeLockManager] = None,
        state_store: Optional[RuntimeStateStore] = None,
        job_runner: Optional[RuntimeJobRunner] = None,
        report_store: Optional[RuntimeReportStore] = None,
        notifier: Optional[Any] = None,
        settings: Optional[Settings] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)

        self.scanner_engine = scanner_engine
        self.paper_engine = paper_engine
        self.regime_engine = regime_engine
        self.ml_inference_engine = ml_inference_engine
        self.healthcheck_runner = healthcheck_runner
        self.notifier = notifier

        self.lock_manager = lock_manager or RuntimeLockManager(self.settings)
        self.state_store = state_store or RuntimeStateStore(self.settings)
        self.job_runner = job_runner or RuntimeJobRunner(self.settings, self.logger)
        self.report_store = report_store or RuntimeReportStore(self.settings)
        self.kill_switch = kill_switch or KillSwitchManager(self.settings, get_data_dir(self.settings))
        self.security_preflight = security_preflight or SecurityPreflightRunner(self.settings, kill_switch=self.kill_switch)

    def run_once(self, config: RuntimePipelineConfig, trigger: RuntimeTrigger = RuntimeTrigger.CLI) -> RuntimePipelineResult:
        security_preflight: Optional[SecurityPreflightRunner] = None,
        kill_switch: Optional[KillSwitchManager] = None,
        run_id = str(uuid.uuid4())
        started_at = datetime.utcnow()

        self.logger.info(f"Starting runtime pipeline. Run ID: {run_id}, Trigger: {trigger.value}")
        RuntimePipelineBuilder.validate_pipeline_config(config)

        result = RuntimePipelineResult(
            run_id=run_id,
            trigger=trigger,
            config=config,
            status=RuntimePipelineStatus.RUNNING,
            started_at=started_at
        )

        try:
            lock_id = self.lock_manager.acquire()
        except RuntimeLockError as e:
            self.logger.warning(f"Could not acquire lock: {e}")
            result.status = RuntimePipelineStatus.LOCKED
            result.finished_at = datetime.utcnow()
            return result

        self.state_store.mark_running(run_id, lock_id)

        try:
            # Session check fallback handled in job_runner
            in_session, session_msg = self.job_runner.should_run_in_session(config.session_policy, started_at)
            if not in_session:
                result.status = RuntimePipelineStatus.SKIPPED
                self.logger.info(session_msg)
                return result

            steps = RuntimePipelineBuilder.build_runtime_pipeline_steps(config)

            for step in steps:
                if step == RuntimeJobType.HEALTHCHECK:
                    if self.healthcheck_runner:
                        job_res = self.job_runner.run_job(step, lambda: self.healthcheck_runner.run() if hasattr(self.healthcheck_runner, "run") else {"status": "ok"})
                        result.job_results.append(job_res)
                        result.healthcheck_summary = job_res.summary

                elif step == RuntimeJobType.SIGNAL_SCAN:
                    if self.scanner_engine:
                        req = RuntimePipelineBuilder.build_scan_request(config)
                        # Normally would call self.scanner_engine.scan(req)
                        job_res = self.job_runner.run_job(step, lambda: self.scanner_engine.scan(req) if hasattr(self.scanner_engine, "scan") else {"mock_scan": True})
                        result.job_results.append(job_res)
                        result.scan_report_summary = job_res.summary

                elif step == RuntimeJobType.PAPER_RUN:
                    if self.paper_engine and config.use_paper and not config.dry_run:
                        # Normally would call self.paper_engine.run(req)
                        job_res = self.job_runner.run_job(step, lambda: self.paper_engine.run(config.strategy_name) if hasattr(self.paper_engine, "run") else {"mock_paper": True})
                        result.job_results.append(job_res)
                        result.paper_result_summary = job_res.summary

                elif step == RuntimeJobType.TELEGRAM_SUMMARY:
                    if self.notifier and config.send_telegram and not config.dry_run:
                        job_res = self.send_summary(result)
                        result.job_results.append(job_res)

            # Evaluate pipeline overall status
            failed_jobs = [j for j in result.job_results if j.status.value == "FAILED"]
            if failed_jobs:
                result.status = RuntimePipelineStatus.FAILED
            elif any(j.status.value == "PARTIAL_SUCCESS" for j in result.job_results):
                result.status = RuntimePipelineStatus.PARTIAL_SUCCESS
            else:
                result.status = RuntimePipelineStatus.SUCCESS

            if config.save_reports:
                formats = self.settings.RUNTIME_REPORT_FORMATS.split(",")
                paths = self.report_store.save_result(result, formats=formats)
                result.output_files = {k: str(v) for k, v in paths.items()}

        except Exception as e:
            self.logger.error(f"Pipeline failed unexpectedly: {e}")
            result.status = RuntimePipelineStatus.FAILED
            result.metadata["unexpected_error"] = str(e)

        finally:
            result.finished_at = datetime.utcnow()
            result.elapsed_seconds = (result.finished_at - result.started_at).total_seconds()
            self.state_store.mark_finished(result)
            self.lock_manager.release(lock_id)

            # Simulated Audit
            # audit_log(RUNTIME_RUN_COMPLETED, metadata={"run_id": result.run_id, "status": result.status.value})

        return result

    def dry_run(self, config: RuntimePipelineConfig) -> RuntimePipelineResult:
        security_preflight: Optional[SecurityPreflightRunner] = None,
        kill_switch: Optional[KillSwitchManager] = None,
        config.dry_run = True
        return self.run_once(config, RuntimeTrigger.TEST)

    def status(self) -> Dict[str, Any]:
        return self.state_store.load().summary()

    def reset_state(self, confirm: bool = False) -> RuntimeState:
        security_preflight: Optional[SecurityPreflightRunner] = None,
        kill_switch: Optional[KillSwitchManager] = None,
        if not confirm:
            raise RuntimeValidationError("You must confirm reset_state by passing confirm=True")
        return self.state_store.reset_state()

    def send_summary(self, result: RuntimePipelineResult) -> RuntimeJobResult:
        security_preflight: Optional[SecurityPreflightRunner] = None,
        kill_switch: Optional[KillSwitchManager] = None,
        def send_func():
            from bist_signal_bot.notifications.formatter import format_runtime_pipeline_result
            msg = format_runtime_pipeline_result(result)
            if self.notifier and hasattr(self.notifier, "send_message"):
                self.notifier.send_message(msg)
            return {"sent": bool(self.notifier)}

        return self.job_runner.run_job(RuntimeJobType.TELEGRAM_SUMMARY, send_func)

    def build_default_pipeline_config(self) -> RuntimePipelineConfig:
        return RuntimePipelineConfig(
            strategy_name=self.settings.RUNTIME_DEFAULT_STRATEGY,
            source=self.settings.RUNTIME_DEFAULT_SOURCE,
            top_n=self.settings.RUNTIME_DEFAULT_TOP_N,
            universe_mode=self.settings.RUNTIME_UNIVERSE_MODE,
            use_trade_risk=self.settings.RUNTIME_USE_TRADE_RISK,
            use_portfolio_risk=self.settings.RUNTIME_USE_PORTFOLIO_RISK,
            use_ml_filter=self.settings.RUNTIME_USE_ML_FILTER,
            use_regime_filter=self.settings.RUNTIME_USE_REGIME_FILTER,
            use_paper=self.settings.RUNTIME_USE_PAPER,
            send_telegram=self.settings.RUNTIME_SEND_TELEGRAM,
            session_policy=SessionPolicy(self.settings.RUNTIME_SESSION_POLICY)
        )

    def run_quality_preflight(self) -> bool:
        """Run optional quality smoke tests before runtime starts."""
        if not getattr(self.settings, "RUNTIME_QUALITY_PREFLIGHT_ENABLED", False):
            return True

        try:
            from bist_signal_bot.app.quality_app import create_quality_gate_runner, create_quality_config_from_settings
            from bist_signal_bot.quality.models import QualitySuite

            self.logger.info("Running optional runtime quality preflight...")
            runner = create_quality_gate_runner(self.settings)
            config = create_quality_config_from_settings(self.settings)

            suite_str = getattr(self.settings, "RUNTIME_QUALITY_PREFLIGHT_SUITE", "SMOKE")
            try:
                config.suite = QualitySuite(suite_str)
            except ValueError:
                config.suite = QualitySuite.SMOKE

            result = runner.run(config)

            if not result.passed():
                self.logger.error(f"Quality preflight failed with status {result.status.value}. Runtime will not start.")
                return False

            self.logger.info("Quality preflight passed.")
            return True
        except Exception as e:
            self.logger.error(f"Error during quality preflight: {e}")
            return False
