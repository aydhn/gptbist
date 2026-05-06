import pytest
import datetime
from bist_signal_bot.risk.models import (
    RiskContext, StopTargetReference, PositionSizeResult, RiskDecision, RiskFilterResult,
    RiskDecisionStatus, RiskSide, StopMethod, TargetMethod, PositionSizingMethod
)

def test_risk_context_validation():
    ctx = RiskContext(
        equity=100000.0,
        available_cash=50000.0,
        current_positions={},
        open_position_count=0,
        daily_signal_count=0,
        portfolio_risk_pct=0.01,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
        metadata={}
    )
    assert ctx.equity == 100000.0

    with pytest.raises(ValueError):
        RiskContext(
            equity=-1000.0,
            available_cash=50000.0,
            current_positions={},
            open_position_count=0,
            daily_signal_count=0,
            portfolio_risk_pct=0.01,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            metadata={}
        )

def test_stop_target_reference_validation():
    ref = StopTargetReference(
        entry_price=100.0,
        stop_price=90.0,
        target_price=120.0,
        risk_per_share=10.0,
        reward_per_share=20.0,
        risk_reward=2.0,
        stop_method=StopMethod.FIXED_PERCENT,
        target_method=TargetMethod.RISK_REWARD_MULTIPLE,
        metadata={}
    )
    assert ref.entry_price == 100.0

    with pytest.raises(ValueError):
        StopTargetReference(
            entry_price=-10.0,
            stop_price=90.0,
            target_price=120.0,
            risk_per_share=10.0,
            reward_per_share=20.0,
            risk_reward=2.0,
            stop_method=StopMethod.FIXED_PERCENT,
            target_method=TargetMethod.RISK_REWARD_MULTIPLE,
            metadata={}
        )

def test_position_size_result_validation():
    res = PositionSizeResult(
        method=PositionSizingMethod.RISK_PERCENT,
        symbol="ASELS",
        side=RiskSide.LONG,
        equity=100000.0,
        entry_price=100.0,
        stop_price=90.0,
        target_risk_pct=0.01,
        max_position_pct=0.20,
        raw_notional=10000.0,
        capped_notional=10000.0,
        quantity=100.0,
        estimated_cost=0.0,
        final_notional=10000.0,
        final_position_pct=0.10,
        risk_amount=1000.0,
        risk_pct=0.01,
        reduced=False,
        issues=[],
        metadata={}
    )
    assert res.quantity == 100.0

    with pytest.raises(ValueError):
        PositionSizeResult(
            method=PositionSizingMethod.RISK_PERCENT,
            symbol="ASELS",
            side=RiskSide.LONG,
            equity=-100000.0,
            entry_price=100.0,
            stop_price=90.0,
            target_risk_pct=0.01,
            max_position_pct=0.20,
            raw_notional=10000.0,
            capped_notional=10000.0,
            quantity=100.0,
            estimated_cost=0.0,
            final_notional=10000.0,
            final_position_pct=0.10,
            risk_amount=1000.0,
            risk_pct=0.01,
            reduced=False,
            issues=[],
            metadata={}
        )

def test_risk_decision_summary():
    from bist_signal_bot.signals.models import SignalCandidate, SignalDirection

    signal = SignalCandidate(
        symbol="ASELS",
        strategy_name="test",
        direction=SignalDirection.LONG,
        score=100.0,
        confidence=100.0,
        generated_at=datetime.datetime.now(datetime.timezone.utc),
        feature_snapshot={}
    )

    ps = PositionSizeResult(
        method=PositionSizingMethod.RISK_PERCENT,
        symbol="ASELS",
        side=RiskSide.LONG,
        equity=100000.0,
        entry_price=100.0,
        stop_price=90.0,
        target_risk_pct=0.01,
        max_position_pct=0.20,
        raw_notional=10000.0,
        capped_notional=10000.0,
        quantity=100.0,
        estimated_cost=0.0,
        final_notional=10000.0,
        final_position_pct=0.10,
        risk_amount=1000.0,
        risk_pct=0.01,
        reduced=False,
        issues=[],
        metadata={}
    )

    fr = RiskFilterResult(
        passed=True,
        status=RiskDecisionStatus.APPROVED,
        reject_reasons=[],
        warnings=[],
        score_adjustment=0.0,
        metadata={}
    )

    decision = RiskDecision(
        signal=signal,
        status=RiskDecisionStatus.APPROVED,
        side=RiskSide.LONG,
        approved=True,
        position_size=ps,
        stop_target=None,
        filter_result=fr,
        final_score=100.0,
        final_confidence=100.0,
        max_loss_amount=1000.0,
        max_loss_pct=0.01,
        estimated_total_cost=0.0,
        estimated_cost_bps=0.0,
        generated_at=datetime.datetime.now(datetime.timezone.utc),
        disclaimer="Not investment advice.",
        metadata={}
    )

    summary = decision.summary()
    assert summary["symbol"] == "ASELS"
    assert summary["status"] == "APPROVED"
    assert summary["approved"] is True
    assert "position_notional" in summary
