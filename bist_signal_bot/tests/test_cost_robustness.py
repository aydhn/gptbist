import pytest
import pandas as pd
from bist_signal_bot.validation.cost_robustness import CostRobustnessAnalyzer
from bist_signal_bot.validation.models import StrategyValidationRequest

def test_cost_robustness_empty_data():
    analyzer = CostRobustnessAnalyzer()
    req = StrategyValidationRequest(strategy_name="MA")
    res = analyzer.analyze("MA", "ASELS", pd.DataFrame(), {}, req)
    assert res.status.value == "INSUFFICIENT_DATA"

def test_calculate_cost_sensitivity():
    analyzer = CostRobustnessAnalyzer()
    score = analyzer.calculate_cost_sensitivity({"BASE": {"net_return_pct": 10.0}, "STRESS": {"net_return_pct": 5.0}})
    assert score == 50.0
