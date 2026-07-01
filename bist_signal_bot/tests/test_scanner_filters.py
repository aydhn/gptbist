import pytest
from bist_signal_bot.scanner.models import SymbolScanResult, ScanCandidateStatus, ScanRequest, ScanUniverseMode
from bist_signal_bot.scanner.filters import ScanFilterEngine
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection, SignalStrength
from bist_signal_bot.risk.models import RiskDecision, RiskDecisionStatus, RiskFilterResult

def test_filter_low_signal_score():
    req = ScanRequest(strategy_name="t", universe_mode=ScanUniverseMode.ALL, min_signal_score=50.0)
    sig = SignalCandidate(strategy_name="t", symbol="A", direction=SignalDirection.LONG, score=40.0, confidence=80.0, strength=SignalStrength.STRONG)
    res = SymbolScanResult(symbol="A", status=ScanCandidateStatus.PASSED, signal=sig)

    engine = ScanFilterEngine()
    out = engine.filter_symbol_result(res, req)
    assert out.status == ScanCandidateStatus.FILTERED

def test_filter_low_confidence():
    req = ScanRequest(strategy_name="t", universe_mode=ScanUniverseMode.ALL, min_confidence=50.0, min_signal_score=10.0)
    sig = SignalCandidate(strategy_name="t", symbol="A", direction=SignalDirection.LONG, score=80.0, confidence=40.0, strength=SignalStrength.STRONG)
    res = SymbolScanResult(symbol="A", status=ScanCandidateStatus.PASSED, signal=sig)

    engine = ScanFilterEngine()
    out = engine.filter_symbol_result(res, req)
    assert out.status == ScanCandidateStatus.FILTERED

def test_filter_risk_rejected():
    req = ScanRequest(strategy_name="t", universe_mode=ScanUniverseMode.ALL, min_signal_score=10.0, min_confidence=10.0)
    sig = SignalCandidate(strategy_name="t", symbol="A", direction=SignalDirection.LONG, score=80.0, confidence=80.0, strength=SignalStrength.STRONG)
    risk = RiskDecision(signal=sig, side=sig.direction, approved=False, filter_result=RiskFilterResult(status=RiskDecisionStatus.REJECTED, passed=False, active_rules=[], triggered_rules=[]), symbol="A", strategy_name="t", status=RiskDecisionStatus.REJECTED)
    res = SymbolScanResult(symbol="A", status=ScanCandidateStatus.PASSED, signal=sig, risk_decision=risk)

    engine = ScanFilterEngine()
    out = engine.filter_symbol_result(res, req)
    assert out.status == ScanCandidateStatus.REJECTED

def test_filter_watch_only():
    req = ScanRequest(strategy_name="t", universe_mode=ScanUniverseMode.ALL, min_signal_score=10.0, min_confidence=10.0)
    sig = SignalCandidate(strategy_name="t", symbol="A", direction=SignalDirection.WATCH, score=80.0, confidence=80.0, strength=SignalStrength.STRONG)
    res = SymbolScanResult(symbol="A", status=ScanCandidateStatus.PASSED, signal=sig)

    engine = ScanFilterEngine()
    out = engine.filter_symbol_result(res, req)
    assert out.status == ScanCandidateStatus.WATCH_ONLY

def test_filter_error_status():
    req = ScanRequest(strategy_name="t", universe_mode=ScanUniverseMode.ALL)
    res = SymbolScanResult(symbol="A", status=ScanCandidateStatus.ERROR)

    engine = ScanFilterEngine()
    out = engine.filter_symbol_result(res, req)
    assert out.status == ScanCandidateStatus.ERROR

def test_filter_no_signal():
    req = ScanRequest(strategy_name="t", universe_mode=ScanUniverseMode.ALL)
    res = SymbolScanResult(symbol="A", status=ScanCandidateStatus.PASSED, signal=None)

    engine = ScanFilterEngine()
    out = engine.filter_symbol_result(res, req)
    assert out.status == ScanCandidateStatus.FILTERED
    assert "No signal generated" in out.reasons

def test_filter_low_final_score():
    req = ScanRequest(strategy_name="t", universe_mode=ScanUniverseMode.ALL, min_signal_score=10.0, min_confidence=10.0, min_final_score=80.0)
    sig = SignalCandidate(strategy_name="t", symbol="A", direction=SignalDirection.LONG, score=80.0, confidence=80.0, strength=SignalStrength.STRONG)
    risk = RiskDecision(signal=sig, side=sig.direction, approved=True, filter_result=RiskFilterResult(status=RiskDecisionStatus.APPROVED, passed=True, active_rules=[], triggered_rules=[]), symbol="A", strategy_name="t", status=RiskDecisionStatus.APPROVED, final_score=50.0)
    res = SymbolScanResult(symbol="A", status=ScanCandidateStatus.PASSED, signal=sig, risk_decision=risk)

    engine = ScanFilterEngine()
    out = engine.filter_symbol_result(res, req)
    assert out.status == ScanCandidateStatus.FILTERED
    assert any("Final score" in r for r in out.reasons)

def test_filter_forbidden_claims():
    req = ScanRequest(strategy_name="t", universe_mode=ScanUniverseMode.ALL, min_signal_score=10.0, min_confidence=10.0)
    sig = SignalCandidate(strategy_name="t", symbol="A", direction=SignalDirection.LONG, score=80.0, confidence=80.0, strength=SignalStrength.STRONG, metadata={"notes": "Kesin al bu hisseyi"})
    res = SymbolScanResult(symbol="A", status=ScanCandidateStatus.PASSED, signal=sig)

    engine = ScanFilterEngine()
    out = engine.filter_symbol_result(res, req)
    assert out.status == ScanCandidateStatus.REJECTED
    assert "Forbidden claim detected" in out.reasons[0]

def test_filter_passed():
    req = ScanRequest(strategy_name="t", universe_mode=ScanUniverseMode.ALL, min_signal_score=10.0, min_confidence=10.0)
    sig = SignalCandidate(strategy_name="t", symbol="A", direction=SignalDirection.LONG, score=80.0, confidence=80.0, strength=SignalStrength.STRONG, metadata={"notes": "Normal signal"})
    res = SymbolScanResult(symbol="A", status=ScanCandidateStatus.PASSED, signal=sig)

    engine = ScanFilterEngine()
    out = engine.filter_symbol_result(res, req)
    assert out.status == ScanCandidateStatus.PASSED
