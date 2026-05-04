import pytest
from datetime import datetime, UTC
from bist_signal_bot.backtesting.models import BacktestFill
from bist_signal_bot.costs.models import OrderSide
from bist_signal_bot.signals.models import SignalDirection
from bist_signal_bot.backtesting.portfolio import BacktestPortfolio, BacktestPosition
from bist_signal_bot.core.exceptions import PortfolioAccountingError

def test_portfolio_initialization():
    pf = BacktestPortfolio(initial_capital=10000.0)
    assert pf.cash == 10000.0
    assert not pf.positions

def test_portfolio_open_long():
    pf = BacktestPortfolio(initial_capital=10000.0)
    fill = BacktestFill(
        symbol="ASELS",
        side=OrderSide.BUY,
        quantity=100.0,
        price=50.0,
        effective_price=50.1,
        gross_notional=5000.0,
        total_cost=10.0,
        total_cost_bps=20.0,
        filled_at=datetime.now(UTC),
        order_id="1"
    )

    trade = pf.open_long("ASELS", 100.0, fill, "TEST")
    assert pf.cash == 10000.0 - 5010.0
    assert "ASELS" in pf.positions
    assert trade.quantity == 100.0
    assert not trade.is_closed()

def test_portfolio_close_position():
    pf = BacktestPortfolio(initial_capital=10000.0)
    fill_buy = BacktestFill(
        symbol="ASELS", side=OrderSide.BUY, quantity=100.0, price=50.0, effective_price=50.0,
        gross_notional=5000.0, total_cost=0.0, total_cost_bps=0.0, filled_at=datetime.now(UTC), order_id="1"
    )
    pf.open_long("ASELS", 100.0, fill_buy, "TEST")

    fill_sell = BacktestFill(
        symbol="ASELS", side=OrderSide.SELL, quantity=100.0, price=60.0, effective_price=60.0,
        gross_notional=6000.0, total_cost=0.0, total_cost_bps=0.0, filled_at=datetime.now(UTC), order_id="2"
    )
    trade = pf.close_position("ASELS", fill_sell, "TEST")
    assert pf.cash == 11000.0 # 5000 remaining + 6000 proceeds
    assert "ASELS" not in pf.positions
    assert trade.is_closed()
    assert trade.net_pnl == 1000.0

def test_portfolio_mark_to_market():
    pf = BacktestPortfolio(initial_capital=10000.0)
    fill_buy = BacktestFill(
        symbol="ASELS", side=OrderSide.BUY, quantity=100.0, price=50.0, effective_price=50.0,
        gross_notional=5000.0, total_cost=0.0, total_cost_bps=0.0, filled_at=datetime.now(UTC), order_id="1"
    )
    pf.open_long("ASELS", 100.0, fill_buy, "TEST")

    snap = pf.mark_to_market(datetime.now(UTC), {"ASELS": 55.0})
    assert snap.cash == 5000.0
    assert snap.position_value == 5500.0
    assert snap.equity == 10500.0

def test_portfolio_insufficient_cash():
    pf = BacktestPortfolio(initial_capital=1000.0)
    fill = BacktestFill(
        symbol="ASELS", side=OrderSide.BUY, quantity=100.0, price=50.0, effective_price=50.1,
        gross_notional=5000.0, total_cost=10.0, total_cost_bps=20.0, filled_at=datetime.now(UTC), order_id="1"
    )
    with pytest.raises(PortfolioAccountingError, match="Insufficient cash"):
        pf.open_long("ASELS", 100.0, fill, "TEST")
