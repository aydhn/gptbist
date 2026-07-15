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

def test_should_include_in_top_passed():
    engine = ScanFilterEngine()
    res = SymbolScanResult(symbol="A", status=ScanCandidateStatus.PASSED)
    assert engine.should_include_in_top(res) is True

def test_should_include_in_top_watch_only_enabled():
    class MockSettings:
        SCANNER_INCLUDE_WATCH_ONLY = True

    engine = ScanFilterEngine(settings=MockSettings())
    res = SymbolScanResult(symbol="A", status=ScanCandidateStatus.WATCH_ONLY)
    assert engine.should_include_in_top(res) is True

def test_should_include_in_top_watch_only_disabled():
    class MockSettings:
        SCANNER_INCLUDE_WATCH_ONLY = False

    engine = ScanFilterEngine(settings=MockSettings())
    res = SymbolScanResult(symbol="A", status=ScanCandidateStatus.WATCH_ONLY)
    assert engine.should_include_in_top(res) is False

def test_should_include_in_top_other_status():
    engine = ScanFilterEngine()

    res1 = SymbolScanResult(symbol="A", status=ScanCandidateStatus.ERROR)
    assert engine.should_include_in_top(res1) is False

    res2 = SymbolScanResult(symbol="A", status=ScanCandidateStatus.REJECTED)
    assert engine.should_include_in_top(res2) is False

    res3 = SymbolScanResult(symbol="A", status=ScanCandidateStatus.FILTERED)
    assert engine.should_include_in_top(res3) is False

def test_filter_results_list():
    engine = ScanFilterEngine()
    req = ScanRequest(strategy_name="t", universe_mode=ScanUniverseMode.ALL)
    res1 = SymbolScanResult(symbol="A", status=ScanCandidateStatus.ERROR)
    res2 = SymbolScanResult(symbol="B", status=ScanCandidateStatus.ERROR)

    out = engine.filter_results([res1, res2], req)

    assert len(out) == 2
    assert out[0].symbol == "A"
    assert out[1].symbol == "B"

def test_filter_results_comprehensive():
    engine = ScanFilterEngine()
    req = ScanRequest(strategy_name="t", universe_mode=ScanUniverseMode.ALL, min_signal_score=50.0, min_confidence=50.0)

    # 1. Error Status
    res_err = SymbolScanResult(symbol="ERR", status=ScanCandidateStatus.ERROR)

    # 2. No Signal
    res_no_sig = SymbolScanResult(symbol="NO_SIG", status=ScanCandidateStatus.PASSED, signal=None)

    # 3. Filtered (low score)
    sig_low_score = SignalCandidate(strategy_name="t", symbol="LOW_SCORE", direction=SignalDirection.LONG, score=40.0, confidence=80.0, strength=SignalStrength.STRONG)
    res_low_score = SymbolScanResult(symbol="LOW_SCORE", status=ScanCandidateStatus.PASSED, signal=sig_low_score)

    # 4. Filtered (low confidence)
    sig_low_conf = SignalCandidate(strategy_name="t", symbol="LOW_CONF", direction=SignalDirection.LONG, score=80.0, confidence=40.0, strength=SignalStrength.STRONG)
    res_low_conf = SymbolScanResult(symbol="LOW_CONF", status=ScanCandidateStatus.PASSED, signal=sig_low_conf)

    # 5. Watch Only
    sig_watch = SignalCandidate(strategy_name="t", symbol="WATCH", direction=SignalDirection.WATCH, score=80.0, confidence=80.0, strength=SignalStrength.STRONG)
    res_watch = SymbolScanResult(symbol="WATCH", status=ScanCandidateStatus.PASSED, signal=sig_watch)

    # 6. Rejected (Risk)
    sig_risk = SignalCandidate(strategy_name="t", symbol="RISK", direction=SignalDirection.LONG, score=80.0, confidence=80.0, strength=SignalStrength.STRONG)
    risk_dec = RiskDecision(signal=sig_risk, side=sig_risk.direction, approved=False, filter_result=RiskFilterResult(status=RiskDecisionStatus.REJECTED, passed=False, active_rules=[], triggered_rules=[]), symbol="RISK", strategy_name="t", status=RiskDecisionStatus.REJECTED)
    res_risk = SymbolScanResult(symbol="RISK", status=ScanCandidateStatus.PASSED, signal=sig_risk, risk_decision=risk_dec)

    # 7. Rejected (Forbidden Claim)
    sig_forbidden = SignalCandidate(strategy_name="t", symbol="FORBIDDEN", direction=SignalDirection.LONG, score=80.0, confidence=80.0, strength=SignalStrength.STRONG, metadata={"claim": "kesin al"})
    res_forbidden = SymbolScanResult(symbol="FORBIDDEN", status=ScanCandidateStatus.PASSED, signal=sig_forbidden)

    # 8. Passed
    sig_pass = SignalCandidate(strategy_name="t", symbol="PASS", direction=SignalDirection.LONG, score=80.0, confidence=80.0, strength=SignalStrength.STRONG)
    res_pass = SymbolScanResult(symbol="PASS", status=ScanCandidateStatus.PASSED, signal=sig_pass)

    out = engine.filter_results(
        [res_err, res_no_sig, res_low_score, res_low_conf, res_watch, res_risk, res_forbidden, res_pass],
        req
    )

    assert len(out) == 8

    assert out[0].symbol == "ERR"
    assert out[0].status == ScanCandidateStatus.ERROR

    assert out[1].symbol == "NO_SIG"
    assert out[1].status == ScanCandidateStatus.FILTERED

    assert out[2].symbol == "LOW_SCORE"
    assert out[2].status == ScanCandidateStatus.FILTERED

    assert out[3].symbol == "LOW_CONF"
    assert out[3].status == ScanCandidateStatus.FILTERED

    assert out[4].symbol == "WATCH"
    assert out[4].status == ScanCandidateStatus.WATCH_ONLY

    assert out[5].symbol == "RISK"
    assert out[5].status == ScanCandidateStatus.REJECTED

    assert out[6].symbol == "FORBIDDEN"
    assert out[6].status == ScanCandidateStatus.REJECTED

    assert out[7].symbol == "PASS"
    assert out[7].status == ScanCandidateStatus.PASSED
