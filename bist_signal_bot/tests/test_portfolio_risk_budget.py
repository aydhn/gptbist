import pytest
import pandas as pd
from bist_signal_bot.portfolio_construction.risk_budget import RiskBudgetCalculator

def test_risk_budget_volatility_and_contribution():
    calc = RiskBudgetCalculator()

    # Create deterministic df
    df = pd.DataFrame({
        "A": [0.01, -0.01, 0.01, -0.01],
        "B": [0.02, 0.02, 0.02, 0.02]
    })

    vols = calc.volatility_by_symbol(df)
    assert "A" in vols
    assert "B" in vols
    assert vols["B"] < vols["A"] # B is constant 0.02, so its std is 0.

    contrib = calc.contribution_to_risk({"A": 0.5, "B": 0.5}, df)
    assert contrib["A"] is not None
    assert contrib["B"] is not None
