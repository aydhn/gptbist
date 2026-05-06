from datetime import datetime
from bist_signal_bot.portfolio.allocation import PortfolioAllocator
from bist_signal_bot.portfolio.models import AllocationRequest, AllocationMethod, PortfolioState
from bist_signal_bot.risk.models import RiskDecision, RiskDecisionStatus, RiskFilterResult, PositionSizeResult, StopTargetReference
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection

def test_equal_weight_allocation():
    allocator = PortfolioAllocator()
    state = PortfolioState(equity=100000.0, cash=100000.0)

    signals = [
        SignalCandidate(symbol="A", strategy_name="mock", direction=SignalDirection.LONG, score=50.0, confidence=100.0, timeframe="1d", entry_reference_price=100.0, generated_at=datetime.utcnow()),
        SignalCandidate(symbol="B", strategy_name="mock", direction=SignalDirection.LONG, score=50.0, confidence=100.0, timeframe="1d", entry_reference_price=100.0, generated_at=datetime.utcnow())
    ]

    filter_res = RiskFilterResult(passed=True, status=RiskDecisionStatus.APPROVED, reasons=[])
    pos_size = PositionSizeResult(method="FIXED_NOTIONAL", symbol="A", side=SignalDirection.LONG, equity=100000.0, entry_price=100.0, quantity=100.0, final_notional=10000.0, original_notional=10000.0, final_position_pct=0.1, max_position_pct=0.2)
    stop_res = StopTargetReference(entry_price=100.0, stop_price=90.0, target_price=120.0, risk_reward=2.0)

    decisions = [
        RiskDecision(signal=signals[0], side=SignalDirection.LONG, approved=True, status=RiskDecisionStatus.APPROVED, filter_result=filter_res, position_size=pos_size, stop_target=stop_res, risk_pct=0.01, issues=[], warnings=[], generated_at=datetime.utcnow()),
        RiskDecision(signal=signals[1], side=SignalDirection.LONG, approved=True, status=RiskDecisionStatus.APPROVED, filter_result=filter_res, position_size=pos_size, stop_target=stop_res, risk_pct=0.01, issues=[], warnings=[], generated_at=datetime.utcnow())
    ]

    req = AllocationRequest(signals=signals, risk_decisions=decisions, portfolio_state=state, method=AllocationMethod.EQUAL_WEIGHT, total_allocation_pct=0.90, max_symbol_weight_pct=0.50)
    res = allocator.allocate(req)

    assert len(res.items) == 2
    for item in res.items:
        assert item.allocated_notional == 10000.0
