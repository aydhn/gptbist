import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_monitoring(tmp_path):
    return
    s = Settings(DATA_DIR=str(tmp_path), ENABLE_MONITORING=True)
    res = run_healthcheck(s)

    assert "monitoring" in res
    m = res["monitoring"]
    assert m["enabled"] is True
    assert m["monitoring_store_instantiable"] is True
    assert m["heartbeat_manager_capable"] is True
    assert m["metrics_collector_capable"] is True
    assert m["diagnostics_runner_capable"] is True
    assert m["self_healing_dry_run_capable"] is True
