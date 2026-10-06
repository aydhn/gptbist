from bist_signal_bot.portfolio.exposure import ExposureAnalyzer
from bist_signal_bot.portfolio.models import PortfolioState, PortfolioPositionSide, PortfolioHolding
import pytest

def test_calculate_exposure_zero_equity():
    analyzer = ExposureAnalyzer()
    state = PortfolioState.model_construct(equity=0.0, cash=0.0, holdings=[])
    report = analyzer.calculate_exposure(state)
    assert report.gross_exposure_pct == 0.0
    assert report.cash_pct == 1.0

def test_calculate_exposure_basic():
    analyzer = ExposureAnalyzer()
    h1 = PortfolioHolding(symbol="A", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=100.0, weight_pct=0.1)
    state = PortfolioState(equity=1000.0, cash=900.0, holdings=[h1])
    report = analyzer.calculate_exposure(state)
    assert report.gross_exposure_pct == 0.1
    assert report.net_exposure_pct == 0.1
    assert report.long_exposure_pct == 0.1
    assert report.short_exposure_pct == 0.0
    assert report.cash_pct == 0.9
