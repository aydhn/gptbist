import pytest
from bist_signal_bot.scanner.models import ScanReport, ScanRequest, ScanUniverseMode
from bist_signal_bot.scanner.reporting import format_scan_markdown, scan_report_to_dict

def test_markdown_format():
    req = ScanRequest(strategy_name="test", universe_mode=ScanUniverseMode.ALL)
    report = ScanReport(request=req)
    md = format_scan_markdown(report)
    assert "Signal scan research output only" in md
    assert "test" in md

def test_scan_report_to_dict():
    req = ScanRequest(strategy_name="dict_test", universe_mode=ScanUniverseMode.SYMBOLS)
    report = ScanReport(request=req, total_symbols=5)
    data = scan_report_to_dict(report)
    assert isinstance(data, dict)
    assert "request" in data
    assert data["request"]["strategy_name"] == "dict_test"
    assert data["total_symbols"] == 5

import pandas as pd
from bist_signal_bot.scanner.reporting import scan_results_to_dataframe
from bist_signal_bot.scanner.models import SymbolScanResult, ScanCandidateStatus
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection, SignalStrength
from bist_signal_bot.risk.models import RiskDecision, RiskDecisionStatus, RiskSide, RiskFilterResult

def test_scan_results_to_dataframe():
    sig = SignalCandidate(
        strategy_name="test",
        symbol="ASELS",
        direction=SignalDirection.LONG,
        score=85.0,
        confidence=80.0,
        strength=SignalStrength.UNKNOWN
    )
    risk = RiskDecision(
        signal=sig,
        status=RiskDecisionStatus.APPROVED,
        side=RiskSide.LONG,
        approved=True,
        filter_result=RiskFilterResult(passed=True, status=RiskDecisionStatus.APPROVED),
        final_score=82.0
    )
    res_full = SymbolScanResult(
        symbol="ASELS",
        status=ScanCandidateStatus.PASSED,
        signal=sig,
        risk_decision=risk,
        rank=1,
        rank_score=85.0,
        reasons=["Reason 1", "Reason 2"],
        portfolio_status="OK",
        elapsed_seconds=1.5
    )
    res_empty = SymbolScanResult(
        symbol="THYAO",
        status=ScanCandidateStatus.REJECTED,
        signal=None,
        risk_decision=None,
        rank=None,
        rank_score=None,
        reasons=[],
        elapsed_seconds=0.5
    )

    df = scan_results_to_dataframe([res_full, res_empty])
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2

    row_full = df[df["symbol"] == "ASELS"].iloc[0]
    assert row_full["status"] == "PASSED"
    assert row_full["signal_intent"] == "LONG"
    assert row_full["signal_score"] == 85.0
    assert row_full["confidence"] == 80.0
    assert row_full["risk_status"] == "APPROVED"
    assert row_full["final_score"] == 82.0
    assert row_full["reasons"] == "Reason 1 | Reason 2"
    assert row_full["elapsed_s"] == 1.5
    assert row_full["portfolio_status"] == "OK"
    assert row_full["rank"] == 1
    assert row_full["rank_score"] == 85.0

    row_empty = df[df["symbol"] == "THYAO"].iloc[0]
    assert row_empty["status"] == "REJECTED"
    assert pd.isna(row_empty["signal_intent"]) or row_empty["signal_intent"] is None
    assert pd.isna(row_empty["signal_score"]) or row_empty["signal_score"] is None
    assert pd.isna(row_empty["confidence"]) or row_empty["confidence"] is None
    assert pd.isna(row_empty["risk_status"]) or row_empty["risk_status"] is None
    assert pd.isna(row_empty["final_score"]) or row_empty["final_score"] is None
    assert row_empty["reasons"] == ""
    assert row_empty["elapsed_s"] == 0.5
    assert pd.isna(row_empty["portfolio_status"]) or row_empty["portfolio_status"] is None
