import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.scanner.filters import ScanFilterEngine
from bist_signal_bot.scanner.models import (
    SymbolScanResult, ScanRequest, ScanCandidateStatus, ScanUniverseMode
)
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection
from bist_signal_bot.risk.models import RiskDecision, RiskDecisionStatus, RiskSide

@pytest.fixture
def filter_engine():
    return ScanFilterEngine()

@pytest.fixture
def default_request():
    return ScanRequest(
        strategy_name="test_strategy",
        universe_mode=ScanUniverseMode.SYMBOLS,
        min_signal_score=50.0,
        min_confidence=40.0,
        min_final_score=50.0
    )

def test_filter_engine_initialization(filter_engine):
    assert filter_engine.settings is not None

def test_filter_error_status(filter_engine, default_request):
    result = SymbolScanResult(symbol="TEST", status=ScanCandidateStatus.ERROR)
    filtered = filter_engine.filter_symbol_result(result, default_request)
    assert filtered.status == ScanCandidateStatus.ERROR

def test_filter_no_signal(filter_engine, default_request):
    result = SymbolScanResult(symbol="TEST", status=ScanCandidateStatus.PASSED, signal=None)
    filtered = filter_engine.filter_symbol_result(result, default_request)
    assert filtered.status == ScanCandidateStatus.FILTERED
    assert "No signal generated" in filtered.reasons[0]

def test_filter_low_signal_score(filter_engine, default_request):
    signal = SignalCandidate(symbol="TEST", strategy="test", strategy_name="test", direction=SignalDirection.LONG, score=40.0, confidence=50.0)
    result = SymbolScanResult(symbol="TEST", status=ScanCandidateStatus.PASSED, signal=signal)
    filtered = filter_engine.filter_symbol_result(result, default_request)
    assert filtered.status == ScanCandidateStatus.FILTERED
    assert "Signal score 40.0 < min 50.0" in filtered.reasons[0]

def test_filter_low_confidence(filter_engine, default_request):
    signal = SignalCandidate(symbol="TEST", strategy="test", strategy_name="test", direction=SignalDirection.LONG, score=60.0, confidence=30.0)
    result = SymbolScanResult(symbol="TEST", status=ScanCandidateStatus.PASSED, signal=signal)
    filtered = filter_engine.filter_symbol_result(result, default_request)
    assert filtered.status == ScanCandidateStatus.FILTERED
    assert "Confidence 30.0 < min 40.0" in filtered.reasons[0]

def test_filter_watch_only_direction(filter_engine, default_request):
    for direction in [SignalDirection.WATCH, SignalDirection.FLAT, SignalDirection.AVOID]:
        signal = SignalCandidate(symbol="TEST", strategy="test", strategy_name="test", direction=direction, score=60.0, confidence=50.0)
        result = SymbolScanResult(symbol="TEST", status=ScanCandidateStatus.PASSED, signal=signal)
        filtered = filter_engine.filter_symbol_result(result, default_request)
        assert filtered.status == ScanCandidateStatus.WATCH_ONLY
        assert f"Direction is {direction.value}" in filtered.reasons[0]

def test_filter_risk_rejected(filter_engine, default_request):
    signal = SignalCandidate(symbol="TEST", strategy="test", strategy_name="test", direction=SignalDirection.LONG, score=60.0, confidence=50.0)
    risk_decision = RiskDecision(signal=signal, side=RiskSide.LONG, approved=False, status=RiskDecisionStatus.REJECTED, filter_result={"passed": False, "status": RiskDecisionStatus.REJECTED, "reject_reasons": []})
    result = SymbolScanResult(symbol="TEST", status=ScanCandidateStatus.PASSED, signal=signal, risk_decision=risk_decision)
    filtered = filter_engine.filter_symbol_result(result, default_request)
    assert filtered.status == ScanCandidateStatus.REJECTED
    assert "Risk engine rejected: Unknown" in filtered.reasons[0]

def test_filter_risk_low_final_score(filter_engine, default_request):
    signal = SignalCandidate(symbol="TEST", strategy="test", strategy_name="test", direction=SignalDirection.LONG, score=60.0, confidence=50.0)
    risk_decision = RiskDecision(signal=signal, side=RiskSide.LONG, approved=True, status=RiskDecisionStatus.APPROVED, filter_result={"passed": True, "status": RiskDecisionStatus.APPROVED, "reject_reasons": []}, final_score=40.0)
    result = SymbolScanResult(symbol="TEST", status=ScanCandidateStatus.PASSED, signal=signal, risk_decision=risk_decision)
    filtered = filter_engine.filter_symbol_result(result, default_request)
    assert filtered.status == ScanCandidateStatus.FILTERED
    assert "Final score 40.0 < min 50.0" in filtered.reasons[0]

def test_filter_forbidden_claims(filter_engine, default_request):
    signal = SignalCandidate(symbol="TEST", strategy="test", strategy_name="test", direction=SignalDirection.LONG, score=60.0, confidence=50.0, metadata={"claim": "Bu kesin al firsati"})
    result = SymbolScanResult(symbol="TEST", status=ScanCandidateStatus.PASSED, signal=signal)
    filtered = filter_engine.filter_symbol_result(result, default_request)
    assert filtered.status == ScanCandidateStatus.REJECTED
    assert "Forbidden claim detected in signal metadata" in filtered.reasons[0]

def test_filter_passed(filter_engine, default_request):
    signal = SignalCandidate(symbol="TEST", strategy="test", strategy_name="test", direction=SignalDirection.LONG, score=60.0, confidence=50.0)
    risk_decision = RiskDecision(signal=signal, side=RiskSide.LONG, approved=True, status=RiskDecisionStatus.APPROVED, filter_result={"passed": True, "status": RiskDecisionStatus.APPROVED, "reject_reasons": []}, final_score=60.0)
    result = SymbolScanResult(symbol="TEST", status=ScanCandidateStatus.PASSED, signal=signal, risk_decision=risk_decision)
    filtered = filter_engine.filter_symbol_result(result, default_request)
    assert filtered.status == ScanCandidateStatus.PASSED
    assert len(filtered.reasons) == 0

def test_filter_results_batch(filter_engine, default_request):
    signal1 = SignalCandidate(symbol="TEST1", strategy="test", strategy_name="test", direction=SignalDirection.LONG, score=60.0, confidence=50.0)
    signal2 = SignalCandidate(symbol="TEST2", strategy="test", strategy_name="test", direction=SignalDirection.LONG, score=40.0, confidence=50.0)

    results = [
        SymbolScanResult(symbol="TEST1", status=ScanCandidateStatus.PASSED, signal=signal1),
        SymbolScanResult(symbol="TEST2", status=ScanCandidateStatus.PASSED, signal=signal2)
    ]

    filtered_results = filter_engine.filter_results(results, default_request)
    assert len(filtered_results) == 2
    assert filtered_results[0].status == ScanCandidateStatus.PASSED
    assert filtered_results[1].status == ScanCandidateStatus.FILTERED

def test_should_include_in_top(filter_engine):
    # Passed status
    passed_result = SymbolScanResult(symbol="TEST", status=ScanCandidateStatus.PASSED)
    assert filter_engine.should_include_in_top(passed_result) is True

    # Watch only status with setting enabled
    filter_engine.settings.SCANNER_INCLUDE_WATCH_ONLY = True
    watch_result = SymbolScanResult(symbol="TEST", status=ScanCandidateStatus.WATCH_ONLY)
    assert filter_engine.should_include_in_top(watch_result) is True

    # Watch only status with setting disabled
    filter_engine.settings.SCANNER_INCLUDE_WATCH_ONLY = False
    assert filter_engine.should_include_in_top(watch_result) is False

    # Other statuses
    for status in [ScanCandidateStatus.FILTERED, ScanCandidateStatus.REJECTED, ScanCandidateStatus.ERROR]:
        result = SymbolScanResult(symbol="TEST", status=status)
        assert filter_engine.should_include_in_top(result) is False
