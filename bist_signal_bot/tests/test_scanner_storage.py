import pytest
import os
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.scanner.storage import ScanReportStore
from bist_signal_bot.scanner.models import ScanReport, ScanRequest, ScanUniverseMode

def test_scan_report_store_save(tmp_path):
    settings = Settings()
    store = ScanReportStore(settings, base_dir=tmp_path)
    req = ScanRequest(strategy_name="test_strat", universe_mode=ScanUniverseMode.SYMBOLS, symbols=["A"])
    report = ScanReport(request=req)

    paths = store.save_report(report, formats=["json", "csv", "markdown"])

    assert "json" in paths
    assert "markdown" in paths
    assert os.path.exists(paths["json"])
    assert os.path.exists(paths["markdown"])

def test_get_scans_dir(tmp_path):
    settings = Settings()
    store = ScanReportStore(settings, base_dir=tmp_path)

    scans_dir = store.get_scans_dir()

    assert scans_dir == tmp_path
    assert isinstance(scans_dir, type(tmp_path))

import pandas as pd
from bist_signal_bot.scanner.models import ScanRankingItem, SymbolScanResult, SymbolScanIssue, ScanCandidateStatus

def test_scan_report_store_save_csv(tmp_path):
    settings = Settings()
    store = ScanReportStore(settings, base_dir=tmp_path)
    req = ScanRequest(strategy_name="test_strat", universe_mode=ScanUniverseMode.SYMBOLS, symbols=["A"])

    # Create sample rankings
    rankings = [
        ScanRankingItem(symbol="A", rank=1, rank_score=95.0, signal_score=90.0, final_score=92.5, status="PASSED"),
        ScanRankingItem(symbol="B", rank=2, rank_score=85.0, signal_score=80.0, final_score=82.5, status="REJECTED")
    ]

    # Create sample results
    results = [
        SymbolScanResult(symbol="A", status=ScanCandidateStatus.PASSED, rank=1, rank_score=95.0),
        SymbolScanResult(symbol="B", status=ScanCandidateStatus.REJECTED, rank=2, rank_score=85.0)
    ]

    # Create sample issues
    issues = [
        SymbolScanIssue(symbol="A", stage="signal", message="Warning: low volume", severity="WARN"),
        SymbolScanIssue(symbol="B", stage="risk", message="Rejected due to high volatility", severity="ERROR")
    ]

    report = ScanReport(
        request=req,
        rankings=rankings,
        results=results,
        issues=issues
    )

    # Use the method directly
    paths = store.save_csv(report)

    # Check that all files were created
    assert "rankings" in paths
    assert "results" in paths
    assert "issues" in paths

    assert os.path.exists(paths["rankings"])
    assert os.path.exists(paths["results"])
    assert os.path.exists(paths["issues"])

    # Verify contents
    df_rankings = pd.read_csv(paths["rankings"])
    assert len(df_rankings) == 2
    assert list(df_rankings["symbol"]) == ["A", "B"]
    assert list(df_rankings["rank"]) == [1, 2]

    df_results = pd.read_csv(paths["results"])
    assert len(df_results) == 2
    assert list(df_results["symbol"]) == ["A", "B"]
    assert list(df_results["status"]) == ["PASSED", "REJECTED"]

    df_issues = pd.read_csv(paths["issues"])
    assert len(df_issues) == 2
    assert list(df_issues["symbol"]) == ["A", "B"]
    assert list(df_issues["stage"]) == ["signal", "risk"]

def test_scan_report_store_save_csv_empty(tmp_path):
    settings = Settings()
    store = ScanReportStore(settings, base_dir=tmp_path)
    req = ScanRequest(strategy_name="test_strat", universe_mode=ScanUniverseMode.SYMBOLS, symbols=["A"])

    # Empty report (no rankings, results, issues)
    report = ScanReport(request=req)

    # Use the method directly
    paths = store.save_csv(report)

    # Check that no files were created
    assert "rankings" not in paths
    assert "results" not in paths
    assert "issues" not in paths
