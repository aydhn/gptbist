import pytest
from pathlib import Path
from bist_signal_bot.app.monte_carlo_app import create_monte_carlo_store
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.monte_carlo.models import MonteCarloResult, MonteCarloRequest, MonteCarloTarget, ResamplingMethod, MonteCarloStatus

def test_monte_carlo_storage(tmp_path: Path):
    settings = Settings()
    store = create_monte_carlo_store(settings, tmp_path)

    req = MonteCarloRequest("req", MonteCarloTarget.TRADES, ResamplingMethod.TRADE_SHUFFLE, 10, 42, 1000.0, 30.0)
    res = MonteCarloResult("mc1", req, MonteCarloStatus.PASS, 0.1, [], [], [])

    files = store.save_result(res)
    assert "result_json" in files
    assert files["result_json"].exists()

    loaded = store.load_result("mc1")
    assert loaded is not None
    assert loaded.monte_carlo_id == "mc1"

    recent = store.list_recent_results(10)
    assert len(recent) == 1
    assert recent[0]["monte_carlo_id"] == "mc1"
