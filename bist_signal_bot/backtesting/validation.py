import pandas as pd
from bist_signal_bot.backtesting.models import BacktestConfig, ExecutionPriceMode
from bist_signal_bot.core.exceptions import BacktestValidationError, BacktestExecutionError

def validate_backtest_data(data: pd.DataFrame) -> None:
    if data is None or data.empty:
        raise BacktestValidationError("Data cannot be empty")
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing = [c for c in required_cols if c not in data.columns]
    if missing:
        raise BacktestValidationError(f"Missing required columns in data: {missing}")

def validate_no_lookahead_execution(signal_index: int, execution_index: int, mode: ExecutionPriceMode) -> None:
    if mode == ExecutionPriceMode.SAME_CLOSE_FOR_RESEARCH_ONLY:
        if execution_index < signal_index:
            raise BacktestExecutionError("Execution index cannot be before signal index")
    else:
        if execution_index <= signal_index:
            raise BacktestExecutionError("Execution index must be strictly greater than signal index for proper next-bar execution")

def validate_backtest_config(config: BacktestConfig) -> None:
    if config.initial_capital <= 0:
        raise BacktestValidationError("initial_capital must be > 0")
    if not (0.0 <= config.max_position_size_pct <= 1.0):
        raise BacktestValidationError("max_position_size_pct must be between 0.0 and 1.0")
    if config.min_trade_notional < 0:
        raise BacktestValidationError("min_trade_notional must be >= 0")

def validate_equity_curve(equity_curve: pd.DataFrame) -> None:
    if equity_curve is None or equity_curve.empty:
        raise BacktestValidationError("Equity curve is empty or None")
    if 'equity' not in equity_curve.columns:
        raise BacktestValidationError("Equity curve missing 'equity' column")
    if (equity_curve['equity'] < 0).any():
        raise BacktestValidationError("Equity curve contains negative equity values")
