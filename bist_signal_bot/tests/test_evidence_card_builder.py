import pytest
from bist_signal_bot.explainability.evidence_card import EvidenceCardBuilder
from bist_signal_bot.explainability.models import SignalExplanation, ExplanationStatus
from datetime import datetime

def test_evidence_card_builder():
    builder = EvidenceCardBuilder()
    exp = SignalExplanation(
        explanation_id="1",
        symbol="ASELS",
        generated_at=datetime.utcnow(),
        summary="Test signal",
        final_status=ExplanationStatus.PASS
    )
    card = builder.build_card(exp)
    assert card.symbol == "ASELS"
    assert len(card.sections) == 1
    assert card.sections[0].title == "Summary"
    assert "ML model context" in card.missing_evidence

def test_evidence_card_builder_missing():
    builder = EvidenceCardBuilder()
    card = builder.build_from_signal({"symbol": "THYAO"})
    assert card.symbol == "THYAO"
