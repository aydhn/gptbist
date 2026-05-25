import pytest
from unittest.mock import patch, MagicMock

@patch("bist_signal_bot.cli.commands.create_monte_carlo_engine")
def test_cli_monte_carlo_run(mock_create):
    from bist_signal_bot.cli.commands import handle_monte_carlo
    from bist_signal_bot.monte_carlo.models import MonteCarloResult, MonteCarloRequest, MonteCarloTarget, ResamplingMethod, MonteCarloStatus

    mock_engine = MagicMock()
    req = MonteCarloRequest("req", MonteCarloTarget.TRADES, ResamplingMethod.TRADE_SHUFFLE, 10, 42, 1000.0, 30.0)
    mock_res = MonteCarloResult("mc1", req, MonteCarloStatus.PASS, 0.1, [], [], [], robustness_score=90.0)
    mock_engine.run_from_trades.return_value = mock_res
    mock_create.return_value = mock_engine

    class Args:
        monte_carlo_command = "run"
        strategy = "S1"
        symbol = "A"
        method = "TRADE_SHUFFLE"
        simulations = 10
        include_cost_randomization = False
        json = False

    handle_monte_carlo(Args())
    mock_engine.run_from_trades.assert_called_once()
