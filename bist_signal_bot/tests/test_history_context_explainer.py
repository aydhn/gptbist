import pytest
from bist_signal_bot.explainability.history_context import HistoryContextExplainer

def test_history_explainer():
    explainer = HistoryContextExplainer()
    res = explainer.explain_history("ASELS")
    assert len(res.warnings) == 1
    assert res.similar_cases_count == 0
