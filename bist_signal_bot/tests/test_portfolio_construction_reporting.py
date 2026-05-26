import pytest
from bist_signal_bot.portfolio_construction.reporting import format_rebalance_simulation_text
from bist_signal_bot.portfolio_construction.models import RebalanceSimulation

def test_reporting_disclaimers():
    sim = RebalanceSimulation(
        rebalance_id="reb1",
        current_weights={"A": 0.5},
        target_weights={"A": 0.6},
        actions=[],
        estimated_turnover_pct=10.0
    )

    text = format_rebalance_simulation_text(sim)
    assert "research-only" in text
    assert "Not an order list" in text or "not an order list" in text
