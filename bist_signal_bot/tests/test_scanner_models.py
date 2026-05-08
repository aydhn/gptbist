import pytest
from bist_signal_bot.scanner.models import (
    ScanRequest, SymbolScanResult, ScanReport, ScanUniverseMode,
    ScanCandidateStatus, ScanStatus, ScanSortKey
)
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection, SignalStrength
from bist_signal_bot.risk.models import RiskDecision, RiskDecisionStatus

def test_scan_request_validation():
    req = ScanRequest(strategy_name="test", universe_mode=ScanUniverseMode.SYMBOLS, symbols=["ASELS"])
    assert req.strategy_name == "test"
    assert req.universe_mode == ScanUniverseMode.SYMBOLS
    assert req.symbols == ["ASELS"]

def test_scan_report_summary():
    req = ScanRequest(strategy_name="test", universe_mode=ScanUniverseMode.ALL)
    report = ScanReport(request=req, status=ScanStatus.SUCCESS, total_symbols=10, passed_count=2)
    summ = report.summary()
    assert summ["status"] == "SUCCESS"
    assert summ["total_symbols"] == 10
    assert summ["passed"] == 2

def test_symbol_scan_result_summary():
    sig = SignalCandidate(
        strategy_name="test",
        symbol="ASELS",
        direction=SignalDirection.LONG,
        score=85.0,
        confidence=80.0,
        strength=SignalStrength.STRONG
    )
    res = SymbolScanResult(
        symbol="ASELS",
        status=ScanCandidateStatus.PASSED,
        signal=sig,
        rank=1,
        rank_score=85.0
    )
    summ = res.summary()
    assert summ["symbol"] == "ASELS"
    assert summ["status"] == "PASSED"
    assert summ["signal_score"] == 85.0
    assert summ["rank"] == 1
