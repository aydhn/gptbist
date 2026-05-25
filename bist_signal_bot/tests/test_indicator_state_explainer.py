import pytest
from bist_signal_bot.explainability.indicator_state import IndicatorStateExplainer
from bist_signal_bot.explainability.models import ContributionDirection

def test_explain_moving_average_state():
    explainer = IndicatorStateExplainer()
    row = {"close": 110, "sma_50": 100}
    exps = explainer.explain_moving_average_state(row)
    assert len(exps) == 1
    assert exps[0].contribution_direction == ContributionDirection.SUPPORTS
    assert "upward trend" in exps[0].message

    row2 = {"close": 90, "sma_50": 100}
    exps2 = explainer.explain_moving_average_state(row2)
    assert len(exps2) == 1
    assert exps2[0].contribution_direction == ContributionDirection.OPPOSES
    assert "downward trend" in exps2[0].message

def test_explain_rsi_state():
    explainer = IndicatorStateExplainer()
    exps = explainer.explain_rsi_state({"rsi_14": 25})
    assert len(exps) == 1
    assert exps[0].contribution_direction == ContributionDirection.SUPPORTS
    assert "Oversold" in exps[0].state

    exps2 = explainer.explain_rsi_state({"rsi_14": 80})
    assert len(exps2) == 1
    assert exps2[0].contribution_direction == ContributionDirection.OPPOSES
    assert "Overbought" in exps2[0].state

    exps3 = explainer.explain_rsi_state({"rsi_14": 50})
    assert len(exps3) == 1
    assert exps3[0].contribution_direction == ContributionDirection.NEUTRAL
    assert "Neutral" in exps3[0].state
