from typing import Any
import pandas as pd
from bist_signal_bot.backtesting.models import BacktestTrade, PortfolioSnapshot, BacktestResult

def build_equity_curve_dataframe(snapshots: list[PortfolioSnapshot]) -> pd.DataFrame:
    if not snapshots: return pd.DataFrame()
    data = [{"timestamp": s.timestamp, "cash": s.cash, "position_value": s.position_value, "equity": s.equity, "gross_exposure": s.gross_exposure, "net_exposure": s.net_exposure, "open_positions": s.open_positions} for s in snapshots]
    df = pd.DataFrame(data)
    df.set_index("timestamp", inplace=True)
    return df

def build_trades_dataframe(trades: list[BacktestTrade]) -> pd.DataFrame:
    if not trades: return pd.DataFrame()
    data = [{"symbol": t.symbol, "entry_time": t.entry_time, "exit_time": t.exit_time, "side": t.side.value, "quantity": t.quantity, "entry_price": t.entry_price, "exit_price": t.exit_price, "entry_cost": t.entry_cost, "exit_cost": t.exit_cost, "gross_pnl": t.gross_pnl, "net_pnl": t.net_pnl, "return_pct": t.return_pct, "bars_held": t.bars_held, "entry_reason": t.entry_reason, "exit_reason": t.exit_reason} for t in trades]
    df = pd.DataFrame(data)
    return df

def basic_backtest_summary(result: BacktestResult) -> dict[str, Any]:
    return {
        "strategy_name": result.strategy_name,
        "symbol": result.symbol,
        "initial_capital": result.config.initial_capital,
        "final_equity": result.final_equity(),
        "total_return_pct": result.total_return_pct(),
        "trade_count": result.trade_count(),
        "closed_trade_count": result.closed_trade_count(),
        "total_cost": result.total_cost(),
        "execution_mode": result.config.execution_price_mode.value,
        "cost_scenario": result.config.scenario.value,
        "started_at": result.started_at.isoformat(),
        "finished_at": result.finished_at.isoformat(),
        "elapsed_seconds": result.elapsed_seconds,
        "disclaimer": result.disclaimer,
    }
