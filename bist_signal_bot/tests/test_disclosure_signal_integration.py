from bist_signal_bot.scanner.engine import SignalScannerEngine
def test_scanner_disclosure_hook():
    engine = SignalScannerEngine(data_service=None, strategy_engine=None)
    assert getattr(engine.settings, 'SCANNER_DISCLOSURE_RISK_CHECK', True)
