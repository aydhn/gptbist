from unittest.mock import patch, MagicMock
from bist_signal_bot.portfolio_construction.engine import PortfolioConstructionEngine
from bist_signal_bot.portfolio_construction.models import PortfolioCandidate

def test_portfolio_valuation_filter():
    engine = PortfolioConstructionEngine()
    engine.settings = MagicMock()
    engine.settings.PORTFOLIO_USE_VALUATION_SCORE = True

    c = PortfolioCandidate(candidate_id="123", symbol="ASELS", final_candidate_score=100.0)

    with patch("bist_signal_bot.app.valuation_app.create_valuation_store") as mock_store:
        mock_risk = MagicMock()
        mock_risk.valuation_score = 90.0
        mock_risk.valuation_risk_level.value = "EXTREME"
        mock_instance = MagicMock()
        mock_instance.load_latest_risk.return_value = mock_risk
        mock_store.return_value = mock_instance

        engine.apply_valuation_filter([c])

        assert c.final_candidate_score == 50.0 # Penaltied by half
