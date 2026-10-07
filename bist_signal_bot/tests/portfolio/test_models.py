import pytest
import pandas as pd
from datetime import datetime

from bist_signal_bot.portfolio.models import (
    PortfolioHolding,
    PortfolioPositionSide,
    PortfolioState,
    CorrelationMatrixResult,
    ExposureReport,
    AllocationRequest,
    AllocationResultItem,
    AllocationResult,
    AllocationMethod,
    PortfolioRiskDecision,
    PortfolioDecisionStatus,
    PortfolioRejectReason
)
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection
from bist_signal_bot.risk.models import RiskDecision

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

def test_portfolio_holding_validation():
    with pytest.raises(ValueError, match="Quantity cannot be negative"):
        PortfolioHolding(symbol="A", side=PortfolioPositionSide.LONG, quantity=-1, avg_price=10.0, market_value=100.0, weight_pct=0.1)

    with pytest.raises(ValueError, match="Average price must be greater than zero"):
        PortfolioHolding(symbol="A", side=PortfolioPositionSide.LONG, quantity=10, avg_price=0.0, market_value=100.0, weight_pct=0.1)

    with pytest.raises(ValueError, match="Market value cannot be negative"):
        PortfolioHolding(symbol="A", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=-1.0, weight_pct=0.1)

    with pytest.raises(ValueError, match="Weight percentage cannot be negative"):
        PortfolioHolding(symbol="A", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=100.0, weight_pct=-0.1)


def test_portfolio_state_exposure_and_counts():
    h1 = PortfolioHolding(symbol="A", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=100.0, weight_pct=0.1, sector="Tech")
    h2 = PortfolioHolding(symbol="B", side=PortfolioPositionSide.SHORT, quantity=5, avg_price=20.0, market_value=100.0, weight_pct=0.1, sector="Bank")
    state = PortfolioState(equity=1000.0, cash=800.0, holdings=[h1, h2])

    assert state.open_position_count() == 2
    assert state.gross_exposure_pct() == 0.20
    assert state.net_exposure_pct() == 0.0 # 100 long - 100 short = 0
    assert state.sector_weights() == {"Tech": 0.1, "Bank": 0.1}

def test_portfolio_state_methods_zero_equity():
    state = PortfolioState(equity=1000.0, cash=800.0, holdings=[])
    state.equity = 0.0 # Bypass validator for testing
    assert state.gross_exposure_pct() == 0.0
    assert state.net_exposure_pct() == 0.0
    assert state.sector_weights() == {}

def test_portfolio_state_validation():
    with pytest.raises(ValueError, match="Equity must be positive"):
        PortfolioState(equity=0, cash=0)

    with pytest.raises(ValueError, match="Cash cannot be negative"):
        PortfolioState(equity=100, cash=-1)

    with pytest.raises(ValueError, match="Daily signal count cannot be negative"):
        PortfolioState(equity=100, cash=0, daily_signal_count=-1)

def test_portfolio_state_daily_signal_count_valid():
    state = PortfolioState(equity=1000.0, cash=1000.0, daily_signal_count=5)
    assert state.daily_signal_count == 5

def test_portfolio_state_symbol_weight():
    h1 = PortfolioHolding(symbol="A", side=PortfolioPositionSide.LONG, quantity=10, avg_price=10.0, market_value=100.0, weight_pct=0.1)
    state = PortfolioState(equity=1000.0, cash=800.0, holdings=[h1])

    assert state.symbol_weight("A") == 0.1
    assert state.symbol_weight("a.is") == 0.1  # normalization check
    assert state.symbol_weight("B") == 0.0

    assert state.holding_symbols() == ["A"]

def test_correlation_matrix_result_summary():
    res = CorrelationMatrixResult(
        symbols=["A", "B"],
        matrix=pd.DataFrame(),
        lookback_rows=30,
        method="pearson",
        generated_at=datetime.now(),
        issues=["issue1"],
        metadata={}
    )
    summary = res.summary()
    assert summary["symbol_count"] == 2
    assert summary["lookback_rows"] == 30
    assert summary["method"] == "pearson"
    assert summary["issues_count"] == 1

def test_exposure_report_summary():
    report = ExposureReport(
        gross_exposure_pct=0.5,
        net_exposure_pct=0.1,
        long_exposure_pct=0.3,
        short_exposure_pct=0.2,
        max_symbol_weight_pct=0.15,
        sector_weights={"Tech": 0.3},
        open_position_count=5,
        cash_pct=0.5,
        issues=["issue"],
        metadata={}
    )
    summary = report.summary()
    assert summary["gross_exposure_pct"] == 0.5
    assert summary["net_exposure_pct"] == 0.1
    assert summary["max_symbol_weight_pct"] == 0.15
    assert summary["open_position_count"] == 5
    assert summary["cash_pct"] == 0.5
    assert summary["issues_count"] == 1

def test_allocation_request_validation():
    state = PortfolioState(equity=1000.0, cash=1000.0)

    with pytest.raises(ValueError, match="Total allocation percentage must be between 0.0 and 1.0"):
        AllocationRequest(signals=[], risk_decisions=[], portfolio_state=state, method=AllocationMethod.EQUAL_WEIGHT, total_allocation_pct=1.1, max_symbol_weight_pct=0.1)

    with pytest.raises(ValueError, match="Max symbol weight percentage must be between 0.0 and 1.0"):
        AllocationRequest(signals=[], risk_decisions=[], portfolio_state=state, method=AllocationMethod.EQUAL_WEIGHT, total_allocation_pct=0.5, max_symbol_weight_pct=-0.1)

    # Valid
    AllocationRequest(signals=[], risk_decisions=[], portfolio_state=state, method=AllocationMethod.EQUAL_WEIGHT, total_allocation_pct=0.5, max_symbol_weight_pct=0.1)

def test_allocation_result_summary():
    res = AllocationResult(
        method=AllocationMethod.EQUAL_WEIGHT,
        items=[
            AllocationResultItem(symbol="A", approved=True, original_notional=100.0, allocated_notional=100.0, allocated_weight_pct=0.1, quantity=10, reduction_pct=0.0, reasons=[], metadata={}),
            AllocationResultItem(symbol="B", approved=False, original_notional=100.0, allocated_notional=0.0, allocated_weight_pct=0.0, quantity=0, reduction_pct=1.0, reasons=[], metadata={})
        ],
        total_allocated_notional=100.0,
        total_allocated_pct=0.1,
        rejected_symbols=["B", "C"],
        reduced_symbols=["D"],
        issues=[],
        generated_at=datetime.now()
    )
    summary = res.summary()
    assert summary["method"] == AllocationMethod.EQUAL_WEIGHT.value
    assert summary["total_allocated_pct"] == 0.1
    assert summary["items_count"] == 2
    assert summary["approved_count"] == 1
    assert summary["rejected_count"] == 2
    assert summary["reduced_count"] == 1

def test_portfolio_risk_decision_summaries():
    state = PortfolioState(equity=1000.0, cash=1000.0)
    alloc_res = AllocationResult(
        method=AllocationMethod.EQUAL_WEIGHT,
        items=[],
        total_allocated_notional=0.0,
        total_allocated_pct=0.0,
        rejected_symbols=[],
        reduced_symbols=[],
        issues=[],
        generated_at=datetime.now()
    )
    exp_before = ExposureReport(0.5, 0.1, 0.3, 0.2, 0.1, {}, 5, 0.5, [], {})
    exp_after = ExposureReport(0.6, 0.2, 0.4, 0.2, 0.1, {}, 6, 0.4, [], {})

    decision = PortfolioRiskDecision(
        portfolio_state=state,
        input_signals=[],
        trade_risk_decisions=[],
        allocation_result=alloc_res,
        exposure_report_before=exp_before,
        exposure_report_after=exp_after,
        correlation_result=None,
        status=PortfolioDecisionStatus.APPROVED,
        approved_count=1,
        rejected_count=2,
        reduced_count=3,
        reject_reasons=[],
        warnings=[],
        generated_at=datetime.now()
    )

    summary = decision.summary()
    assert summary["status"] == PortfolioDecisionStatus.APPROVED.value
    assert summary["approved_count"] == 1
    assert summary["rejected_count"] == 2
    assert summary["reduced_count"] == 3
    assert summary["disclaimer"] == decision.disclaimer

    safe_dict = decision.safe_public_dict()
    assert safe_dict["status"] == PortfolioDecisionStatus.APPROVED.value
    assert safe_dict["approved_count"] == 1
    assert safe_dict["rejected_count"] == 2
    assert safe_dict["reduced_count"] == 3
    assert safe_dict["allocation_method"] == AllocationMethod.EQUAL_WEIGHT.value
    assert safe_dict["total_allocated_pct"] == 0.0
    assert safe_dict["gross_exposure_before_pct"] == 0.5
    assert safe_dict["gross_exposure_after_pct"] == 0.6
    assert safe_dict["disclaimer"] == decision.disclaimer
