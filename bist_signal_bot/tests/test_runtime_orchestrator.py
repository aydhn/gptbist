import pytest
from types import SimpleNamespace
from bist_signal_bot.app.runtime_app import create_runtime_orchestrator, create_runtime_pipeline_config_from_settings
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.runtime.models import RuntimePipelineStatus, RuntimeTrigger, RuntimeJobStatus
from bist_signal_bot.scanner.models import ScanStatus

def test_orchestrator_run_once(tmp_path):
    settings = Settings()
    # Mocking storage dirs to tmp_path
    orchestrator = create_runtime_orchestrator(settings)
    orchestrator.lock_manager.base_dir = tmp_path
    orchestrator.lock_manager.lock_file = tmp_path / "runtime.lock"
    orchestrator.state_store.base_dir = tmp_path
    orchestrator.state_store.state_file = tmp_path / "state.json"
    orchestrator.report_store.base_dir = tmp_path / "runs"

    config = create_runtime_pipeline_config_from_settings(settings)
    config.symbols = ["ASELS"]

    res = orchestrator.run_once(config, trigger=RuntimeTrigger.TEST)

    assert res.status == RuntimePipelineStatus.SUCCESS
    assert res.success_count() > 0
    assert not orchestrator.lock_manager.is_locked()

def test_orchestrator_dry_run(tmp_path):
    settings = Settings()
    orchestrator = create_runtime_orchestrator(settings)
    orchestrator.lock_manager.base_dir = tmp_path
    orchestrator.lock_manager.lock_file = tmp_path / "runtime.lock"
    orchestrator.state_store.base_dir = tmp_path
    orchestrator.state_store.state_file = tmp_path / "state.json"
    orchestrator.report_store.base_dir = tmp_path / "runs"

    config = create_runtime_pipeline_config_from_settings(settings)
    config.symbols = ["ASELS"]

    res = orchestrator.dry_run(config)
    assert res.trigger == RuntimeTrigger.TEST
    assert res.config.dry_run is True

def test_failed_scan_cannot_produce_success_pipeline():
    class FailedScanner:
        data_service = None

        def scan(self, request):
            return SimpleNamespace(
                status=ScanStatus.FAILED,
                summary=lambda: {"status": "FAILED", "error": 2},
            )

    orchestrator = create_runtime_orchestrator(Settings())
    orchestrator.scanner_engine = FailedScanner()
    config = create_runtime_pipeline_config_from_settings(Settings())
    config.symbols = ["ASELS"]
    config.use_regime_filter = False

    result = SimpleNamespace(
        job_results=[],
        healthcheck_summary=None,
        scan_report_summary=None,
        paper_result_summary=None,
        regime_summary=None,
        ml_summary=None,
        metadata={},
        status=RuntimePipelineStatus.RUNNING,
    )
    orchestrator._execute_pipeline_steps(config, result)

    scan_job = next(j for j in result.job_results if j.job_type.value == "SIGNAL_SCAN")
    assert scan_job.status == RuntimeJobStatus.FAILED
    assert result.status == RuntimePipelineStatus.FAILED
