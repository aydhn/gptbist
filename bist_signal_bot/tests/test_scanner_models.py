from bist_signal_bot.scanner.models import (
    ScanRequest, SymbolScanResult, ScanReport, ScanUniverseMode,
    ScanCandidateStatus, ScanStatus
)
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection, SignalStrength

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

def test_scan_report_safe_public_dict():
    req = ScanRequest(strategy_name="test_safe_dict", universe_mode=ScanUniverseMode.ALL)
    report = ScanReport(request=req, status=ScanStatus.SUCCESS, total_symbols=15, passed_count=5)

    summary = report.summary()
    safe_dict = report.safe_public_dict()

    assert safe_dict == summary
    assert safe_dict["status"] == "SUCCESS"
    assert safe_dict["strategy"] == "test_safe_dict"
    assert safe_dict["total_symbols"] == 15
    assert safe_dict["passed"] == 5

def test_scan_report_top_candidates():
    req = ScanRequest(strategy_name="test", universe_mode=ScanUniverseMode.ALL)

    res1 = SymbolScanResult(symbol="SYM1", status=ScanCandidateStatus.PASSED, rank=2)
    res2 = SymbolScanResult(symbol="SYM2", status=ScanCandidateStatus.FILTERED, rank=1)
    res3 = SymbolScanResult(symbol="SYM3", status=ScanCandidateStatus.PASSED, rank=1)
    res4 = SymbolScanResult(symbol="SYM4", status=ScanCandidateStatus.PASSED, rank=None)
    res5 = SymbolScanResult(symbol="SYM5", status=ScanCandidateStatus.PASSED, rank=3)

    report = ScanReport(
        request=req,
        status=ScanStatus.SUCCESS,
        results=[res1, res2, res3, res4, res5]
    )

    candidates = report.top_candidates()
    assert len(candidates) == 4
    assert candidates[0].symbol == "SYM3"
    assert candidates[1].symbol == "SYM1"
    assert candidates[2].symbol == "SYM5"
    assert candidates[3].symbol == "SYM4"

    limited = report.top_candidates(n=2)
    assert len(limited) == 2
    assert limited[0].symbol == "SYM3"
    assert limited[1].symbol == "SYM1"
