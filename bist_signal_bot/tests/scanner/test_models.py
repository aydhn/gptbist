import pytest
from datetime import datetime
from bist_signal_bot.scanner.models import (
    ScanUniverseMode,
    ScanStatus,
    ScanCandidateStatus,
    ScanSortKey,
    ScanRequest,
    SymbolScanIssue,
    SymbolScanResult,
    ScanRankingItem,
    ScanReport,
)
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection

def test_scan_request_defaults():
    request = ScanRequest(
        strategy_name="test_strat",
        universe_mode=ScanUniverseMode.SYMBOLS
    )
    assert request.strategy_name == "test_strat"
    assert request.universe_mode == ScanUniverseMode.SYMBOLS
    assert request.symbols == []
    assert request.source == "mock"
    assert request.timeframe == "1d"
    assert request.use_trade_risk is True
    assert request.use_portfolio_risk is True
    assert request.use_paper is False
    assert request.top_n == 10
    assert request.sort_key == ScanSortKey.FINAL_SCORE
    assert request.descending is True
    assert request.continue_on_error is True

def test_symbol_scan_result_summary():
    signal = SignalCandidate(
        symbol="AAPL",
        strategy_name="test",
        direction=SignalDirection.LONG,
        score=85.0
    )

    result = SymbolScanResult(
        symbol="AAPL",
        status=ScanCandidateStatus.PASSED,
        signal=signal,
        rank=1,
        rank_score=90.0,
        elapsed_seconds=1.5
    )

    summary = result.summary()
    assert summary["symbol"] == "AAPL"
    assert summary["status"] == ScanCandidateStatus.PASSED.value
    assert summary["signal_intent"] == SignalDirection.LONG.value
    assert summary["signal_score"] == 85.0
    assert summary["final_score"] is None
    assert summary["portfolio_status"] is None
    assert summary["rank"] == 1
    assert summary["rank_score"] == 90.0
    assert summary["elapsed_seconds"] == 1.5

def test_scan_report_summary():
    request = ScanRequest(
        strategy_name="test_strat",
        universe_mode=ScanUniverseMode.ALL
    )

    report = ScanReport(
        request=request,
        status=ScanStatus.SUCCESS,
        total_symbols=100,
        processed_symbols=100,
        passed_count=10,
        filtered_count=80,
        rejected_count=5,
        error_count=5,
        elapsed_seconds=10.5
    )

    summary = report.summary()
    assert summary["status"] == ScanStatus.SUCCESS.value
    assert summary["strategy"] == "test_strat"
    assert summary["total_symbols"] == 100
    assert summary["processed"] == 100
    assert summary["passed"] == 10
    assert summary["filtered"] == 80
    assert summary["rejected"] == 5
    assert summary["error"] == 5
    assert summary["elapsed_seconds"] == 10.5
    assert summary["output_files"] == {}

def test_scan_report_top_candidates():
    request = ScanRequest(strategy_name="test_strat", universe_mode=ScanUniverseMode.ALL)

    r1 = SymbolScanResult(symbol="AAPL", status=ScanCandidateStatus.PASSED, rank=2)
    r2 = SymbolScanResult(symbol="MSFT", status=ScanCandidateStatus.PASSED, rank=1)
    r3 = SymbolScanResult(symbol="GOOG", status=ScanCandidateStatus.REJECTED, rank=3)
    r4 = SymbolScanResult(symbol="AMZN", status=ScanCandidateStatus.PASSED, rank=None)

    report = ScanReport(
        request=request,
        results=[r1, r2, r3, r4]
    )

    top = report.top_candidates()
    # Should only include PASSED, sorted by rank (None at the end)
    assert len(top) == 3
    assert top[0].symbol == "MSFT"
    assert top[1].symbol == "AAPL"
    assert top[2].symbol == "AMZN"

    top_2 = report.top_candidates(n=2)
    assert len(top_2) == 2
    assert top_2[0].symbol == "MSFT"
    assert top_2[1].symbol == "AAPL"

def test_scan_report_safe_public_dict():
    request = ScanRequest(strategy_name="test", universe_mode=ScanUniverseMode.ALL)
    report = ScanReport(request=request)

    # safe_public_dict is an alias to summary
    assert report.safe_public_dict() == report.summary()
