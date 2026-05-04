import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck
from bist_signal_bot.config.settings import Settings

def test_healthcheck_includes_backtest():
    settings = Settings()
    class MockStore:
        def exists(self): return True
        def get_universe_dir(self): return "mock"
        def get_universe_file_path(self): return "mock"
        def get_watchlists_dir(self): return "mock"
        def get_snapshots_dir(self): return "mock"

    class MockUniverse:
        def count(self, active_only): return 1

    class MockSessionService:
        class MockCalendar:
            manual_holidays = []
        calendar = MockCalendar()

    class MockSessionStatus:
        timezone = "Europe/Istanbul"
        day_type = type('obj', (object,), {'value': 'REGULAR'})()
        is_trading_day = True
        is_market_open = True
        next_trading_day = None
        previous_trading_day = None

    import bist_signal_bot.app.healthcheck as hc
    hc.store = MockStore()
    hc.universe = MockUniverse()
    hc.session_service = MockSessionService()
    hc.session_status = MockSessionStatus()

    status = run_healthcheck()

    assert "backtest_engine" in status
    assert "enabled" in status["backtest_engine"]
    assert "initial_capital" in status["backtest_engine"]
    assert status["backtest_engine"]["engine_instantiable"] is True
