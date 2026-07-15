import pytest
import pandas as pd
from datetime import datetime, timezone
from bist_signal_bot.scanner.models import (
    ScanReport, ScanRequest, ScanUniverseMode, SymbolScanResult,
    ScanCandidateStatus, ScanRankingItem, SymbolScanIssue
)
from bist_signal_bot.scanner.reporting import (
    format_scan_markdown, scan_report_to_dict, scan_results_to_dataframe,
    scan_rankings_to_dataframe, scan_issues_to_dataframe, format_scan_report_text
)
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection, SignalStrength
from bist_signal_bot.risk.models import RiskDecision, RiskDecisionStatus, RiskSide, RiskFilterResult
from bist_signal_bot.portfolio.models import PortfolioRiskDecision, PortfolioState, AllocationResult, AllocationMethod, ExposureReport, PortfolioDecisionStatus

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
    assert "results" in data
    assert isinstance(data["results"], list)

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

def test_scan_rankings_to_dataframe():
    item1 = ScanRankingItem(symbol="AAPL", rank_score=85.5, rank=1, status="PASSED")
    item2 = ScanRankingItem(symbol="MSFT", rank_score=80.0, rank=2, status="PASSED")

    df = scan_rankings_to_dataframe([item1, item2])
    assert len(df) == 2
    assert "symbol" in df.columns
    assert "rank_score" in df.columns
    assert df.iloc[0]["symbol"] == "AAPL"
    assert df.iloc[1]["symbol"] == "MSFT"

def test_scan_issues_to_dataframe():
    issue1 = SymbolScanIssue(symbol="AAPL", stage="DATA", message="Missing data", severity="ERROR")
    issue2 = SymbolScanIssue(symbol="MSFT", stage="SIGNAL", message="Low volume", severity="WARNING")

    df = scan_issues_to_dataframe([issue1, issue2])
    assert len(df) == 2
    assert "symbol" in df.columns
    assert "stage" in df.columns
    assert df.iloc[0]["symbol"] == "AAPL"
    assert df.iloc[1]["symbol"] == "MSFT"

def test_markdown_format_with_empty_report():
    req = ScanRequest(strategy_name="md_empty", universe_mode=ScanUniverseMode.SYMBOLS, top_n=2)
    report = ScanReport(request=req, results=[], issues=[])

    md = format_scan_markdown(report)
    assert "No passed candidates found." not in md

    text = format_scan_report_text(report)
    assert "No passed candidates found." in text

def test_markdown_format_with_full_report():
    req = ScanRequest(strategy_name="md_test", universe_mode=ScanUniverseMode.SYMBOLS, top_n=2)

    sig1 = SignalCandidate(symbol="AAPL", strategy_name="md_test", direction=SignalDirection.LONG, score=90, strength=SignalStrength.UNKNOWN)
    risk1 = RiskDecision(signal=sig1, status=RiskDecisionStatus.APPROVED, side=RiskSide.LONG, approved=True, filter_result=RiskFilterResult(passed=True, status=RiskDecisionStatus.APPROVED), final_score=82.0)
    res1 = SymbolScanResult(symbol="AAPL", status=ScanCandidateStatus.PASSED, rank=1, rank_score=90.0, signal=sig1, risk_decision=risk1)

    sig2 = SignalCandidate(symbol="MSFT", strategy_name="md_test", direction=SignalDirection.LONG, score=85, strength=SignalStrength.UNKNOWN)
    risk2 = RiskDecision(signal=sig2, status=RiskDecisionStatus.APPROVED, side=RiskSide.LONG, approved=True, filter_result=RiskFilterResult(passed=True, status=RiskDecisionStatus.APPROVED), final_score=80.0)
    res2 = SymbolScanResult(symbol="MSFT", status=ScanCandidateStatus.PASSED, rank=2, rank_score=85.0, signal=sig2, risk_decision=risk2)

    portfolio_state = PortfolioState(equity=100000, cash=100000)
    alloc_res = AllocationResult(method=AllocationMethod.EQUAL_WEIGHT, items=[], total_allocated_notional=0.0, total_allocated_pct=0.0, rejected_symbols=[], reduced_symbols=[], issues=[], generated_at=datetime.now(timezone.utc))
    exp_report = ExposureReport(gross_exposure_pct=0.0, net_exposure_pct=0.0, long_exposure_pct=0.0, short_exposure_pct=0.0, max_symbol_weight_pct=0.0, sector_weights={}, open_position_count=0, cash_pct=1.0, issues=[], metadata={})

    portfolio_dec = PortfolioRiskDecision(
        portfolio_state=portfolio_state, input_signals=[sig1, sig2], trade_risk_decisions=[],
        allocation_result=alloc_res, exposure_report_before=exp_report, exposure_report_after=exp_report,
        correlation_result=None, status=PortfolioDecisionStatus.APPROVED, approved_count=2, rejected_count=0,
        reduced_count=0, reject_reasons=["Reason 1"], warnings=[], generated_at=datetime.now(timezone.utc)
    )

    issue1 = SymbolScanIssue(symbol="AAPL", stage="DATA", message="Missing data", severity="ERROR")

    report = ScanReport(request=req, results=[res1, res2], portfolio_decision=portfolio_dec, issues=[issue1])

    md = format_scan_markdown(report)
    assert "# BIST Bot Signal Scan Report" in md
    assert "**Strategy**: `md_test`" in md
    assert "| 1 | AAPL | LONG | 90.0 | 82.0 | PASSED |" in md
    assert "| 2 | MSFT | LONG | 85.0 | 80.0 | PASSED |" in md
    assert "## Portfolio Risk Summary" in md
    assert "Status: **APPROVED**" in md
    assert "- Reason 1" in md
    assert "## Issues" in md
    assert "- **ERROR** [DATA] AAPL: Missing data" in md

def test_text_format_with_full_report():
    req = ScanRequest(strategy_name="text_test", universe_mode=ScanUniverseMode.SYMBOLS, top_n=2)

    sig1 = SignalCandidate(symbol="AAPL", strategy_name="text_test", direction=SignalDirection.LONG, score=90, strength=SignalStrength.UNKNOWN)
    risk1 = RiskDecision(signal=sig1, status=RiskDecisionStatus.APPROVED, side=RiskSide.LONG, approved=True, filter_result=RiskFilterResult(passed=True, status=RiskDecisionStatus.APPROVED), final_score=82.0)
    res1 = SymbolScanResult(symbol="AAPL", status=ScanCandidateStatus.PASSED, rank=1, rank_score=90.0, signal=sig1, risk_decision=risk1)

    portfolio_state = PortfolioState(equity=100000, cash=100000)
    alloc_res = AllocationResult(method=AllocationMethod.EQUAL_WEIGHT, items=[], total_allocated_notional=0.0, total_allocated_pct=0.0, rejected_symbols=[], reduced_symbols=[], issues=[], generated_at=datetime.now(timezone.utc))
    exp_report = ExposureReport(gross_exposure_pct=0.0, net_exposure_pct=0.0, long_exposure_pct=0.0, short_exposure_pct=0.0, max_symbol_weight_pct=0.0, sector_weights={}, open_position_count=0, cash_pct=1.0, issues=[], metadata={})

    portfolio_dec = PortfolioRiskDecision(
        portfolio_state=portfolio_state, input_signals=[sig1], trade_risk_decisions=[],
        allocation_result=alloc_res, exposure_report_before=exp_report, exposure_report_after=exp_report,
        correlation_result=None, status=PortfolioDecisionStatus.APPROVED, approved_count=1, rejected_count=0,
        reduced_count=0, reject_reasons=["Reason 1"], warnings=[], generated_at=datetime.now(timezone.utc)
    )

    report = ScanReport(request=req, results=[res1], portfolio_decision=portfolio_dec, issues=[])

    text = format_scan_report_text(report)
    assert "Strategy: text_test" in text
    assert "  1. AAPL - LONG - Score: 90.0 - Status: PASSED" in text
    assert "Portfolio Risk Summary:" in text
    assert "  Status: APPROVED" in text
    assert "  Allocations: 0" in text
