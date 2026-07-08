import pytest
from datetime import datetime
from bist_signal_bot.portfolio.risk_engine import PortfolioRiskEngine
from bist_signal_bot.portfolio.models import PortfolioState
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection
from bist_signal_bot.config.settings import Settings

def test_portfolio_risk_engine_evaluate():
    settings = Settings()
    engine = PortfolioRiskEngine(settings=settings)
    state = engine.build_default_portfolio_state(equity=100000.0, cash=100000.0)

    signals = [
        SignalCandidate(symbol="A", strategy_name="mock", direction=SignalDirection.LONG, score=70.0, confidence=100.0, timeframe="1d", entry_reference_price=10.0, generated_at=datetime.utcnow()),
        SignalCandidate(symbol="B", strategy_name="mock", direction=SignalDirection.LONG, score=60.0, confidence=100.0, timeframe="1d", entry_reference_price=20.0, generated_at=datetime.utcnow())
    ]

    decision = engine.evaluate_portfolio_signals(signals, state)

    assert decision is not None
    assert decision.portfolio_state == state
    assert decision.approved_count + decision.rejected_count == 2

def test_portfolio_risk_engine_invalid_allocation_method_fallback():
    settings = Settings(PORTFOLIO_ALLOCATION_METHOD="INVALID_METHOD")
    engine = PortfolioRiskEngine(settings=settings)
    state = engine.build_default_portfolio_state(equity=100000.0, cash=100000.0)

    signals = [
        SignalCandidate(symbol="A", strategy_name="mock", direction=SignalDirection.LONG, score=70.0, confidence=100.0, timeframe="1d", entry_reference_price=10.0, generated_at=datetime.utcnow())
    ]

    decision = engine.evaluate_portfolio_signals(signals, state)

    assert decision is not None
    from bist_signal_bot.portfolio.models import AllocationMethod
    assert decision.allocation_result.method == AllocationMethod.HYBRID
