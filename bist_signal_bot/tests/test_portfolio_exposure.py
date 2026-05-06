from unittest.mock import MagicMock
import pytest
from bist_signal_bot.portfolio.exposure import ExposureAnalyzer
from bist_signal_bot.portfolio.models import PortfolioState, PortfolioHolding, PortfolioPositionSide
from bist_signal_bot.config.settings import Settings

def test_exposure_analyzer_calculate():
    h1 = PortfolioHolding(symbol="A", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=100.0, weight_pct=0.1, sector="Tech")
    h2 = PortfolioHolding(symbol="B", side=PortfolioPositionSide.SHORT, quantity=5, avg_price=20.0, market_value=100.0, weight_pct=0.1, sector="Bank")
    state = PortfolioState(equity=1000.0, cash=800.0, holdings=[h1, h2])

    analyzer = ExposureAnalyzer()
    report = analyzer.calculate_exposure(state)

    assert report.gross_exposure_pct == 0.20
    assert report.net_exposure_pct == 0.0
    assert report.max_symbol_weight_pct == 0.10
    assert report.cash_pct == 0.80

def test_exposure_analyzer_limits():
    settings = MagicMock()
    settings.PORTFOLIO_MAX_GROSS_EXPOSURE_PCT = 0.15
    settings.PORTFOLIO_MAX_NET_EXPOSURE_PCT = 1.0
    settings.PORTFOLIO_MAX_SYMBOL_WEIGHT_PCT = 0.20
    settings.PORTFOLIO_MAX_SECTOR_WEIGHT_PCT = 0.40
    settings.PORTFOLIO_MIN_CASH_PCT = 0.05
    settings.PORTFOLIO_MAX_OPEN_POSITIONS = 5 # overriding after init
    h1 = PortfolioHolding(symbol="A", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=100.0, weight_pct=0.1)
    h2 = PortfolioHolding(symbol="B", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=100.0, weight_pct=0.1)
    state = PortfolioState(equity=1000.0, cash=800.0, holdings=[h1, h2])

    analyzer = ExposureAnalyzer()
    report = analyzer.calculate_exposure(state)

    ok, reasons, issues = analyzer.check_exposure_limits(report, settings)
    assert not ok
    assert len(reasons) > 0
