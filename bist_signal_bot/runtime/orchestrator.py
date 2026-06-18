import uuid
import logging
from datetime import datetime
from typing import Optional, Any, Dict, List

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import RuntimeValidationError, RuntimeLockError
from bist_signal_bot.runtime.models import (
    RuntimePipelineConfig, RuntimePipelineResult, RuntimeTrigger, RuntimePipelineStatus,
    RuntimeJobType, RuntimeJobConfig, RuntimeState, RuntimeJobResult, RuntimeJobStatus,
    SessionPolicy
)
from bist_signal_bot.runtime.locks import RuntimeLockManager
from bist_signal_bot.runtime.state import RuntimeStateStore
from bist_signal_bot.runtime.jobs import RuntimeJobRunner
from bist_signal_bot.runtime.pipelines import RuntimePipelineBuilder
from bist_signal_bot.scanner.models import ScanUniverseMode

from bist_signal_bot.reports.generator import ResearchReportGenerator
from bist_signal_bot.reports.digest import ReportDigestBuilder
from bist_signal_bot.reports.models import ReportType
from bist_signal_bot.app.reports_app import create_report_generator, create_digest_builder
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

        if getattr(self.settings, "SCENARIO_USE_SANDBOX", False) and getattr(self.settings, "BIST_BOT_ENV", "") == "scenario":
             # We shouldn't allow real telegram actions here
             pass

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
        if config.profile_runtime and getattr(self.settings, 'ENABLE_PERFORMANCE_PROFILING', False):
            from bist_signal_bot.app.performance_app import create_local_profiler
            from bist_signal_bot.performance.models import BenchmarkType
            profiler = create_local_profiler(self.settings)
            with profiler.profile_context("runtime_run_once", BenchmarkType.RUNTIME_RUN_ONCE) as perf_ctx:
                result = self._run_once_impl(config, trigger)
                # Attach performance to result after execution completes, but before yielding context
                if result:
                    pass

            # After context finishes, attach the saved profile info
            if "profile" in perf_ctx and perf_ctx["profile"]:
                profile = perf_ctx["profile"]
                result.performance_profile_id = profile.profile_id
                peak = next((m.value for m in profile.metrics if m.name == "Peak Memory Usage"), None)
                result.memory_peak_mb = peak
                if profile.spans:
                    slowest = max(profile.spans, key=lambda s: s.elapsed_seconds)
                    result.slowest_stage = slowest.name
            return result
        else:
            return self._run_once_impl(config, trigger)

    def _run_config_gate_integration(self, config: RuntimePipelineConfig, trigger: RuntimeTrigger) -> Optional[RuntimePipelineResult]:
        if getattr(config, "config_gate_before_run", False) or getattr(self.settings, "RUNTIME_CONFIG_GATE_BEFORE_RUN", False):
            try:
                from bist_signal_bot.app.config_registry_app import create_config_gate
                from bist_signal_bot.config_registry.models import RuntimeProfileType
                gate = create_config_gate(self.settings)

                profile_type = None
                if getattr(config, "runtime_profile", None):
                    profile_type = RuntimeProfileType(config.runtime_profile)

                gate_res = gate.runtime_gate(profile_type=profile_type)

                if gate_res.blocked:
                    self.logger.error("Config Gate blocked execution.")
                    result = RuntimePipelineResult(
                        run_id=f"run_{uuid.uuid4().hex[:8]}",
                        trigger=trigger,
                        config=config,
                        status=RuntimePipelineStatus.FAILED,
                        started_at=datetime.utcnow()
                    )
                    result.config_gate_status = gate_res.decision.value
                    result.metadata["config_gate_warnings"] = gate_res.warnings
                    return result
            except Exception as e:
                self.logger.error(f"Config gate error: {e}")
        return None

    def _check_data_freshness(self, config: RuntimePipelineConfig) -> None:
        if getattr(self.settings, "RUNTIME_REQUIRE_FRESH_DATA", False):
            try:
                from bist_signal_bot.data.data_service import MarketDataService
                from bist_signal_bot.data.mock_provider import MockMarketDataProvider
                ds = MarketDataService(provider=MockMarketDataProvider())
                fr = ds.freshness_report(config.symbols, config.timeframe, getattr(self.settings, "DATA_FRESHNESS_MAX_AGE_HOURS", 48))
                if fr.stale_symbols or fr.missing_symbols:
                    self.logger.warning(f"Runtime data freshness check failed. Stale: {fr.stale_symbols}, Missing: {fr.missing_symbols}")
            except Exception as e:
                self.logger.warning(f"Failed to check data freshness: {e}")

    def _apply_adaptive_config(self, config: RuntimePipelineConfig) -> None:
        if config and getattr(config, 'use_adaptive', False) and hasattr(self, 'adaptive_engine') and getattr(self, 'adaptive_engine', None):
            try:
                syms = config.symbols if hasattr(config, 'symbols') and config.symbols else []
                strats = [j.strategy_name for j in config.jobs if j.strategy_name]
                adaptive_config = getattr(self, 'adaptive_engine').build_runtime_strategy_config(syms, strats)
                if not config.metadata: config.metadata = {}
                config.metadata["adaptive_config"] = adaptive_config
            except Exception as e:
                self.logger.warning(f"Adaptive integration failed: {e}")

    def _execute_pipeline_steps(self, config: RuntimePipelineConfig, result: RuntimePipelineResult) -> None:
        steps = RuntimePipelineBuilder.build_runtime_pipeline_steps(config)
        fetched_data: dict = {}  # shared across steps: DATA_REFRESH -> REGIME_ANALYSIS

        for step in steps:
            if step == RuntimeJobType.HEALTHCHECK:
                if self.healthcheck_runner:
                    job_res = self.job_runner.run_job(step, lambda: self.healthcheck_runner.run() if hasattr(self.healthcheck_runner, "run") else {"status": "ok"})
                    result.job_results.append(job_res)
                    result.healthcheck_summary = job_res.summary

            elif step == RuntimeJobType.DATA_REFRESH:
                data_service = getattr(self.scanner_engine, "data_service", None)
                if data_service is not None and hasattr(data_service, "get_many_ohlcv"):
                    def _refresh():
                        from bist_signal_bot.data.symbol_universe import DEFAULT_SEED_SYMBOLS
                        from bist_signal_bot.data.models import Timeframe

                        raw = list(config.symbols) if getattr(config, "symbols", None) else list(DEFAULT_SEED_SYMBOLS)
                        syms = [getattr(s, "symbol", s) for s in raw]  # SymbolInfo -> ticker str
                        timeframe = Timeframe(config.timeframe)
                        requested = list(syms)
                        missing: list[str] = []

                        if config.source == "local":
                            store = getattr(data_service, "store", None)
                            provider = getattr(data_service, "provider", None)
                            vendor = getattr(provider, "vendor", None)
                            if store is None or vendor is None:
                                raise RuntimeValidationError("Local runtime data requires a configured local store.")
                            syms = [s for s in requested if store.exists(s, vendor, timeframe)]
                            missing = [s for s in requested if s not in syms]

                        if not syms:
                            raise RuntimeValidationError("No local market data is available for the runtime symbols.")

                        refreshed = data_service.get_many_ohlcv(
                            syms,
                            timeframe=timeframe,
                            refresh=False,
                            save=False,
                            allow_provider_fallback=False,
                        )
                        fetched_data.update(refreshed)
                        if not fetched_data:
                            raise RuntimeValidationError("Market data refresh returned no usable data.")
                        return {
                            "symbols_refreshed": len(fetched_data),
                            "symbols_requested": len(requested),
                            "symbols_missing": len(missing),
                            "network_used": False,
                        }
                    job_res = self.job_runner.run_job(step, _refresh)
                    result.job_results.append(job_res)

            elif step == RuntimeJobType.SIGNAL_SCAN:
                if self.scanner_engine:
                    req = RuntimePipelineBuilder.build_scan_request(config)
                    if fetched_data:
                        req.symbols = list(fetched_data)
                        req.universe_mode = ScanUniverseMode.SYMBOLS
                        req.source = "local_file"
                    scan_holder: dict[str, Any] = {}

                    def _scan():
                        report = self.scanner_engine.scan(req)
                        scan_holder["report"] = report
                        return report.summary() if hasattr(report, "summary") else {"output": str(report)}

                    job_res = self.job_runner.run_job(step, _scan)
                    report = scan_holder.get("report")
                    report_status = getattr(getattr(report, "status", None), "value", None)
                    if report_status == "FAILED":
                        job_res.status = RuntimeJobStatus.FAILED
                        job_res.issues.append("Signal scan failed for all requested symbols.")
                    elif report_status == "PARTIAL_SUCCESS":
                        job_res.status = RuntimeJobStatus.PARTIAL_SUCCESS
                        job_res.issues.append("Signal scan completed with symbol-level errors.")
                    result.job_results.append(job_res)
                    result.scan_report_summary = job_res.summary

            elif step == RuntimeJobType.REGIME_ANALYSIS:
                if self.regime_engine is not None and fetched_data:
                    def _regime():
                        dfs = {}
                        for sym, md in fetched_data.items():
                            df = getattr(md, "data", md)
                            if df is not None and not getattr(df, "empty", True):
                                dfs[sym] = df
                        if not dfs:
                            raise RuntimeValidationError("No usable data frames are available for regime analysis.")
                        batch = self.regime_engine.classify_many(dfs)
                        return batch.summary()
                    job_res = self.job_runner.run_job(step, _regime)
                    if job_res.status == RuntimeJobStatus.SUCCESS:
                        requested = int(job_res.summary.get("requested_count", 0))
                        succeeded = int(job_res.summary.get("success_count", 0))
                        failed = int(job_res.summary.get("failed_count", 0))
                        if requested > 0 and succeeded == 0:
                            job_res.status = RuntimeJobStatus.FAILED
                            job_res.issues.append("Regime analysis failed for all requested symbols.")
                        elif failed > 0:
                            job_res.status = RuntimeJobStatus.PARTIAL_SUCCESS
                            job_res.issues.append("Regime analysis completed with symbol-level errors.")
                    result.job_results.append(job_res)
                    result.regime_summary = job_res.summary

            elif step == RuntimeJobType.ML_INFERENCE:
                def _ml_inference():
                    if self.ml_inference_engine is None:
                        raise RuntimeValidationError("ML inference requires a configured registered model.")
                    if not config.ml_model_id:
                        raise RuntimeValidationError("ml_model_id is required for runtime ML inference.")

                    from bist_signal_bot.ml.inference.models import MLInferenceInput

                    inference_config = self.ml_inference_engine.build_default_config(config.ml_model_id)
                    inference_config.enabled = True
                    inputs = []
                    for symbol, market_data in fetched_data.items():
                        data = getattr(market_data, "data", market_data)
                        if data is not None and not getattr(data, "empty", True):
                            inputs.append(MLInferenceInput(
                                symbol=symbol,
                                data=data,
                                config=inference_config,
                                timeframe=config.timeframe,
                            ))
                    if not inputs:
                        raise RuntimeValidationError("No usable data is available for ML inference.")
                    return self.ml_inference_engine.predict_batch(inputs).summary()

                job_res = self.job_runner.run_job(step, _ml_inference)
                if job_res.status == RuntimeJobStatus.SUCCESS:
                    requested = int(job_res.summary.get("requested_count", 0))
                    errors = int(job_res.summary.get("error_count", 0))
                    if requested > 0 and errors == requested:
                        job_res.status = RuntimeJobStatus.FAILED
                        job_res.issues.append("ML inference failed for all requested symbols.")
                    elif errors > 0:
                        job_res.status = RuntimeJobStatus.PARTIAL_SUCCESS
                        job_res.issues.append("ML inference completed with symbol-level errors.")
                result.job_results.append(job_res)
                result.ml_summary = job_res.summary

            elif step == RuntimeJobType.PAPER_RUN:
                if self.paper_engine and getattr(config, 'use_paper', False) and not getattr(config, 'dry_run', False):
                    job_res = self.job_runner.run_job(step, lambda: self.paper_engine.run(getattr(config, 'strategy_name', '')) if hasattr(self.paper_engine, "run") else {"mock_paper": True})
                    result.job_results.append(job_res)
                    result.paper_result_summary = job_res.summary

            elif step == RuntimeJobType.TELEGRAM_SUMMARY:
                if self.notifier and getattr(config, 'send_telegram', False) and not getattr(config, 'dry_run', False):
                    job_res = self.send_summary(result)
                    result.job_results.append(job_res)

            elif step == RuntimeJobType.CLEANUP:
                result.metadata.setdefault("skipped_steps", []).append({
                    "step": RuntimeJobType.CLEANUP.value,
                    "reason": "No cleanup service is configured.",
                })

        failed_jobs = [j for j in result.job_results if j.status == RuntimeJobStatus.FAILED]
        if failed_jobs:
            result.status = RuntimePipelineStatus.FAILED
        elif any(j.status == RuntimeJobStatus.PARTIAL_SUCCESS for j in result.job_results):
            result.status = RuntimePipelineStatus.PARTIAL_SUCCESS
        else:
            result.status = RuntimePipelineStatus.SUCCESS

    def _integrate_portfolio_research(self, config: RuntimePipelineConfig, result: RuntimePipelineResult) -> None:
        if getattr(config, "build_research_portfolio", False) or getattr(self.settings, "RUNTIME_BUILD_RESEARCH_PORTFOLIO", False):
            try:
                from bist_signal_bot.app.portfolio_research_app import create_portfolio_research_engine
                from bist_signal_bot.portfolio_research.models import PortfolioResearchRequest, AllocationMethod

                engine = create_portfolio_research_engine(self.settings)

                method_str = getattr(config, "portfolio_allocation_method", None) or getattr(self.settings, "RUNTIME_PORTFOLIO_ALLOCATION_METHOD", "HYBRID")
                try:
                    method = AllocationMethod(method_str)
                except ValueError:
                    method = AllocationMethod.HYBRID

                req = PortfolioResearchRequest(
                    symbols=getattr(config, 'symbols', []),
                    allocation_method=method,
                    max_items=getattr(config, "portfolio_max_items", None) or getattr(self.settings, "RUNTIME_PORTFOLIO_MAX_ITEMS", 10),
                    save_snapshot=True,
                    source=getattr(config, "data_source", "local")
                )

                snapshot = engine.build_snapshot(req)

                result.metadata["portfolio_snapshot_id"] = snapshot.snapshot_id
                result.metadata["portfolio_item_count"] = snapshot.item_count
                result.metadata["portfolio_warnings"] = len(snapshot.warnings)
                self.logger.info(f"Built research portfolio snapshot: {snapshot.snapshot_id}")
            except Exception as e:
                self.logger.error(f"Failed to build research portfolio: {e}")
                result.metadata["portfolio_error"] = str(e)

    def _run_once_impl(self, config: RuntimePipelineConfig, trigger: RuntimeTrigger = RuntimeTrigger.CLI) -> RuntimePipelineResult:
        gate_result = self._run_config_gate_integration(config, trigger)
        if gate_result:
            return gate_result

        self._check_data_freshness(config)
        self._apply_adaptive_config(config)

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
            in_session, session_msg = self.job_runner.should_run_in_session(config.session_policy, started_at)
            if not in_session:
                result.status = RuntimePipelineStatus.SKIPPED
                self.logger.info(session_msg)
                return result

            self._execute_pipeline_steps(config, result)

            if getattr(config, 'save_reports', False):
                formats = getattr(self.settings, 'RUNTIME_REPORT_FORMATS', '').split(",")
                paths = self.report_store.save_result(result, formats=formats)
                result.output_files = {k: str(v) for k, v in paths.items()}

        except Exception as e:
            self.logger.error(f"Pipeline failed unexpectedly: {e}")
            result.status = RuntimePipelineStatus.FAILED
            result.metadata["unexpected_error"] = str(e)

        finally:
            result.finished_at = datetime.utcnow()
            result.elapsed_seconds = (result.finished_at - result.started_at).total_seconds()

            self._integrate_portfolio_research(config, result)

            self.state_store.mark_finished(result)
            self.lock_manager.release(lock_id)

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

# Add drift check
def run_drift_check_if_enabled(engine, settings):
    if settings.RUNTIME_RUN_DRIFT_CHECK:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Running optional drift check at the end of runtime pipeline...")
        from bist_signal_bot.drift.models import DriftAnalysisRequest
        try:
             res = engine.analyze(DriftAnalysisRequest(save_output=True))
             logger.info(f"Drift Check completed. Status: {res.status.value}")
        except Exception as e:
             logger.error(f"Failed to run drift check during runtime: {e}")

def maintenance_hook_before_heavy_research():
    from bist_signal_bot.config.settings import get_settings
    settings = get_settings()

    if getattr(settings, 'MAINTENANCE_DOCTOR_BEFORE_RUN', False):
         from bist_signal_bot.app.maintenance_app import create_maintenance_doctor
         doc = create_maintenance_doctor()
         doc.run_doctor() # Not halting, just logging / checking

    if getattr(settings, 'BACKUP_BEFORE_HEAVY_RESEARCH', False):
         # Typically just recommending or checking age, but could trigger backup
         pass

    def update_knowledge_index(self, settings: Any = None):
        try:
            from bist_signal_bot.app.knowledge_app import create_knowledge_indexer
            from bist_signal_bot.knowledge.models import KnowledgeIndexBuildRequest
            indexer = create_knowledge_indexer(settings)
            req = KnowledgeIndexBuildRequest(incremental=True, use_embeddings=False)
            indexer.build_index(req)
        except Exception:
            pass
    def run_whatif_analysis(self) -> dict[str, Any]:
        if not getattr(self.settings, "ENABLE_WHATIF_LAB", True):
            return {"status": "SKIPPED", "reason": "WhatIf disabled"}
        if not getattr(self.settings, "RUNTIME_RUN_WHATIF_ANALYSIS", False):
            return {"status": "SKIPPED", "reason": "Runtime whatif disabled"}

        try:
            from bist_signal_bot.app.whatif_app import create_whatif_engine
            engine = create_whatif_engine(self.settings)
            res = engine.run_default(source_type="runtime_orchestrator")
            return {"status": "SUCCESS", "run_id": res.run_id}
        except Exception as e:
            self.logger.error(f"Runtime whatif error: {e}")
            return {"status": "ERROR", "message": str(e)}
