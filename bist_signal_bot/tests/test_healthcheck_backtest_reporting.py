from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_backtest_reporting():
    status = run_healthcheck(Settings())
    assert "backtest_reporting" in status
    assert status["backtest_reporting"]["enabled"] is True
    assert "report_formats" in status["backtest_reporting"]
    assert status["backtest_reporting"]["analyzer_instantiable"] is True
    assert status["backtest_reporting"]["report_writer_instantiable"] is True
