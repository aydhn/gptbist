from bist_signal_bot.portfolio.holdings import build_portfolio_state, update_holding_prices
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
