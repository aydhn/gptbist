from unittest.mock import patch, MagicMock
from bist_signal_bot.explainability.evidence_card import EvidenceCardBuilder
from bist_signal_bot.explainability.models import EvidenceCardSectionType

def test_evidence_card_valuation_section():
    builder = EvidenceCardBuilder()
    builder.settings = MagicMock()

    with patch("bist_signal_bot.app.valuation_app.create_valuation_store") as mock_store:
        mock_risk = MagicMock()
        mock_risk.valuation_score = 50.0
        mock_risk.valuation_risk_level.value = "FAIR"
        mock_risk.recommended_decision = "HOLD"
        mock_instance = MagicMock()
        mock_instance.load_latest_risk.return_value = mock_risk
        mock_store.return_value = mock_instance

        section = builder.section_valuation("ASELS")
        assert section is not None
        assert section.title == "Valuation Context"
        assert "50.0" in section.body
