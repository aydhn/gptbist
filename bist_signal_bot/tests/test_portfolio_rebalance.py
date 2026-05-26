import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.portfolio_construction.rebalance import RebalanceSimulator
from bist_signal_bot.portfolio_construction.models import RebalanceActionType

def test_rebalance_simulator():
    settings = Settings()
    sim = RebalanceSimulator(settings)

    cw = {"A": 0.5, "B": 0.5}
    tw = {"A": 0.6, "C": 0.4} # B goes to 0, A increases, C is added

    turnover = sim.estimate_turnover(cw, tw)
    # A: +0.1, B: -0.5, C: +0.4 -> total absolute change = 1.0 -> one sided turnover = 50.0%
    assert turnover == 50.0

    actions = sim.build_actions(cw, tw)
    action_map = {a["symbol"]: a["action"] for a in actions}

    assert action_map["A"] == RebalanceActionType.INCREASE.value
    assert action_map["B"] == RebalanceActionType.REMOVE.value
    assert action_map["C"] == RebalanceActionType.ADD.value
