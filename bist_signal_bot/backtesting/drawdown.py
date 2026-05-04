import pandas as pd
from bist_signal_bot.core.exceptions import BacktestMetricsError

def calculate_drawdown_curve(equity_curve: pd.DataFrame, equity_col: str = "equity") -> pd.DataFrame:
    if equity_curve.empty:
        raise BacktestMetricsError("Cannot calculate drawdown on empty equity curve")

    if equity_col not in equity_curve.columns:
        raise BacktestMetricsError(f"Column '{equity_col}' not found in equity curve")

    df = pd.DataFrame()

    if 'timestamp' in equity_curve.columns:
         df['timestamp'] = equity_curve['timestamp']
    else:
         df['timestamp'] = equity_curve.index

    if 'timestamp' in df.columns and not isinstance(df.index, pd.DatetimeIndex):
         if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
             df['timestamp'] = pd.to_datetime(df['timestamp'])
         df = df.set_index('timestamp')

    df['equity'] = list(equity_curve[equity_col])
    df['running_peak'] = df['equity'].cummax()
    df['drawdown'] = df['equity'] - df['running_peak']

    df['drawdown_pct'] = 0.0
    valid_mask = df['running_peak'] > 0
    df.loc[valid_mask, 'drawdown_pct'] = (df.loc[valid_mask, 'drawdown'] / df.loc[valid_mask, 'running_peak']) * 100.0

    return df

def max_drawdown(drawdown_curve: pd.DataFrame) -> float | None:
    if drawdown_curve.empty or 'drawdown_pct' not in drawdown_curve.columns:
        return None
    return float(drawdown_curve['drawdown_pct'].min())

def max_drawdown_duration(drawdown_curve: pd.DataFrame) -> int | None:
    if drawdown_curve.empty or 'drawdown_pct' not in drawdown_curve.columns:
        return None

    underwater = drawdown_curve['drawdown_pct'] < 0
    if not underwater.any():
        return 0

    duration = underwater.groupby((~underwater).cumsum()).sum()
    return int(duration.max())

def current_drawdown(drawdown_curve: pd.DataFrame) -> float | None:
    if drawdown_curve.empty or 'drawdown_pct' not in drawdown_curve.columns:
        return None
    return float(drawdown_curve['drawdown_pct'].iloc[-1])
