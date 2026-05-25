import pytest
from bist_signal_bot.explainability.ensemble_explain import EnsembleExplainer
from bist_signal_bot.explainability.models import ExplanationStatus, ContributionDirection

def test_ensemble_explainer():
    explainer = EnsembleExplainer()
    payload = {
        "symbol": "ASELS",
        "score": 0.8,
        "agreement_count": 4,
        "disagreement_count": 1,
        "conflict_score": 0.2
    }
    res = explainer.explain_consensus(payload)
    assert res.agreement_count == 4
    assert res.disagreement_count == 1
    assert res.conflict_score == 0.2
    assert res.status == ExplanationStatus.PASS
    assert res.final_direction == ContributionDirection.SUPPORTS

def test_ensemble_explainer_conflict():
    explainer = EnsembleExplainer()
    payload = {
        "symbol": "ASELS",
        "score": 0.1,
        "agreement_count": 2,
        "disagreement_count": 3,
        "conflict_score": 0.8
    }
    res = explainer.explain_consensus(payload)
    assert res.status == ExplanationStatus.WARN
    assert len(res.warnings) == 1
    assert res.final_direction == ContributionDirection.OPPOSES
