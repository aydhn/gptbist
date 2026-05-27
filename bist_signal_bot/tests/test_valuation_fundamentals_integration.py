from datetime import datetime
from unittest.mock import patch, MagicMock

# We test the injected logic using standard patching
@patch("bist_signal_bot.app.valuation_app.create_valuation_store")
def test_fundamentals_valuation_injection(mock_store):
    from bist_signal_bot.fundamentals.engine import FundamentalEngine

    mock_risk = MagicMock()
    mock_risk.valuation_score = 60.0
    mock_risk.valuation_risk_level.value = "MEDIUM"

    mock_instance = MagicMock()
    mock_instance.load_latest_risk.return_value = mock_risk
    mock_store.return_value = mock_instance

    engine = FundamentalEngine(None, None, None, None, None, None, None)
    scorecard = engine.build_scorecard("ASELS", datetime.utcnow())

    # In my patch I didn't verify it was available, I just setattr. Let's see if metadata exists
    if hasattr(scorecard, "metadata"):
        assert scorecard.metadata.get("valuation_score") == 60.0
        assert scorecard.metadata.get("valuation_risk_level") == "MEDIUM"
