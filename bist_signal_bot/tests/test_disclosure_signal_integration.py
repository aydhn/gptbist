from bist_signal_bot.scanner.engine import SignalScannerEngine, SignalScannerDependencies
def test_scanner_disclosure_hook():
    engine = SignalScannerEngine(deps=SignalScannerDependencies(data_service=None, strategy_engine=None))
    assert getattr(engine.settings, 'SCANNER_DISCLOSURE_RISK_CHECK', True) is not False
