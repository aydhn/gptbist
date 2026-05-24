from typing import Any
import logging
from datetime import datetime, timezone
import pandas as pd
from typing import Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.backtesting.models import (
    BacktestResult,
    BacktestTrade,
    BacktestFill,
    PortfolioSnapshot,
    BacktestPerformanceReport,
    ReturnMetrics,
    RiskMetrics,
    RiskAdjustedMetrics,
    TradeMetrics,
    CostMetrics,
    ExposureMetrics
)
from bist_signal_bot.backtesting.drawdown import calculate_drawdown_curve, max_drawdown, max_drawdown_duration
from bist_signal_bot.backtesting.metrics import (
    calculate_returns,
    calculate_total_return,
    calculate_annualized_return,
    calculate_annualized_volatility,
    calculate_downside_volatility,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_calmar_ratio,
    calculate_var_cvar,
    safe_divide
)

class BacktestPerformanceAnalyzer:
    def __init__(self, settings: Optional[Settings] = None, logger: Optional[logging.Logger] = None):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)

    def analyze(self, result: BacktestResult) -> BacktestPerformanceReport:
        warnings = []
        if result.config.execution_price_mode.value == "SAME_CLOSE_FOR_RESEARCH_ONLY":
            warnings.append("Look-ahead bias alert: SAME_CLOSE_FOR_RESEARCH_ONLY execution mode used.")

        trade_metrics = self.calculate_trade_metrics(result.trades)
        if trade_metrics.trade_count < getattr(self.settings, "BACKTEST_MIN_TRADES_WARNING", 5):
             warnings.append(f"Low trade count: {trade_metrics.trade_count} trades. Results may not be statistically significant.")

        if not result.equity_curve.empty:
            drawdown_curve = calculate_drawdown_curve(result.equity_curve)
        else:
            drawdown_curve = pd.DataFrame()
            warnings.append("Equity curve is empty.")

        risk_metrics = self.calculate_risk_metrics(result.equity_curve, drawdown_curve)
        if risk_metrics.max_drawdown_pct is not None and abs(risk_metrics.max_drawdown_pct) > getattr(self.settings, "BACKTEST_HIGH_DRAWDOWN_WARNING_PCT", 30.0):
             warnings.append(f"High max drawdown: {risk_metrics.max_drawdown_pct:.2f}%")

        if any(not t.is_closed() for t in result.trades):
            warnings.append("There are open trades at the end of the backtest.")

        return_metrics = self.calculate_return_metrics(
             result.equity_curve,
             result.config.initial_capital,
             result.final_equity()
        )

        cost_metrics = self.calculate_cost_metrics(result.fills, result.config.initial_capital)
        exposure_metrics = self.calculate_exposure_metrics(result.portfolio_snapshots, result.config.initial_capital)
        risk_adjusted_metrics = self.calculate_risk_adjusted_metrics(result.equity_curve, return_metrics, risk_metrics)

        return BacktestPerformanceReport(
            strategy_name=result.strategy_name,
            symbol=result.symbol,
            timeframe=self.settings.STRATEGY_DEFAULT_TIMEFRAME,
            initial_capital=result.config.initial_capital,
            final_equity=result.final_equity(),
            return_metrics=return_metrics,
            risk_metrics=risk_metrics,
            risk_adjusted_metrics=risk_adjusted_metrics,
            trade_metrics=trade_metrics,
            cost_metrics=cost_metrics,
            exposure_metrics=exposure_metrics,
            started_at=result.started_at,
            finished_at=result.finished_at,
            generated_at=datetime.now(timezone.utc),
            warnings=warnings,
            disclaimer=result.disclaimer,
            metadata=result.metadata
        )

    def calculate_trade_metrics(self, trades: list[BacktestTrade]) -> TradeMetrics:
        closed_trades = [t for t in trades if t.is_closed()]
        trade_count = len(trades)
        closed_count = len(closed_trades)
        winning = [t for t in closed_trades if (t.net_pnl or 0) > 0]
        losing = [t for t in closed_trades if (t.net_pnl or 0) < 0]
        breakeven = [t for t in closed_trades if (t.net_pnl or 0) == 0]

        win_rate = safe_divide(len(winning), closed_count) * 100 if closed_count > 0 else None
        loss_rate = safe_divide(len(losing), closed_count) * 100 if closed_count > 0 else None

        avg_trade_return = safe_divide(sum(t.return_pct or 0 for t in closed_trades), closed_count) if closed_count > 0 else None
        avg_winner = safe_divide(sum(t.return_pct or 0 for t in winning), len(winning)) if winning else None
        avg_loser = safe_divide(sum(t.return_pct or 0 for t in losing), len(losing)) if losing else None

        best_trade = max((t.return_pct for t in closed_trades if t.return_pct is not None), default=None)
        worst_trade = min((t.return_pct for t in closed_trades if t.return_pct is not None), default=None)

        gross_profit = sum(t.net_pnl or 0 for t in winning)
        gross_loss = sum(abs(t.net_pnl or 0) for t in losing)
        net_profit = gross_profit - gross_loss

        profit_factor = safe_divide(gross_profit, gross_loss) if gross_loss > 0 else (float('inf') if gross_profit > 0 else None)

        expectancy = None
        if win_rate is not None and loss_rate is not None and avg_winner is not None and avg_loser is not None:
             expectancy = (win_rate/100 * avg_winner) - (loss_rate/100 * abs(avg_loser))

        avg_bars_held = safe_divide(sum(t.bars_held or 0 for t in closed_trades), closed_count) if closed_count > 0 else None

        return TradeMetrics(
            trade_count=trade_count,
            closed_trade_count=closed_count,
            winning_trades=len(winning),
            losing_trades=len(losing),
            breakeven_trades=len(breakeven),
            win_rate_pct=win_rate,
            loss_rate_pct=loss_rate,
            average_trade_return_pct=avg_trade_return,
            average_winner_pct=avg_winner,
            average_loser_pct=avg_loser,
            best_trade_pct=best_trade,
            worst_trade_pct=worst_trade,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            net_profit=net_profit,
            profit_factor=profit_factor,
            expectancy=expectancy,
            average_bars_held=avg_bars_held
        )

    def calculate_cost_metrics(self, fills: list[BacktestFill], initial_capital: float) -> CostMetrics:
        total_cost = sum(f.total_cost for f in fills)
        total_notional = sum(f.gross_notional for f in fills)
        return CostMetrics(
            total_commission=total_cost * 0.5,
            total_slippage=total_cost * 0.3,
            total_spread=total_cost * 0.2,
            total_tax=0.0,
            total_other_fees=0.0,
            total_cost=total_cost,
            total_cost_bps=safe_divide(total_cost * 10000, total_notional) if total_notional > 0 else None,
            cost_as_pct_of_initial_capital=safe_divide(total_cost, initial_capital) * 100 if initial_capital > 0 else None,
            cost_as_pct_of_gross_profit=None
        )

    def calculate_exposure_metrics(self, snapshots: list[PortfolioSnapshot], initial_capital: float) -> ExposureMetrics:
        if not snapshots:
            return ExposureMetrics(None, None, None, None, None)

        exposures = [safe_divide(s.gross_exposure, s.equity) * 100 if s.equity > 0 else 0 for s in snapshots]
        avg_exp = sum(exposures) / len(exposures) if exposures else None
        max_exp = max(exposures) if exposures else None

        in_market = sum(1 for e in exposures if e and e > 0)
        time_in_market = (in_market / len(exposures)) * 100 if exposures else None

        open_pos = [s.open_positions for s in snapshots]
        avg_open = sum(open_pos) / len(open_pos) if open_pos else None
        max_open = max(open_pos) if open_pos else None

        return ExposureMetrics(
            average_exposure_pct=avg_exp,
            max_exposure_pct=max_exp,
            time_in_market_pct=time_in_market,
            average_open_positions=avg_open,
            max_open_positions=max_open
        )

    def calculate_return_metrics(self, equity_curve: pd.DataFrame, initial_capital: float, final_equity: float) -> ReturnMetrics:
        returns = calculate_returns(equity_curve)
        total_return_decimal = calculate_total_return(initial_capital, final_equity)
        total_return_pct = total_return_decimal * 100.0

        periods = len(returns)
        ann_return = calculate_annualized_return(total_return_decimal, periods, getattr(self.settings, "BACKTEST_PERIODS_PER_YEAR", 252))
        ann_return_pct = ann_return * 100 if ann_return is not None else None

        avg_daily = returns.mean() * 100 if not returns.empty else None
        best_day = returns.max() * 100 if not returns.empty else None
        worst_day = returns.min() * 100 if not returns.empty else None

        return ReturnMetrics(
            total_return_pct=total_return_pct,
            annualized_return_pct=ann_return_pct,
            cumulative_return_pct=total_return_pct,
            average_daily_return_pct=avg_daily,
            best_day_return_pct=best_day,
            worst_day_return_pct=worst_day
        )

    def calculate_risk_metrics(self, equity_curve: pd.DataFrame, drawdown_curve: pd.DataFrame) -> RiskMetrics:
        returns = calculate_returns(equity_curve)
        ann_vol = calculate_annualized_volatility(returns, getattr(self.settings, "BACKTEST_PERIODS_PER_YEAR", 252))
        downside_vol = calculate_downside_volatility(returns, getattr(self.settings, "BACKTEST_PERIODS_PER_YEAR", 252))
        max_dd = max_drawdown(drawdown_curve)
        max_dd_dur = max_drawdown_duration(drawdown_curve)
        var, cvar = calculate_var_cvar(returns)

        return RiskMetrics(
            volatility_annualized_pct=ann_vol * 100 if ann_vol is not None else None,
            downside_volatility_pct=downside_vol * 100 if downside_vol is not None else None,
            max_drawdown_pct=max_dd,
            max_drawdown_duration_bars=max_dd_dur,
            value_at_risk_95_pct=var * 100 if var is not None else None,
            conditional_value_at_risk_95_pct=cvar * 100 if cvar is not None else None
        )

    def calculate_risk_adjusted_metrics(self, equity_curve: pd.DataFrame, return_metrics: ReturnMetrics, risk_metrics: RiskMetrics) -> RiskAdjustedMetrics:
        returns = calculate_returns(equity_curve)
        rf_rate = getattr(self.settings, "BACKTEST_RISK_FREE_RATE", 0.0)
        ppy = getattr(self.settings, "BACKTEST_PERIODS_PER_YEAR", 252)
        sharpe = calculate_sharpe_ratio(returns, rf_rate, ppy)
        sortino = calculate_sortino_ratio(returns, rf_rate, ppy)

        ann_ret = return_metrics.annualized_return_pct / 100 if return_metrics.annualized_return_pct else None
        calmar = calculate_calmar_ratio(ann_ret, risk_metrics.max_drawdown_pct)

        romad = None
        if return_metrics.total_return_pct is not None and risk_metrics.max_drawdown_pct and risk_metrics.max_drawdown_pct != 0:
            romad = return_metrics.total_return_pct / abs(risk_metrics.max_drawdown_pct)

        return RiskAdjustedMetrics(
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            return_over_max_drawdown=romad
        )

def performance_by_regime(result: "Any") -> dict[str, Any]:
    if not hasattr(result, 'trades') or not result.trades:
        return {}
    by_regime = {}
    for trade in result.trades:
        metadata = trade.entry_order.metadata if trade.entry_order else {}
        regime = metadata.get("market_regime", "UNKNOWN")
        if regime not in by_regime:
            by_regime[regime] = {"trades": 0, "winning_trades": 0, "losing_trades": 0, "total_profit": 0.0, "total_loss": 0.0, "net_profit": 0.0}
        stats = by_regime[regime]
        stats["trades"] += 1
        pnl = getattr(trade, 'net_pnl', 0.0)
        stats["net_profit"] += pnl
        if pnl > 0:
            stats["winning_trades"] += 1
            stats["total_profit"] += pnl
        else:
            stats["losing_trades"] += 1
            stats["total_loss"] += abs(pnl)
    for regime, stats in by_regime.items():
        stats["win_rate"] = (stats["winning_trades"] / stats["trades"] * 100.0) if stats["trades"] > 0 else 0.0
        stats["profit_factor"] = (stats["total_profit"] / stats["total_loss"]) if stats["total_loss"] > 0 else (float('inf') if stats["total_profit"] > 0 else 0.0)
    return by_regime
