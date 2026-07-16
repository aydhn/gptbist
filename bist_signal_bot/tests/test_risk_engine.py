import pytest
import datetime
from bist_signal_bot.risk.engine import RiskEngine
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection
from bist_signal_bot.risk.models import RiskDecisionStatus, PositionSizingMethod

def test_risk_engine_evaluate_signal_approved():
    settings = Settings()
    settings.RISK_POSITION_SIZING_METHOD = "RISK_PERCENT"
    engine = RiskEngine.from_settings(settings)

    signal = SignalCandidate(
        symbol="ASELS",
        strategy_name="test",
        direction=SignalDirection.LONG,
        score=100.0,
        confidence=100.0,
        generated_at=datetime.datetime.now(datetime.timezone.utc),
        entry_reference_price=100.0,
        feature_snapshot={"close": 100.0, "atr_14": 2.0}
    )

    context = engine.build_default_context(equity=100000.0, available_cash=100000.0)
    decision = engine.evaluate_signal(signal, context, None)

    assert decision.status in [RiskDecisionStatus.APPROVED, RiskDecisionStatus.REDUCED]
    assert decision.approved is True
    assert decision.position_size is not None
    assert decision.position_size.method == PositionSizingMethod.RISK_PERCENT

def test_risk_engine_evaluate_signal_rejected_by_score():
    settings = Settings()
    settings.RISK_MIN_SIGNAL_SCORE = 80.0
    engine = RiskEngine.from_settings(settings)

    signal = SignalCandidate(
        symbol="ASELS",
        strategy_name="test",
        direction=SignalDirection.LONG,
        score=50.0,
        confidence=100.0,
        generated_at=datetime.datetime.now(datetime.timezone.utc),
        entry_reference_price=100.0,
        feature_snapshot={"close": 100.0, "atr_14": 2.0}
    )

    context = engine.build_default_context()
    decision = engine.evaluate_signal(signal, context, None)

    assert decision.status == RiskDecisionStatus.REJECTED
    assert decision.approved is False
    assert "SCORE_TOO_LOW" in [r.name for r in decision.filter_result.reject_reasons]

def test_risk_engine_evaluate_batch():
    settings = Settings()
    settings.RISK_POSITION_SIZING_METHOD = "RISK_PERCENT"
    engine = RiskEngine.from_settings(settings)

    signals = [
        SignalCandidate(
            symbol="ASELS",
            strategy_name="test",
            direction=SignalDirection.LONG,
            score=100.0,
            confidence=100.0,
            generated_at=datetime.datetime.now(datetime.timezone.utc),
            entry_reference_price=100.0,
            feature_snapshot={"close": 100.0, "atr_14": 2.0}
        ),
        SignalCandidate(
            symbol="GARAN",
            strategy_name="test",
            direction=SignalDirection.FLAT,
            score=100.0,
            confidence=100.0,
            generated_at=datetime.datetime.now(datetime.timezone.utc),
            entry_reference_price=50.0,
            feature_snapshot={"close": 50.0}
        )
    ]

    context = engine.build_default_context()
    batch = engine.evaluate_batch(signals, context)

    assert batch.requested_count == 2
    assert batch.approved_count == 1
    assert batch.watch_only_count == 1
