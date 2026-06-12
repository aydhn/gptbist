import logging
from datetime import datetime, UTC
from typing import Any
import pandas as pd

from bist_signal_bot.ml.inference.engine import MLInferenceEngine
from bist_signal_bot.ml.inference.models import MLInferenceConfig, MLFilterDecision
from bist_signal_bot.backtesting.models import (
    BacktestMode, ExecutionPriceMode, BacktestOrder, BacktestOrderType, BacktestConfig, BacktestResult,
)
from bist_signal_bot.backtesting.portfolio import BacktestPortfolio
from bist_signal_bot.backtesting.models import ReturnMetrics, RiskMetrics, RiskAdjustedMetrics, TradeMetrics, CostMetrics, ExposureMetrics, BacktestPerformanceReport, BenchmarkComparisonReport, BacktestReportBundle
from bist_signal_bot.backtesting.execution import BacktestExecutionModel
from bist_signal_bot.costs.engine import TransactionCostEngine
from bist_signal_bot.costs.models import CostScenario, OrderSide
from bist_signal_bot.strategies.engine import StrategyEngine
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.data.models import MarketDataFrame

class BacktestEngine:
    def __init__(self, strategy_engine: StrategyEngine, cost_engine: TransactionCostEngine, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.strategy_engine = strategy_engine
        self.cost_engine = cost_engine
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger("bist_signal_bot.backtest")

    def build_default_config(self) -> BacktestConfig:
        return BacktestConfig(
            initial_capital=self.settings.BACKTEST_INITIAL_CAPITAL,
            execution_price_mode=ExecutionPriceMode(self.settings.BACKTEST_EXECUTION_PRICE_MODE),
            commission_enabled=self.settings.BACKTEST_COMMISSION_ENABLED,
            slippage_enabled=self.settings.BACKTEST_SLIPPAGE_ENABLED,
            allow_short=self.settings.BACKTEST_ALLOW_SHORT,
            max_position_size_pct=self.settings.BACKTEST_MAX_POSITION_SIZE_PCT,
            min_trade_notional=self.settings.BACKTEST_MIN_TRADE_NOTIONAL,
            trade_on_candidate_statuses=["ACTIVE"],
            close_on_opposite_signal=self.settings.BACKTEST_CLOSE_ON_OPPOSITE_SIGNAL,
            close_on_flat_signal=self.settings.BACKTEST_CLOSE_ON_FLAT_SIGNAL,
            one_position_per_symbol=self.settings.BACKTEST_ONE_POSITION_PER_SYMBOL,
            use_fractional_shares=self.settings.BACKTEST_USE_FRACTIONAL_SHARES,
            close_open_positions_at_end=self.settings.BACKTEST_CLOSE_OPEN_POSITIONS_AT_END,
            scenario=CostScenario(self.settings.BACKTEST_COST_SCENARIO)
        )

    def should_close_position(self, candidate: SignalCandidate, current_position, config: BacktestConfig) -> bool:
        if not current_position: return False
        if current_position.side == SignalDirection.LONG:
            if config.close_on_opposite_signal and candidate.direction == SignalDirection.SHORT: return True
            if config.close_on_flat_signal and candidate.direction == SignalDirection.FLAT: return True
        return False

    def generate_order_from_candidate(self, candidate: SignalCandidate, timestamp: datetime, price: float, equity: float, config: BacktestConfig) -> BacktestOrder | None:
        if candidate.direction == SignalDirection.LONG: side = OrderSide.BUY
        elif candidate.direction == SignalDirection.SHORT: side = OrderSide.SELL
        else: return None
        if side == OrderSide.SELL and not config.allow_short: return None
        notional = equity * config.max_position_size_pct
        if notional < config.min_trade_notional: return None

        return BacktestOrder(
            symbol=candidate.symbol, side=side, order_type=BacktestOrderType.MARKET, quantity=0.0, requested_price=price,
            requested_at=timestamp, reason=f"Signal: {candidate.reasons[0]}" if candidate.reasons else "Signal candidate", metadata={"notional": notional}
        )


    def _process_pending_orders(self, pending_orders: list[BacktestOrder], current_row: pd.Series, current_time: datetime, portfolio: BacktestPortfolio, exec_model: BacktestExecutionModel, config: BacktestConfig):
        for order in pending_orders[:]:
            try:
                if config.execution_price_mode == ExecutionPriceMode.NEXT_OPEN: exec_price = float(current_row['open'])
                else: exec_price = float(current_row['close'])

                if order.order_type == BacktestOrderType.CLOSE_POSITION:
                    fill = exec_model.create_fill(order, exec_price, current_time)
                    portfolio.close_position(order.symbol, fill, order.reason)
                else:
                    if config.one_position_per_symbol and portfolio.has_position(order.symbol): pass
                    else:
                        notional = order.metadata.get("notional", 0.0)
                        qty = exec_model.quantity_from_notional(notional, exec_price, config.use_fractional_shares)
                        if qty > 0:
                            order.quantity = qty
                            fill = exec_model.create_fill(order, exec_price, current_time)
                            if portfolio.can_open_position(order.symbol, fill.total_cost + fill.gross_notional):
                                if fill.side == OrderSide.BUY: portfolio.open_long(order.symbol, qty, fill, order.reason)
            except Exception as e:
                self.logger.warning(f"Error executing order: {e}")
            pending_orders.remove(order)

    def _process_signals(self, symbol: str, current_price: float, current_time: datetime, historical_slice: pd.DataFrame, strategy_instance, portfolio: BacktestPortfolio, exec_model: BacktestExecutionModel, orders: list[BacktestOrder], pending_orders: list[BacktestOrder], config: BacktestConfig):
        if len(historical_slice) < 5:
            return

        try:
            candidate = strategy_instance.generate_candidate(symbol, historical_slice)
            if candidate and candidate.status.value in config.trade_on_candidate_statuses:
                pos = portfolio.get_position(symbol)
                if self.should_close_position(candidate, pos, config):
                    close_order = BacktestOrder(symbol=symbol, side=OrderSide.SELL if pos.side == SignalDirection.LONG else OrderSide.BUY, order_type=BacktestOrderType.CLOSE_POSITION, quantity=pos.quantity, requested_price=current_price, requested_at=current_time, reason=f"Opposite/Flat Signal: {candidate.reasons[0] if candidate.reasons else ''}")
                    orders.append(close_order)
                    if config.execution_price_mode == ExecutionPriceMode.SAME_CLOSE_FOR_RESEARCH_ONLY:
                         fill = exec_model.create_fill(close_order, current_price, current_time)
                         portfolio.close_position(symbol, fill, close_order.reason)
                    else: pending_orders.append(close_order)
                elif candidate.direction in [SignalDirection.LONG, SignalDirection.SHORT]:
                     if config.one_position_per_symbol and pos: pass
                     else:
                         equity = portfolio.current_equity({symbol: current_price})
                         entry_order = self.generate_order_from_candidate(candidate, current_time, current_price, equity, config)
                         if entry_order:
                             orders.append(entry_order)
                             if config.execution_price_mode == ExecutionPriceMode.SAME_CLOSE_FOR_RESEARCH_ONLY:
                                 qty = exec_model.quantity_from_notional(entry_order.metadata["notional"], current_price, config.use_fractional_shares)
                                 if qty > 0:
                                     entry_order.quantity = qty
                                     fill = exec_model.create_fill(entry_order, current_price, current_time)
                                     if fill.side == OrderSide.BUY: portfolio.open_long(symbol, qty, fill, entry_order.reason)
                             else: pending_orders.append(entry_order)
        except Exception as e:
            pass

    def _close_open_positions_at_end(self, symbol: str, df: pd.DataFrame, portfolio: BacktestPortfolio, exec_model: BacktestExecutionModel, orders: list[BacktestOrder], config: BacktestConfig):
        if config.close_open_positions_at_end and portfolio.has_position(symbol):
            last_time = df.index[-1]
            last_price = float(df.iloc[-1]['close'])
            pos = portfolio.get_position(symbol)
            close_order = BacktestOrder(symbol=symbol, side=OrderSide.SELL if pos.side == SignalDirection.LONG else OrderSide.BUY, order_type=BacktestOrderType.CLOSE_POSITION, quantity=pos.quantity, requested_price=last_price, requested_at=last_time, reason="End of backtest")
            orders.append(close_order)
            fill = exec_model.create_fill(close_order, last_price, last_time)
            portfolio.close_position(symbol, fill, close_order.reason)
            portfolio.mark_to_market(last_time, {symbol: last_price})

    def run_single_symbol(self, strategy_name: str, symbol: str, data: MarketDataFrame | pd.DataFrame, params: dict[str, Any] | None = None, config: BacktestConfig | None = None) -> BacktestResult:
        import time
        start_time = time.time()
        profiler = None
        timer_span = None
        if getattr(self.settings, 'ENABLE_PERFORMANCE_PROFILING', False):
            from bist_signal_bot.app.performance_app import create_local_profiler
            profiler = create_local_profiler(self.settings)
            timer_span = profiler.timer.start_span(f"backtest_single_{symbol}")

        started_at = datetime.now(UTC)
        df = data.data.copy() if isinstance(data, MarketDataFrame) else data.copy()
        df.sort_index(inplace=True)
        config = config or self.build_default_config()

        portfolio = BacktestPortfolio(initial_capital=config.initial_capital, allow_short=config.allow_short, use_fractional_shares=config.use_fractional_shares)
        exec_model = BacktestExecutionModel(self.cost_engine, config)
        orders, issues = [], []

        strategy_instance = self.strategy_engine.registry.get(strategy_name)
        if not strategy_instance: raise ValueError(f"Strategy {strategy_name} not found")

        pending_orders = []

        for i in range(len(df)):
            current_time = df.index[i]
            current_row = df.iloc[i]
            current_price = float(current_row['close'])

            self._process_pending_orders(pending_orders, current_row, current_time, portfolio, exec_model, config)

            historical_slice = df.iloc[:i+1]
            if len(historical_slice) < 5:
                 portfolio.mark_to_market(current_time, {symbol: current_price})
                 continue

            self._process_signals(symbol, current_price, current_time, historical_slice, strategy_instance, portfolio, exec_model, orders, pending_orders, config)

            portfolio.mark_to_market(current_time, {symbol: current_price})

        self._close_open_positions_at_end(symbol, df, portfolio, exec_model, orders, config)

        finished_at = datetime.now(UTC)
        elapsed = (finished_at - started_at).total_seconds()

        eq_df = pd.DataFrame([{"timestamp": s.timestamp, "cash": s.cash, "position_value": s.position_value, "equity": s.equity, "gross_exposure": s.gross_exposure, "net_exposure": s.net_exposure, "open_positions": s.open_positions} for s in portfolio.snapshots])
        if not eq_df.empty: eq_df.set_index("timestamp", inplace=True)

        res = BacktestResult(strategy_name=strategy_name, symbol=symbol, mode=BacktestMode.SINGLE_SYMBOL, config=config, trades=portfolio.trades, fills=portfolio.fills, portfolio_snapshots=portfolio.snapshots, orders=orders, equity_curve=eq_df, started_at=started_at, finished_at=finished_at, elapsed_seconds=elapsed,
            data_source=data.source.value if hasattr(data, "source") else "UNKNOWN",
            data_row_count=len(df), issues=issues)


        # Phase 47: Research Logging
        if self.settings.ENABLE_RESEARCH_LEDGER and self.settings.RESEARCH_AUTO_LOG_BACKTEST:
            try:
                from ..app.research_app import create_research_ledger, create_research_event_builder
                ledger = create_research_ledger(self.settings)
                builder = create_research_event_builder(self.settings)
                run_obj = builder.from_backtest_result(res)
                ledger.append_run(run_obj)
            except Exception as e:
                self.logger.warning(f"Failed to log backtest to research ledger: {e}")

        return res

    def run_batch_symbols(self, strategy_name: str, symbols_data: dict[str, MarketDataFrame | pd.DataFrame], params: dict[str, Any] | None = None, config: BacktestConfig | None = None) -> dict[str, BacktestResult]:
        results = {}
        for symbol, data in symbols_data.items():
            try:
                res = self.run_single_symbol(strategy_name, symbol, data, params, config)
                results[symbol] = res
            except Exception as e:
                self.logger.error(f"Batch backtest failed for {symbol}: {e}")
        return results
