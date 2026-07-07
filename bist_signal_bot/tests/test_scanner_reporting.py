import pytest
import pandas as pd
from bist_signal_bot.scanner.models import ScanReport, ScanRequest, ScanUniverseMode, ScanRankingItem
from bist_signal_bot.scanner.reporting import format_scan_markdown, scan_report_to_dict, scan_rankings_to_dataframe

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

def test_scan_rankings_to_dataframe():
    items = [
        ScanRankingItem(symbol="AAPL", rank_score=100.5, rank=1, signal_score=0.9, status="ACTIVE"),
        ScanRankingItem(symbol="MSFT", rank_score=80.2, rank=2, status="ACTIVE")
    ]
    df = scan_rankings_to_dataframe(items)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "symbol" in df.columns
    assert df.iloc[0]["symbol"] == "AAPL"
    assert df.iloc[1]["symbol"] == "MSFT"
    assert df.iloc[0]["rank_score"] == 100.5
    assert df.iloc[0]["rank"] == 1

    # Test empty list
    df_empty = scan_rankings_to_dataframe([])
    assert isinstance(df_empty, pd.DataFrame)
    assert len(df_empty) == 0
