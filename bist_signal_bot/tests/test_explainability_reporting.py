import pytest
from bist_signal_bot.explainability.reporting import (
    format_signal_explanation_text,
    format_evidence_card_text,
    format_evidence_card_markdown,
    format_decision_trace_text,
    format_explainability_report_markdown
)
from bist_signal_bot.explainability.models import (
    SignalExplanation, ExplanationStatus, EvidenceCard, EvidenceCardSection,
    EvidenceCardSectionType, DecisionTrace
)
from datetime import datetime

def test_format_signal_text():
    exp = SignalExplanation(
        explanation_id="1", symbol="ASELS", strategy_name="t",
        generated_at=datetime.utcnow(), summary="sum", final_status=ExplanationStatus.PASS
    )
    text = format_signal_explanation_text(exp)
    assert "ASELS" in text
    assert "sum" in text
    assert "research-only" in text

def test_format_card_markdown():
    card = EvidenceCard(
        card_id="1", symbol="THYAO", created_at=datetime.utcnow(),
        title="T", summary="S", overall_status=ExplanationStatus.PASS,
        sections=[EvidenceCardSection(section_id="s1", section_type=EvidenceCardSectionType.SUMMARY, title="Sum", body="B", status=ExplanationStatus.PASS)]
    )
    md = format_evidence_card_markdown(card)
    assert "# Evidence Card: THYAO" in md
    assert "## Sum" in md
    assert "research-only" in md

def test_format_trace_text():
    trace = DecisionTrace(
        trace_id="1", symbol="GARAN", created_at=datetime.utcnow(),
        final_decision="PROCEED", stages=[{"name": "S1", "status": "PASS"}]
    )
    text = format_decision_trace_text(trace)
    assert "GARAN" in text
    assert "S1: PASS" in text

def test_format_report():
    card = EvidenceCard(card_id="1", symbol="THYAO", created_at=datetime.utcnow(), title="T", summary="S", overall_status=ExplanationStatus.PASS)
    trace = DecisionTrace(trace_id="1", symbol="GARAN", created_at=datetime.utcnow(), final_decision="PROCEED", stages=[])
    md = format_explainability_report_markdown([card], [trace])
    assert "Explainability Report" in md
    assert "Evidence Card: THYAO" in md
    assert "Decision Trace: GARAN" in md
