from datetime import datetime, timezone
from bist_signal_bot.portfolio.allocation import PortfolioAllocator
from bist_signal_bot.portfolio.models import AllocationRequest, AllocationMethod, PortfolioState
from bist_signal_bot.risk.models import RiskDecision, RiskDecisionStatus, RiskFilterResult, PositionSizeResult
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection

def _make_signal(symbol: str, score: float = 50.0):
    return SignalCandidate(
        symbol=symbol,
        strategy_name="mock",
        direction=SignalDirection.LONG,
        score=score,
        confidence=100.0,
        timeframe="1d",
        entry_reference_price=100.0,
        generated_at=datetime.now(timezone.utc)
    )

def _make_decision(signal: SignalCandidate, status: RiskDecisionStatus, final_notional: float = 100000.0, risk_pct: float = 0.01):
    filter_res = RiskFilterResult(passed=(status == RiskDecisionStatus.APPROVED), status=status, reasons=[])
    pos_size = None
    if status == RiskDecisionStatus.APPROVED:
        pos_size = PositionSizeResult(
            method="FIXED_NOTIONAL",
            symbol=signal.symbol,
            side=SignalDirection.LONG,
            equity=100000.0,
            entry_price=100.0,
            quantity=final_notional / 100.0,
            final_notional=final_notional,
            original_notional=final_notional,
            final_position_pct=final_notional / 100000.0,
            max_position_pct=0.2,
            risk_pct=risk_pct
        )
    return RiskDecision(
        signal=signal,
        side=SignalDirection.LONG,
        approved=(status == RiskDecisionStatus.APPROVED),
        status=status,
        filter_result=filter_res,
        position_size=pos_size,
        stop_target=None,
        issues=[],
        warnings=[],
        generated_at=datetime.now(timezone.utc)
    )

def test_no_valid_decisions():
    allocator = PortfolioAllocator()
    state = PortfolioState(equity=100000.0, cash=100000.0)
    req = AllocationRequest(signals=[], risk_decisions=[], portfolio_state=state, method=AllocationMethod.EQUAL_WEIGHT, total_allocation_pct=0.90, max_symbol_weight_pct=0.50)
    res = allocator.allocate(req)
    assert res.total_allocated_notional == 0.0
    assert len(res.items) == 0

def test_rejected_decisions():
    allocator = PortfolioAllocator()
    state = PortfolioState(equity=100000.0, cash=100000.0)
    sig = _make_signal("A")
    dec = _make_decision(sig, RiskDecisionStatus.REJECTED)
    req = AllocationRequest(signals=[sig], risk_decisions=[dec], portfolio_state=state, method=AllocationMethod.EQUAL_WEIGHT, total_allocation_pct=0.90, max_symbol_weight_pct=0.50)
    res = allocator.allocate(req)
    assert len(res.items) == 1
    assert not res.items[0].approved
    assert res.items[0].allocated_notional == 0.0

def test_allocation_methods():
    allocator = PortfolioAllocator()
    allocator.settings.PORTFOLIO_MIN_ALLOCATION_NOTIONAL = 0.0
    state = PortfolioState(equity=100000.0, cash=100000.0)
    sig_a = _make_signal("A", score=10.0)
    sig_b = _make_signal("B", score=30.0)
    dec_a = _make_decision(sig_a, RiskDecisionStatus.APPROVED, risk_pct=0.01)
    dec_b = _make_decision(sig_b, RiskDecisionStatus.APPROVED, risk_pct=0.02)

    # Score weighted
    req = AllocationRequest(signals=[sig_a, sig_b], risk_decisions=[dec_a, dec_b], portfolio_state=state, method=AllocationMethod.SCORE_WEIGHTED, total_allocation_pct=1.0, max_symbol_weight_pct=1.0)
    res = allocator.allocate(req)
    assert len(res.items) == 2
    item_a = next(i for i in res.items if i.symbol == "A")
    item_b = next(i for i in res.items if i.symbol == "B")
    assert item_a.allocated_notional == 25000.0  # 10 / 40 * 100k
    assert item_b.allocated_notional == 75000.0  # 30 / 40 * 100k

    # Risk parity
    req.method = AllocationMethod.RISK_PARITY_SIMPLE
    res = allocator.allocate(req)
    item_a = next(i for i in res.items if i.symbol == "A")
    item_b = next(i for i in res.items if i.symbol == "B")
    # A risk 1%, B risk 2% => A weight 1/1 / (1/1 + 1/2) = 2/3, B weight 1/3
    assert abs(item_a.allocated_notional - 66666.666) < 100.0
    assert abs(item_b.allocated_notional - 33333.333) < 100.0

    # Risk budget
    req.method = AllocationMethod.RISK_BUDGET
    res = allocator.allocate(req)
    item_a = next(i for i in res.items if i.symbol == "A")
    item_b = next(i for i in res.items if i.symbol == "B")
    # A risk 0.01, B risk 0.02 => normalize to 1/3, 2/3
    assert abs(item_a.allocated_notional - 33333.33) < 100.0
    assert abs(item_b.allocated_notional - 66666.66) < 100.0

def test_allocation_fallbacks():
    allocator = PortfolioAllocator()
    allocator.settings.PORTFOLIO_MIN_ALLOCATION_NOTIONAL = 0.0
    state = PortfolioState(equity=100000.0, cash=100000.0)
    sig_a = _make_signal("A", score=0.0)
    sig_b = _make_signal("B", score=0.0)
    dec_a = _make_decision(sig_a, RiskDecisionStatus.APPROVED, risk_pct=0.0)
    dec_b = _make_decision(sig_b, RiskDecisionStatus.APPROVED, risk_pct=0.0)

    # Score zero total
    req = AllocationRequest(signals=[sig_a, sig_b], risk_decisions=[dec_a, dec_b], portfolio_state=state, method=AllocationMethod.SCORE_WEIGHTED, total_allocation_pct=1.0, max_symbol_weight_pct=1.0)
    res = allocator.allocate(req)
    assert res.items[0].allocated_notional == 50000.0
    assert res.items[1].allocated_notional == 50000.0

    # Risk parity zero inv risks
    req.method = AllocationMethod.RISK_PARITY_SIMPLE
    res = allocator.allocate(req)
    # fallbacks to 0.01 internally
    assert res.items[0].allocated_notional == 50000.0
    assert res.items[1].allocated_notional == 50000.0

    # Hybrid
    req.method = AllocationMethod.HYBRID
    res = allocator.allocate(req)
    assert res.items[0].allocated_notional == 50000.0

    # Volatility scaled (fallback equal)
    req.method = AllocationMethod.VOLATILITY_SCALED
    res = allocator.allocate(req)
    assert res.items[0].allocated_notional == 50000.0
    assert any("VOLATILITY_SCALED fallback" in issue for issue in res.issues)

def test_max_weight_cap():
    allocator = PortfolioAllocator()
    allocator.settings.PORTFOLIO_MIN_ALLOCATION_NOTIONAL = 0.0
    state = PortfolioState(equity=100000.0, cash=100000.0)
    sig_a = _make_signal("A")
    sig_b = _make_signal("B")
    sig_c = _make_signal("C")

    # Give A much higher risk budget, it would naturally get > 50%
    dec_a = _make_decision(sig_a, RiskDecisionStatus.APPROVED, risk_pct=0.08)
    dec_b = _make_decision(sig_b, RiskDecisionStatus.APPROVED, risk_pct=0.01)
    dec_c = _make_decision(sig_c, RiskDecisionStatus.APPROVED, risk_pct=0.01)

    req = AllocationRequest(signals=[sig_a, sig_b, sig_c], risk_decisions=[dec_a, dec_b, dec_c], portfolio_state=state, method=AllocationMethod.RISK_BUDGET, total_allocation_pct=1.0, max_symbol_weight_pct=0.50)
    res = allocator.allocate(req)

    item_a = next(i for i in res.items if i.symbol == "A")
    item_b = next(i for i in res.items if i.symbol == "B")
    item_c = next(i for i in res.items if i.symbol == "C")

    assert item_a.allocated_notional == 50000.0  # Capped at 50%
    assert abs(item_b.allocated_notional - 25000.0) <= 100.0
    assert abs(item_c.allocated_notional - 25000.0) <= 100.0

def test_insufficient_cash():
    allocator = PortfolioAllocator()
    allocator.settings.PORTFOLIO_MIN_ALLOCATION_NOTIONAL = 0.0
    state = PortfolioState(equity=100000.0, cash=100.0)  # Low cash
    sig_a = _make_signal("A")
    dec_a = _make_decision(sig_a, RiskDecisionStatus.APPROVED, final_notional=10000.0)
    req = AllocationRequest(signals=[sig_a], risk_decisions=[dec_a], portfolio_state=state, method=AllocationMethod.EQUAL_WEIGHT, total_allocation_pct=1.0, max_symbol_weight_pct=1.0)
    res = allocator.allocate(req)

    assert len(res.items) == 1
    item = res.items[0]
    assert item.allocated_notional <= 100.0

def test_below_min_notional():
    allocator = PortfolioAllocator()
    allocator.settings.PORTFOLIO_MIN_ALLOCATION_NOTIONAL = 50000.0
    state = PortfolioState(equity=10000.0, cash=10000.0)
    sig_a = _make_signal("A")
    dec_a = _make_decision(sig_a, RiskDecisionStatus.APPROVED)
    req = AllocationRequest(signals=[sig_a], risk_decisions=[dec_a], portfolio_state=state, method=AllocationMethod.EQUAL_WEIGHT, total_allocation_pct=1.0, max_symbol_weight_pct=1.0)
    res = allocator.allocate(req)

    assert len(res.items) == 1
    assert not res.items[0].approved
    assert res.items[0].allocated_notional == 0.0
    assert any("Below min notional" in str(reason) for reason in res.items[0].reasons)

def test_capping_max_allocation():
    allocator = PortfolioAllocator()
    allocator.settings.PORTFOLIO_MIN_ALLOCATION_NOTIONAL = 0.0
    state = PortfolioState(equity=100000.0, cash=100000.0)
    sig_a = _make_signal("A")
    dec_a = _make_decision(sig_a, RiskDecisionStatus.APPROVED, final_notional=5000.0) # Original limit is 5000
    req = AllocationRequest(signals=[sig_a], risk_decisions=[dec_a], portfolio_state=state, method=AllocationMethod.EQUAL_WEIGHT, total_allocation_pct=1.0, max_symbol_weight_pct=1.0)
    res = allocator.allocate(req)

    # Requested 100k, but decision limited to 5k
    assert res.items[0].allocated_notional == 5000.0
    assert res.items[0].reduction_pct == 0.0

def test_reduced_allocation():
    allocator = PortfolioAllocator()
    allocator.settings.PORTFOLIO_MIN_ALLOCATION_NOTIONAL = 0.0
    state = PortfolioState(equity=10000.0, cash=10000.0)
    sig_a = _make_signal("A")
    dec_a = _make_decision(sig_a, RiskDecisionStatus.APPROVED, final_notional=20000.0) # Original limit 20k
    req = AllocationRequest(signals=[sig_a], risk_decisions=[dec_a], portfolio_state=state, method=AllocationMethod.EQUAL_WEIGHT, total_allocation_pct=0.5, max_symbol_weight_pct=1.0)
    res = allocator.allocate(req)

    # Target is 50% of 10k = 5000
    assert res.items[0].allocated_notional == 5000.0
    assert res.items[0].reduction_pct == 0.75 # (20000 - 5000) / 20000
    assert "A" in res.reduced_symbols
