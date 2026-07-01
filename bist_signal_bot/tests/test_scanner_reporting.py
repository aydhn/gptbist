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
