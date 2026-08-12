import pytest
from bist_signal_bot.portfolio.exposure import ExposureAnalyzer
from bist_signal_bot.portfolio.models import PortfolioState, PortfolioHolding, PortfolioPositionSide
import datetime

def test_zero_equity():
    state = PortfolioState(
        equity=0.0,
        cash=0.0,
        holdings=[],
        timestamp=datetime.datetime.now(datetime.UTC),
        daily_signal_count=0
    )
    analyzer = ExposureAnalyzer()
    report = analyzer.calculate_exposure(state)
    assert report.gross_exposure_pct == 0.0
    assert report.cash_pct == 1.0
    assert "Portfolio equity is zero or negative" in report.issues

test_zero_equity()
print("Success")
