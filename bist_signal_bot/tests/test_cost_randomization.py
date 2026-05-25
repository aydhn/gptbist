from bist_signal_bot.monte_carlo.cost_randomization import CostRandomizer
from bist_signal_bot.monte_carlo.models import CostRandomizationConfig

def test_randomize_trade_costs():
    randomizer = CostRandomizer()
    config = CostRandomizationConfig("c", 1.0, 1.0, 1.5, 2.0, 1.0, 1.0, 1.0, 1.0, 42)

    trades = [{"gross_return_pct": 5.0, "net_return_pct": 4.0}]
    res = randomizer.randomize_trade_costs(trades, config, seed=42)

    new_trade = res[0]
    drag = new_trade["gross_return_pct"] - new_trade["net_return_pct"]
    assert drag >= 1.5 and drag <= 2.0
    assert new_trade["metadata"]["cost_randomized"] is True

def test_randomize_returns_for_costs():
    randomizer = CostRandomizer()
    config = CostRandomizationConfig("c", 1.0, 1.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0, 42)

    returns = [5.0]
    res = randomizer.randomize_returns_for_costs(returns, config, seed=42)

    assert abs(res[0] - 4.9) < 1e-5
