import pytest
import pandas as pd
from bist_signal_bot.paper.engine import PaperTradingEngine
from bist_signal_bot.paper.ledger import PaperLedgerStore
from bist_signal_bot.strategies.engine import StrategyEngine
from bist_signal_bot.data.market_data import MarketDataService
from bist_signal_bot.paper.models import PaperRunRequest, PaperExecutionMode
from bist_signal_bot.config.settings import Settings

@pytest.fixture
def mock_engine(tmp_path):
    settings = Settings()
    ledger = PaperLedgerStore(settings, base_dir=tmp_path)
    strat = StrategyEngine(settings)
    data = MarketDataService(settings)
    return PaperTradingEngine(
        ledger_store=ledger,
        strategy_engine=strat,
        data_service=data,
        settings=settings
    )

def test_engine_init(mock_engine):
    # 29. PaperTradingEngine initialize_account çalışır.
    state = mock_engine.initialize_account("test_acc", 1500)
    assert state.account.account_id == "test_acc"
    assert state.account.cash == 1500

def test_engine_run_once(mock_engine):
    # 30. PaperTradingEngine run_once mock strategy ile çalışır.
    mock_engine.initialize_account("test_acc", 100000)

    req = PaperRunRequest(
        account_id="test_acc",
        symbols=["ASELS"],
        strategy_name="moving_average_trend",
        source="mock",
        timeframe="1D",
        execution_mode=PaperExecutionMode.LATEST_CLOSE_RESEARCH,
        use_trade_risk=False,
        use_portfolio_risk=False
    )

    res = mock_engine.run_once(req)
    assert res.status == "SUCCESS"
    # Depending on mock data, might generate signal or not. We just check it runs without crashing.

def test_engine_close_position(mock_engine):
    # 34. PaperTradingEngine close_position çalışır.
    state = mock_engine.initialize_account("test_acc", 100000)

    # We artificially open a position to test close
    from bist_signal_bot.paper.models import PaperPosition, PaperPositionSide
    import uuid
    from datetime import datetime, UTC
    pos = PaperPosition(
        position_id=str(uuid.uuid4()),
        account_id="test_acc",
        symbol="ASELS",
        side=PaperPositionSide.LONG,
        quantity=10,
        avg_entry_price=50.0,
        last_price=50.0,
        market_value=500.0,
        opened_at=datetime.now(UTC)
    )
    state.positions.append(pos)
    mock_engine.ledger_store.save(state)

    res = mock_engine.close_position("test_acc", "ASELS", manual_price=55.0)
    assert res.status == "SUCCESS"
    assert len(res.fills) == 1
    assert len(res.positions) == 0

def test_run_result_summary(mock_engine):
    # 35. PaperRunResult summary doğru count üretir.
    state = mock_engine.initialize_account("test_acc", 100000)
    req = PaperRunRequest(
        account_id="test_acc",
        symbols=["ASELS"],
        strategy_name="moving_average_trend",
        source="mock",
        timeframe="1D"
    )
    res = mock_engine.run_once(req)
    summary = res.summary()
    assert "account_id" in summary
    assert "signals_count" in summary
