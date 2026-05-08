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

def test_ranking_to_dataframe():
    ranker = ScanRanker()
    rankings = ranker.rank([_make_result("A", 60), _make_result("B", 80)])
    df = ranking_to_dataframe(rankings)
    assert not df.empty
    assert len(df) == 2
