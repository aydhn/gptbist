import pytest
from bist_signal_bot.scanner.models import SymbolScanResult, ScanCandidateStatus, ScanSortKey
from bist_signal_bot.scanner.ranking import ScanRanker, ranking_to_dataframe
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection, SignalStrength
from bist_signal_bot.risk.models import RiskDecision, RiskDecisionStatus, RiskFilterResult

def _make_result(symbol, score, confidence=50.0, final_score=None):
    sig = SignalCandidate(
        strategy_name="test", symbol=symbol, direction=SignalDirection.LONG,
        score=score, confidence=confidence, strength=SignalStrength.STRONG
    )
    risk = RiskDecision(signal=sig, side=sig.direction, approved=True, filter_result=RiskFilterResult(status=RiskDecisionStatus.APPROVED, passed=True, active_rules=[], triggered_rules=[]),
        symbol=symbol, strategy_name="test", status=RiskDecisionStatus.APPROVED,
        final_score=final_score if final_score is not None else score
    )
    return SymbolScanResult(
        symbol=symbol, status=ScanCandidateStatus.PASSED, signal=sig, risk_decision=risk
    )

def test_scan_ranker_final_score():
    r1 = _make_result("A", score=60, final_score=70)
    r2 = _make_result("B", score=80, final_score=65)

    ranker = ScanRanker()
    rankings = ranker.rank([r1, r2], sort_key=ScanSortKey.FINAL_SCORE)

    assert rankings[0].symbol == "A"
    assert rankings[1].symbol == "B"
    assert rankings[0].rank_score == 70
    assert rankings[1].rank_score == 65

def test_scan_ranker_signal_score():
    r1 = _make_result("A", score=60, final_score=70)
    r2 = _make_result("B", score=80, final_score=65)

    ranker = ScanRanker()
    rankings = ranker.rank([r1, r2], sort_key=ScanSortKey.SIGNAL_SCORE)

    assert rankings[0].symbol == "B"
    assert rankings[1].symbol == "A"

def test_scan_ranker_none_at_bottom():
    r1 = _make_result("A", score=60)
    r1.risk_decision.final_score = None
    r1.signal.score = None
    r2 = _make_result("B", score=80)

    ranker = ScanRanker()
    rankings = ranker.rank([r1, r2], sort_key=ScanSortKey.FINAL_SCORE)

    assert rankings[0].symbol == "B"
    assert rankings[1].symbol == "A"

def test_ranking_to_dataframe_empty():
    # Empty test
    empty_df = ranking_to_dataframe([])
    assert empty_df.empty
    assert len(empty_df) == 0

def test_ranking_to_dataframe_normal():
    ranker = ScanRanker()

    # Normal test
    rankings = ranker.rank([_make_result("A", 60), _make_result("B", 80)])
    df = ranking_to_dataframe(rankings)
    assert not df.empty
    assert len(df) == 2
    assert "symbol" in df.columns
    assert "rank_score" in df.columns
    assert df.iloc[0]["symbol"] == "B"
    assert df.iloc[1]["symbol"] == "A"
    assert df.iloc[0]["rank_score"] == 80.0
    assert df.iloc[1]["rank_score"] == 60.0
    assert list(df["rank"]) == [1, 2]

    # Check that model fields are present
    assert "final_score" in df.columns
    assert "confidence" in df.columns


def _make_result_with_metadata(symbol, score, metadata, final_score=None):
    res = _make_result(symbol, score, final_score=final_score)
    res.signal.metadata = metadata
    # for RiskReward test
    if "risk_reward" in metadata:
        res.signal.risk_reward = metadata["risk_reward"]
        res.risk_decision.stop_target.risk_reward = metadata["risk_reward"]
    # cost
    if "cost_bps" in metadata:
        res.metadata["cost_bps"] = metadata["cost_bps"]
    return res

def test_calculate_rank_score_ml_score():
    res = _make_result_with_metadata("A", 60, {"ml_prediction_score": 85.5})
    ranker = ScanRanker()
    assert ranker.calculate_rank_score(res, ScanSortKey.ML_SCORE) == 85.5

def test_calculate_rank_score_ml_probability():
    res = _make_result_with_metadata("A", 60, {"ml_probability_positive": 0.75})
    ranker = ScanRanker()
    assert ranker.calculate_rank_score(res, ScanSortKey.ML_PROBABILITY) == 0.75

def test_calculate_rank_score_final_score():
    res = _make_result_with_metadata("A", 60, {}, final_score=75.0)
    ranker = ScanRanker()
    assert ranker.calculate_rank_score(res, ScanSortKey.FINAL_SCORE) == 75.0

def test_calculate_rank_score_signal_score():
    res = _make_result_with_metadata("A", 60, {})
    ranker = ScanRanker()
    assert ranker.calculate_rank_score(res, ScanSortKey.SIGNAL_SCORE) == 60.0

def test_calculate_rank_score_confidence():
    res = _make_result("A", 60, confidence=90.0)
    ranker = ScanRanker()
    assert ranker.calculate_rank_score(res, ScanSortKey.CONFIDENCE) == 90.0

def test_calculate_rank_score_risk_reward():
    from bist_signal_bot.risk.models import StopTargetReference
    res = _make_result("A", 60)
    res.risk_decision.stop_target = StopTargetReference(entry_price=10.0, stop_price=9.0, target_price=12.0, risk_reward=2.0)
    ranker = ScanRanker()
    assert ranker.calculate_rank_score(res, ScanSortKey.RISK_REWARD) == 2.0

def test_calculate_rank_score_liquidity():
    res = _make_result_with_metadata("A", 60, {"features": {"liquidity_score": 88.0}})
    ranker = ScanRanker()
    assert ranker.calculate_rank_score(res, ScanSortKey.LIQUIDITY) == 88.0

def test_calculate_rank_score_volume_activity():
    res = _make_result_with_metadata("A", 60, {"features": {"volume_activity_score": 70.0}})
    ranker = ScanRanker()
    assert ranker.calculate_rank_score(res, ScanSortKey.VOLUME_ACTIVITY) == 70.0

def test_calculate_rank_score_momentum():
    res = _make_result_with_metadata("A", 60, {"features": {"momentum_strength_score": 65.0}})
    ranker = ScanRanker()
    assert ranker.calculate_rank_score(res, ScanSortKey.MOMENTUM) == 65.0

def test_calculate_rank_score_trend():
    res = _make_result_with_metadata("A", 60, {"features": {"trend_strength_score": 55.0}})
    ranker = ScanRanker()
    assert ranker.calculate_rank_score(res, ScanSortKey.TREND) == 55.0

def test_calculate_rank_score_low_cost():
    res = _make_result_with_metadata("A", 60, {"cost_bps": 10.0})
    ranker = ScanRanker()
    assert ranker.calculate_rank_score(res, ScanSortKey.LOW_COST) == 90.0

def test_calculate_rank_score_low_volatility():
    res = _make_result_with_metadata("A", 60, {"features": {"volatility_risk_score": 30.0}})
    ranker = ScanRanker()
    assert ranker.calculate_rank_score(res, ScanSortKey.LOW_VOLATILITY) == 70.0

def test_calculate_rank_score_fallback_zero():
    res = _make_result_with_metadata("A", 60, {})
    # removing signal and risk
    res.signal = None
    res.risk_decision = None
    ranker = ScanRanker()
    assert ranker.calculate_rank_score(res, ScanSortKey.FINAL_SCORE) == 0.0
    assert ranker.calculate_rank_score(res, ScanSortKey.SIGNAL_SCORE) == 0.0
    assert ranker.calculate_rank_score(res, ScanSortKey.CONFIDENCE) == 0.0
    assert ranker.calculate_rank_score(res, ScanSortKey.RISK_REWARD) == 0.0
    assert ranker.calculate_rank_score(res, ScanSortKey.ML_SCORE) == 0.0
