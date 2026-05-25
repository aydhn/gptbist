import pytest
from pathlib import Path
from bist_signal_bot.explainability.storage import ExplainabilityStore
from bist_signal_bot.explainability.models import SignalExplanation, ExplanationStatus, EvidenceCard, DecisionTrace
from datetime import datetime

def test_explainability_store_signal(tmp_path):
    store = ExplainabilityStore(base_dir=tmp_path)
    exp = SignalExplanation(
        explanation_id="exp1",
        symbol="ASELS",
        generated_at=datetime.utcnow(),
        summary="Test",
        final_status=ExplanationStatus.PASS
    )
    store.append_signal_explanation(exp)

    loaded = store.load_signal_explanations()
    assert len(loaded) == 1
    assert loaded[0].explanation_id == "exp1"

    assert store.get_signal_explanation("exp1").symbol == "ASELS"

def test_explainability_store_card(tmp_path):
    store = ExplainabilityStore(base_dir=tmp_path)
    card = EvidenceCard(
        card_id="c1",
        symbol="THYAO",
        created_at=datetime.utcnow(),
        title="T",
        summary="S",
        overall_status=ExplanationStatus.PASS
    )
    store.append_evidence_card(card)
    loaded = store.load_evidence_cards(symbol="THYAO")
    assert len(loaded) == 1
    assert loaded[0].card_id == "c1"

def test_explainability_store_trace(tmp_path):
    store = ExplainabilityStore(base_dir=tmp_path)
    trace = DecisionTrace(
        trace_id="t1",
        symbol="GARAN",
        created_at=datetime.utcnow(),
        final_decision="PROCEED",
        stages=[]
    )
    store.append_decision_trace(trace)
    loaded = store.load_decision_traces("GARAN")
    assert len(loaded) == 1
    assert loaded[0].trace_id == "t1"
