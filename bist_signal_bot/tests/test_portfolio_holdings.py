from bist_signal_bot.portfolio.holdings import build_portfolio_state, update_holding_prices, holding_from_dict
from bist_signal_bot.portfolio.models import PortfolioHolding, PortfolioPositionSide

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

def test_holding_from_dict():
    data = {
        "symbol": "ASELS",
        "side": PortfolioPositionSide.LONG,
        "quantity": 10.0,
        "avg_price": 10.0,
        "market_value": 100.0,
        "weight_pct": 0.1,
        "sector": "Defense",
        "metadata": {"test": True}
    }

    holding = holding_from_dict(data)

    assert isinstance(holding, PortfolioHolding)
    assert holding.symbol == "ASELS"
    assert holding.side == PortfolioPositionSide.LONG
    assert holding.quantity == 10.0
    assert holding.avg_price == 10.0
    assert holding.market_value == 100.0
    assert holding.weight_pct == 0.1
    assert holding.sector == "Defense"
    assert holding.metadata == {"test": True}

def test_update_holding_prices_short_pnl_and_missing_symbol():
    h_short = PortfolioHolding(symbol="THYAO", side=PortfolioPositionSide.SHORT, quantity=5, avg_price=20.0, market_value=100.0, weight_pct=0.5)
    h_missing = PortfolioHolding(symbol="GARAN", side=PortfolioPositionSide.LONG, quantity=10, avg_price=15.0, market_value=150.0, weight_pct=0.5)
    state = build_portfolio_state(equity=250.0, cash=0.0, holdings=[h_short, h_missing])

    new_state = update_holding_prices(state, {"THYAO": 15.0})

    assert new_state.holdings[0].last_price == 15.0
    assert new_state.holdings[0].market_value == 75.0
    assert new_state.holdings[0].unrealized_pnl == 25.0

    assert new_state.holdings[1].last_price is None
    assert new_state.holdings[1].market_value == 150.0

    assert new_state.equity == 225.0

def test_portfolio_state_from_backtest_snapshot():
    import datetime
    from bist_signal_bot.backtesting.models import PositionState

    class DummySnapshot:
        def __init__(self, equity, cash, timestamp):
            self.equity = equity
            self.cash = cash
            self.timestamp = timestamp

    class DummyPosition:
        def __init__(self, symbol, state, quantity, avg_price, last_price, market_value, unrealized_pnl, opened_at):
            self.symbol = symbol
            self.state = state
            self.quantity = quantity
            self.avg_price = avg_price
            self.last_price = last_price
            self.market_value = market_value
            self.unrealized_pnl = unrealized_pnl
            self.opened_at = opened_at

    snapshot = DummySnapshot(equity=1000.0, cash=100.0, timestamp=datetime.datetime.now())
    pos1 = DummyPosition("ASELS", PositionState.LONG, 10, 10.0, 12.0, 120.0, 20.0, datetime.datetime.now())
    pos2 = DummyPosition("THYAO", PositionState.SHORT, 5, 20.0, 15.0, 75.0, 25.0, datetime.datetime.now())
    pos3 = DummyPosition("GARAN", PositionState.FLAT, 0, 0, 0, 0, 0, None)

    from bist_signal_bot.portfolio.holdings import portfolio_state_from_backtest_snapshot
    state = portfolio_state_from_backtest_snapshot(snapshot, [pos1, pos2, pos3], daily_signals=2)

    assert state.equity == 1000.0
    assert state.cash == 100.0
    assert state.daily_signal_count == 2
    assert len(state.holdings) == 2
    assert state.holdings[0].symbol == "ASELS"
    assert state.holdings[0].side == PortfolioPositionSide.LONG
    assert state.holdings[1].symbol == "THYAO"
    assert state.holdings[1].side == PortfolioPositionSide.SHORT

def test_portfolio_state_from_backtest_snapshot_zero_equity():
    import datetime
    import pytest
    from pydantic import ValidationError
    from bist_signal_bot.backtesting.models import PositionState

    class DummySnapshot:
        def __init__(self, equity, cash, timestamp):
            self.equity = equity
            self.cash = cash
            self.timestamp = timestamp

    class DummyPosition:
        def __init__(self, symbol, state, quantity, avg_price, last_price, market_value, unrealized_pnl, opened_at):
            self.symbol = symbol
            self.state = state
            self.quantity = quantity
            self.avg_price = avg_price
            self.last_price = last_price
            self.market_value = market_value
            self.unrealized_pnl = unrealized_pnl
            self.opened_at = opened_at

    snapshot = DummySnapshot(equity=0.0, cash=100.0, timestamp=datetime.datetime.now())
    pos1 = DummyPosition("ASELS", PositionState.LONG, 10, 10.0, 12.0, 120.0, 20.0, datetime.datetime.now())

    from bist_signal_bot.portfolio.holdings import portfolio_state_from_backtest_snapshot

    with pytest.raises(ValidationError):
        portfolio_state_from_backtest_snapshot(snapshot, [pos1])
