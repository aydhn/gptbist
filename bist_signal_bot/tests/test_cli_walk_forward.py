from unittest.mock import MagicMock, patch


@patch("bist_signal_bot.validation.walk_forward.WalkForwardAnalyzer")
def test_cli_train_test(mock_analyzer_cls):
    from bist_signal_bot.cli.commands import handle_validate_backtest

    mock_analyzer = MagicMock()
    mock_analyzer_cls.return_value = mock_analyzer

    mock_result = MagicMock()
    mock_result.summary.return_value = {"test": "result"}
    mock_result.split_results = [MagicMock()]
    mock_result.split_results[0].test_report.return_metrics.total_return_pct = 5.0
    mock_result.overfit_risk_level.value = "LOW"

    mock_analyzer.run_train_test.return_value = mock_result

    class Args:
        pass

    args = Args()
    args.validate_command = "train-test"
    args.source = "mock"
    args.symbol = "ASELS"
    args.strategy = "moving_average_trend"
    args.timeframe = "1d"
    args.period = "1y"
    args.rows = 500
    args.train_ratio = 0.7
    args.compare_benchmark = None
    args.param = None
    args.json = True

    with patch("bist_signal_bot.cli.commands.BacktestEngine", create=True):
        handle_validate_backtest(args)

    mock_analyzer.run_train_test.assert_called_once()


@patch("bist_signal_bot.validation.robustness.RobustnessAnalyzer")
def test_cli_robustness(mock_analyzer_cls):
    from bist_signal_bot.cli.commands import handle_validate_backtest

    mock_analyzer = MagicMock()
    mock_analyzer_cls.return_value = mock_analyzer

    mock_result = MagicMock()
    mock_result.summary.return_value = {"test": "result"}
    mock_result.run_results = [MagicMock()]
    mock_result.stability_score = 90.0
    mock_result.overfit_risk_level.value = "LOW"

    mock_analyzer.run_parameter_robustness.return_value = mock_result

    class Args:
        pass

    args = Args()
    args.validate_command = "robustness"
    args.source = "mock"
    args.symbol = "ASELS"
    args.strategy = "moving_average_trend"
    args.param_range = ["fast=10,20"]
    args.max_runs = 20
    args.timeframe = "1d"
    args.period = "1y"
    args.rows = 500
    args.param = None
    args.json = True

    with patch("bist_signal_bot.cli.commands.BacktestEngine", create=True):
        handle_validate_backtest(args)

    mock_analyzer.run_parameter_robustness.assert_called_once()
