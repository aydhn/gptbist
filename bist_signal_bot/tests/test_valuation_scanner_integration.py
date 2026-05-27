from unittest.mock import patch, MagicMock
from bist_signal_bot.scanner.engine import SignalScannerEngine

def test_scanner_valuation_injection():
    # Because we added a method to the engine
    engine = SignalScannerEngine(None, None, None, None, None, None, None, None)
    engine.settings = MagicMock()
    engine.settings.SCANNER_INCLUDE_VALUATION_CONTEXT = True

    # We monkey-patched models to add fields
    from bist_signal_bot.scanner.models import SymbolScanResult
    from bist_signal_bot.scanner.models import ScanCandidateStatus

    res = SymbolScanResult(symbol="ASELS", status=ScanCandidateStatus.PASSED)

    with patch("bist_signal_bot.app.valuation_app.create_valuation_store") as mock_store:
        mock_risk = MagicMock()
        mock_risk.valuation_score = 45.0
        mock_risk.valuation_risk_level.value = "LOW"
        mock_instance = MagicMock()
        mock_instance.load_latest_risk.return_value = mock_risk
        mock_store.return_value = mock_instance

        engine.add_valuation_context(res)

        assert getattr(res, "valuation_score", None) == 45.0
        assert getattr(res, "valuation_risk_level", None) == "LOW"
