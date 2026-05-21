import pytest
from bist_signal_bot.drift.portfolio_drift import PortfolioDriftAnalyzer
from bist_signal_bot.drift.models import DriftStatus, DriftSeverity
from bist_signal_bot.config.settings import Settings

def test_portfolio_drift_missing():
    pda = PortfolioDriftAnalyzer(Settings())
    res = pda.analyze(None, None)
    assert res.status == DriftStatus.INSUFFICIENT_DATA

def test_portfolio_drift_shift():
    s = Settings()
    s.DRIFT_EXPOSURE_CHANGE_WARN = 0.20
    pda = PortfolioDriftAnalyzer(s)

    ref = {"exposures": [{"symbol": "A", "weight": 1.0}]}
    cur = {"exposures": [{"symbol": "B", "weight": 1.0}]}

    res = pda.analyze(ref, cur)
    assert res.status == DriftStatus.WATCH
    assert res.severity == DriftSeverity.MEDIUM
