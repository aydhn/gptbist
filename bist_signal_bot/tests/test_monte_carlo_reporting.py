from bist_signal_bot.monte_carlo.models import MonteCarloResult, MonteCarloRequest, MonteCarloTarget, ResamplingMethod, MonteCarloStatus
from bist_signal_bot.monte_carlo.reporting import format_monte_carlo_result_text

def test_format_monte_carlo_result_text():
    req = MonteCarloRequest("req", MonteCarloTarget.TRADES, ResamplingMethod.TRADE_SHUFFLE, 10, 42, 1000.0, 30.0, strategy_name="S1", symbol="A")
    res = MonteCarloResult("mc1", req, MonteCarloStatus.PASS, 0.1, [], [], [], robustness_score=85.0)

    txt = format_monte_carlo_result_text(res)
    assert "Monte Carlo Result (ID: mc1)" in txt
    assert "Status: PASS" in txt
    assert "Robustness Score: 85.0" in txt
