import pytest
import pandas as pd
from bist_signal_bot.validation.regime_robustness import RegimeRobustnessAnalyzer

def test_regime_robustness_empty_labels():
    analyzer = RegimeRobustnessAnalyzer()
    res = analyzer.analyze("MA", "ASELS", [], None)
    assert res.status.value == "INSUFFICIENT_DATA"
    assert "No regime labels" in res.warnings[0]

def test_regime_robustness_metrics():
    analyzer = RegimeRobustnessAnalyzer()
    res = analyzer.analyze("MA", "ASELS", [], pd.Series([1,2,3]))
    assert res.regime_metrics is not None
    assert res.weakest_regime is not None
    assert res.strongest_regime is not None
