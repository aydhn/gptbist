from bist_signal_bot.portfolio.holdings import build_portfolio_state, update_holding_prices
from bist_signal_bot.portfolio.models import PortfolioHolding, PortfolioPositionSide
from datetime import datetime
from bist_signal_bot.portfolio.holdings import holding_from_dict, portfolio_state_from_backtest_snapshot
from bist_signal_bot.backtesting.models import PositionState

def test_build_portfolio_state():
    state = build_portfolio_state(equity=1000.0, cash=1000.0)
    assert state.equity == 1000.0
    assert state.cash == 1000.0
    assert len(state.holdings) == 0

def test_update_holding_prices():
    h1 = PortfolioHolding(symbol="ASELS", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=100.0, weight_pct=1.0)
    state = build_portfolio_state(equity=100.0, cash=0.0, holdings=[h1])

    new_state = update_holding_prices(state, {"ASELS": 12.0})
    assert new_state.holdings[0].last_price == 12.0
    assert new_state.holdings[0].market_value == 120.0
    assert new_state.holdings[0].unrealized_pnl == 20.0
    assert new_state.equity == 120.0

def test_build_portfolio_state_with_args():
    h1 = PortfolioHolding(symbol="ASELS", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=100.0, weight_pct=1.0)
    state = build_portfolio_state(equity=1000.0, cash=900.0, holdings=[h1], daily_signal_count=5)

    assert state.equity == 1000.0
    assert state.cash == 900.0
    assert len(state.holdings) == 1
    assert state.holdings[0].symbol == "ASELS"
    assert state.daily_signal_count == 5

def test_holding_from_dict():
    data = {
        "symbol": "THYAO",
        "side": PortfolioPositionSide.SHORT,
        "quantity": 5,
        "avg_price": 50.0,
        "market_value": 250.0,
        "weight_pct": 0.5
    }
    holding = holding_from_dict(data)
    assert holding.symbol == "THYAO"
    assert holding.side == PortfolioPositionSide.SHORT
    assert holding.quantity == 5

def test_update_holding_prices_short_and_missing():
    h1 = PortfolioHolding(symbol="THYAO", side=PortfolioPositionSide.SHORT, quantity=10, avg_price=50.0, market_value=500.0, weight_pct=0.5)
    h2 = PortfolioHolding(symbol="GARAN", side=PortfolioPositionSide.LONG, quantity=20, avg_price=10.0, market_value=200.0, weight_pct=0.2)
    state = build_portfolio_state(equity=1000.0, cash=300.0, holdings=[h1, h2])

    # Price for GARAN is missing, THYAO price drops to 40.0 (profit of 10 per share = 100)
    new_state = update_holding_prices(state, {"THYAO": 40.0})

    # THYAO updated
    assert new_state.holdings[0].last_price == 40.0
    assert new_state.holdings[0].market_value == 400.0
    assert new_state.holdings[0].unrealized_pnl == 100.0

    # GARAN not updated, retains old market value
    assert new_state.holdings[1].market_value == 200.0

    # New equity = cash (300) + THYAO (400) + GARAN (200) = 900
    assert new_state.equity == 900.0

class MockPosition:
    def __init__(self, symbol, state, quantity, avg_price, last_price, market_value, unrealized_pnl, opened_at):
        self.symbol = symbol
        self.state = state
        self.quantity = quantity
        self.avg_price = avg_price
        self.last_price = last_price
        self.market_value = market_value
        self.unrealized_pnl = unrealized_pnl
        self.opened_at = opened_at

class MockSnapshot:
    def __init__(self, equity, cash, timestamp):
        self.equity = equity
        self.cash = cash
        self.timestamp = timestamp

def test_portfolio_state_from_backtest_snapshot():
    dt = datetime(2023, 1, 1)
    snapshot = MockSnapshot(equity=1000.0, cash=400.0, timestamp=dt)

    pos1 = MockPosition("ASELS", PositionState.LONG, 10, 10.0, 12.0, 120.0, 20.0, dt)
    pos2 = MockPosition("THYAO", PositionState.SHORT, 5, 50.0, 40.0, 200.0, 50.0, dt)
    pos3 = MockPosition("GARAN", PositionState.FLAT, 0, 0.0, 0.0, 0.0, 0.0, dt)

    state = portfolio_state_from_backtest_snapshot(snapshot, [pos1, pos2, pos3], daily_signals=2)

    assert state.equity == 1000.0
    assert state.cash == 400.0
    assert state.timestamp == dt
    assert state.daily_signal_count == 2
    assert len(state.holdings) == 2

    # LONG position
    assert state.holdings[0].symbol == "ASELS"
    assert state.holdings[0].side == PortfolioPositionSide.LONG
    assert state.holdings[0].weight_pct == 120.0 / 1000.0
    assert state.holdings[0].metadata["backtest_position"] is True

    # SHORT position
    assert state.holdings[1].symbol == "THYAO"
    assert state.holdings[1].side == PortfolioPositionSide.SHORT
    assert state.holdings[1].weight_pct == 200.0 / 1000.0
