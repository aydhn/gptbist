import pytest
from bist_signal_bot.scanner.models import ScanReport, ScanRequest, ScanUniverseMode
from bist_signal_bot.scanner.reporting import format_scan_markdown

def test_markdown_format():
    req = ScanRequest(strategy_name="test", universe_mode=ScanUniverseMode.ALL)
    report = ScanReport(request=req)
    md = format_scan_markdown(report)
    assert "Signal scan research output only" in md
    assert "test" in md
