import pytest
from bist_signal_bot.portfolio.models import PortfolioHolding, PortfolioPositionSide, PortfolioState

def test_portfolio_holding_normalizes_symbol():
    holding = PortfolioHolding(
        symbol="asels.is",
        side=PortfolioPositionSide.LONG,
        quantity=10,
        avg_price=10.0,
        market_value=100.0,
        weight_pct=0.1
    )
    assert holding.symbol == "ASELS"

def test_portfolio_state_exposure_and_counts():
    h1 = PortfolioHolding(symbol="A", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=100.0, weight_pct=0.1, sector="Tech")
    h2 = PortfolioHolding(symbol="B", side=PortfolioPositionSide.SHORT, quantity=5, avg_price=20.0, market_value=100.0, weight_pct=0.1, sector="Bank")
    state = PortfolioState(equity=1000.0, cash=800.0, holdings=[h1, h2])

    assert state.open_position_count() == 2
    assert state.gross_exposure_pct() == 0.20
    assert state.net_exposure_pct() == 0.0 # 100 long - 100 short = 0
    assert state.sector_weights() == {"Tech": 0.1, "Bank": 0.1}

def test_portfolio_state_validation():
    with pytest.raises(ValueError):
        PortfolioState(equity=-100, cash=0)
