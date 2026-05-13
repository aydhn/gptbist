import pytest
from bist_signal_bot.app.runtime_app import create_runtime_orchestrator, create_runtime_pipeline_config_from_settings
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.runtime.models import RuntimePipelineStatus, RuntimeTrigger

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
    config.strategy_name = "test"

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
    config.strategy_name = "test"

    res = orchestrator.dry_run(config)
    assert res.trigger == RuntimeTrigger.TEST
    assert res.config.dry_run is True
