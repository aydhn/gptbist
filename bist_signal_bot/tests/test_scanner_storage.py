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
