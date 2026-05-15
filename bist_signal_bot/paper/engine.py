import logging
import uuid
import pandas as pd
from datetime import datetime, UTC
from typing import Any, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import PaperTradingError, PaperAccountError
from bist_signal_bot.paper.models import (
    PaperAccountStatus,
    PaperExecutionMode,
    PaperLedgerEvent,
    PaperLedgerEventType,
    PaperLedgerState,
    PaperOrderSide,
    PaperOrderStatus,
    PaperRunRequest,
    PaperRunResult
)
from bist_signal_bot.paper.account import PaperAccountManager
from bist_signal_bot.paper.ledger import PaperLedgerStore
from bist_signal_bot.paper.orders import PaperOrderManager
from bist_signal_bot.paper.execution import PaperExecutionSimulator
from bist_signal_bot.strategies.engine import StrategyEngine
from bist_signal_bot.risk.engine import RiskEngine
from bist_signal_bot.portfolio.risk_engine import PortfolioRiskEngine
from bist_signal_bot.ml.inference.engine import MLInferenceEngine
from bist_signal_bot.ml.inference.models import MLInferenceConfig, MLFilterDecision
from bist_signal_bot.security.kill_switch import KillSwitchManager
from bist_signal_bot.security.models import KillSwitchScope
from bist_signal_bot.storage.paths import get_data_dir
from bist_signal_bot.core.exceptions import KillSwitchActiveError

from bist_signal_bot.data.data_service import MarketDataService

class PaperTradingEngine:
    def __init__(
        self,
        ledger_store: PaperLedgerStore,
        strategy_engine: StrategyEngine,
        risk_engine: Optional[RiskEngine] = None,
        portfolio_risk_engine: Optional[PortfolioRiskEngine] = None,
        execution_simulator: Optional[PaperExecutionSimulator] = None,
        data_service: Optional[MarketDataService] = None,
        settings: Optional[Settings] = None,
        notifier: Optional[Any] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.settings = settings or Settings()
        self.ledger_store = ledger_store
        self.strategy_engine = strategy_engine
        self.risk_engine = risk_engine or RiskEngine(self.settings)
        self.portfolio_risk_engine = portfolio_risk_engine or PortfolioRiskEngine(self.settings)
        self.execution_simulator = execution_simulator or PaperExecutionSimulator(settings=self.settings)
        self.data_service = data_service or MarketDataService(self.settings)
        self.notifier = notifier
        self.logger = logger or logging.getLogger("bist_signal_bot.paper.engine")
        self.account_manager = PaperAccountManager(self.settings)
        self.order_manager = PaperOrderManager()

    def initialize_account(self, account_id: Optional[str] = None, initial_cash: Optional[float] = None, overwrite: bool = False) -> PaperLedgerState:
        acc_id = account_id or self.settings.PAPER_DEFAULT_ACCOUNT_ID

        if self.ledger_store.exists(acc_id):
            if not overwrite:
                raise PaperAccountError(f"Account {acc_id} already exists. Use overwrite=True to reset.")
            # Reset existing
            state = self.ledger_store.load(acc_id)
            self.account_manager.reset_account(state.account, initial_cash)
            # Clear ledgers
            state.orders = []
            state.fills = []
            state.positions = []
            state.trades = []
            state.events = []
            state.events.append(PaperLedgerEvent(
                event_id=str(uuid.uuid4()),
                account_id=acc_id,
                event_type=PaperLedgerEventType.ACCOUNT_RESET,
                message=f"Account {acc_id} reset"
            ))
            self.ledger_store.save(state)
            return state
        else:
            # Create new
            account = self.account_manager.create_account(initial_cash=initial_cash, account_id=acc_id)
            state = self.ledger_store.initialize_ledger(account)
            state.events.append(PaperLedgerEvent(
                event_id=str(uuid.uuid4()),
                account_id=acc_id,
                event_type=PaperLedgerEventType.ACCOUNT_INITIALIZED,
                message=f"Account {acc_id} initialized"
            ))
            self.ledger_store.save(state)
            return state

    def load_state(self, account_id: str) -> PaperLedgerState:
        return self.ledger_store.load(account_id)

    def run_once(self, request: PaperRunRequest) -> PaperRunResult:
        if self.kill_switch.is_active(KillSwitchScope.PAPER):
            self.logger.warning("PAPER kill switch is active. Paper Engine run aborted.")
            return PaperRunResult(request=request, status=PaperAccountStatus.ERROR, error="Kill Switch Active")
        start_time = datetime.now()

        # 1. Load state
        state = self.load_state(request.account_id)
        if state.account.status != PaperAccountStatus.ACTIVE:
            raise PaperAccountError(f"Account {request.account_id} is not ACTIVE")

        result = PaperRunResult(
            account=state.account,
            status="SUCCESS"
        )

        # 2. Collect market data and generate signals
        symbols = [s.upper() for s in request.symbols]
        data_frames = {}
        all_signals = []

        for symbol in symbols:
            try:
                # Need sufficient rows for strategy, assuming 200 is safe
                df = self.data_service.get_data(symbol, request.source, request.timeframe, rows=200)
                if df.empty:
                    result.issues.append(f"No data for {symbol}")
                    continue
                data_frames[symbol] = df

                strat_res = self.strategy_engine.run(
                    symbol=symbol,
                    data=df,
                    strategy_name=request.strategy_name,
                    params=request.params
                )

                # Check for active signals (LONG/SHORT)
                for sig in strat_res.signals:
                    if sig.intent.value in ["LONG", "SHORT"]:
                        all_signals.append((symbol, sig, df))

            except Exception as e:
                 result.issues.append(f"Strategy error for {symbol}: {str(e)}")

        result.signals = [s[1] for s in all_signals]

        # 3. Risk Engine
        approved_candidates = []
        if request.use_trade_risk and all_signals:
            for symbol, sig, df in all_signals:
                 try:
                     risk_dec = self.risk_engine.evaluate(sig, df)
                     result.risk_decisions.append(risk_dec)
                     if risk_dec.status.value == "APPROVED":
                         approved_candidates.append((symbol, sig, risk_dec, df))
                 except Exception as e:
                     result.issues.append(f"Risk error for {symbol}: {str(e)}")
        else:
             # If risk engine is off, pass through but maybe with fallback sizing
             for symbol, sig, df in all_signals:
                 approved_candidates.append((symbol, sig, None, df))

        # 4. Portfolio Risk Engine
        portfolio_approved = []
        if request.use_portfolio_risk and approved_candidates:
             # Need current positions and equity
             open_positions = {p.symbol: {"quantity": p.quantity, "value": p.market_value, "side": p.side.value}
                               for p in state.positions if p.is_open}
             current_equity = state.account.equity

             signals_for_portfolio = [sig for _, sig, _, _ in approved_candidates]
             try:
                 port_dec = self.portfolio_risk_engine.evaluate_batch(
                     signals=signals_for_portfolio,
                     current_positions=open_positions,
                     total_equity=current_equity
                 )
                 result.portfolio_decision = port_dec

                 if port_dec.status.value == "APPROVED":
                     # Filter candidates based on portfolio approval
                     approved_symbols = [al.symbol for al in port_dec.allocations if al.approved and al.allocated_quantity > 0]
                     for symbol, sig, risk_dec, df in approved_candidates:
                          if symbol in approved_symbols:
                               # Override risk decision quantity with portfolio allocation if available
                               allocation = next(a for a in port_dec.allocations if a.symbol == symbol)
                               if risk_dec:
                                   risk_dec.recommended_size = float(allocation.allocated_quantity)
                               portfolio_approved.append((symbol, sig, risk_dec, port_dec, df))
             except Exception as e:
                 result.issues.append(f"Portfolio risk error: {str(e)}")
        else:
             for symbol, sig, risk_dec, df in approved_candidates:
                 portfolio_approved.append((symbol, sig, risk_dec, None, df))

        # 5. Order Creation & Execution
        open_pos_symbols = state.open_position_symbols()
        latest_prices = {}

        for symbol, df in data_frames.items():
            latest_prices[symbol] = float(df.iloc[-1]['close'])

        for symbol, sig, risk_dec, port_dec, df in portfolio_approved:
            # Simplification: Only process LONG signals for now
            if sig.intent.value == "LONG" and symbol not in open_pos_symbols:
                qty = risk_dec.recommended_size if risk_dec and risk_dec.recommended_size else (self.settings.PAPER_INITIAL_CASH * 0.1 / latest_prices.get(symbol, 1))

                try:
                    # Create Order
                    order = self.order_manager.create_market_order(
                        account_id=request.account_id,
                        symbol=symbol,
                        side=PaperOrderSide.BUY,
                        quantity=qty,
                        signal=sig,
                        risk_decision=risk_dec,
                        portfolio_decision=port_dec
                    )
                    state.orders.append(order)
                    result.orders.append(order)

                    if order.status == PaperOrderStatus.CREATED:
                        self.order_manager.accept_order(order)

                        # Simulate Fill
                        fill = self.execution_simulator.simulate_fill(
                            order=order,
                            data=df,
                            mode=request.execution_mode
                        )
                        result.fills.append(fill)

                        # Apply to Ledger
                        state = self.execution_simulator.apply_fill_to_ledger(state, fill)

                except Exception as e:
                     result.issues.append(f"Execution error for {symbol}: {str(e)}")

        # 6. Mark to market
        state = self.execution_simulator.mark_to_market(state, latest_prices)

        # 7. Save State
        self.ledger_store.save(state)

        result.positions = state.open_positions()
        result.account = state.account
        result.events = state.events

        end_time = datetime.now()
        result.elapsed_seconds = (end_time - start_time).total_seconds()

        if result.issues:
             result.status = "COMPLETED_WITH_ISSUES"

        # 8. Optional Notification
        if self.settings.PAPER_SEND_TELEGRAM_SUMMARY:
            self.send_paper_summary(result)

        return result

    def close_position(self, account_id: str, symbol: str, execution_mode: PaperExecutionMode = PaperExecutionMode.LATEST_CLOSE_RESEARCH, data: Optional[pd.DataFrame] = None, manual_price: Optional[float] = None) -> PaperRunResult:
        state = self.load_state(account_id)

        positions = [p for p in state.positions if p.is_open and p.symbol == symbol]
        if not positions:
            raise PaperTradingError(f"No open position found for {symbol}")

        pos = positions[0]

        order = self.order_manager.create_market_order(
            account_id=account_id,
            symbol=symbol,
            side=PaperOrderSide.SELL,
            quantity=pos.quantity
        )
        self.order_manager.accept_order(order)
        state.orders.append(order)

        fill = self.execution_simulator.simulate_fill(
            order=order,
            data=data,
            mode=execution_mode,
            manual_price=manual_price
        )

        state = self.execution_simulator.apply_fill_to_ledger(state, fill)
        self.ledger_store.save(state)

        result = PaperRunResult(
            account=state.account,
            status="SUCCESS",
            orders=[order],
            fills=[fill],
            positions=state.open_positions()
        )
        return result

    def cancel_order(self, account_id: str, order_id: str) -> PaperLedgerState:
        state = self.load_state(account_id)
        for order in state.orders:
             if order.order_id == order_id:
                  self.order_manager.cancel_order(order, reason="Manual cancellation")
                  self.ledger_store.save(state)
                  return state
        raise PaperTradingError(f"Order {order_id} not found")

    def status(self, account_id: str) -> dict[str, Any]:
        state = self.load_state(account_id)
        return state.summary()

    def send_paper_summary(self, result: PaperRunResult) -> None:
        if self.notifier:
            try:
                # We assume notifier has a format_paper_run_result method
                msg = self.notifier.formatter.format_paper_run_result(result) if hasattr(self.notifier, "formatter") and hasattr(self.notifier.formatter, "format_paper_run_result") else str(result.summary())
                self.notifier.send_message(msg)
            except Exception as e:
                self.logger.error(f"Failed to send paper summary: {e}")
