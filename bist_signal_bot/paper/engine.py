import logging
import uuid
from dataclasses import dataclass
import pandas as pd
from datetime import datetime, UTC
from typing import Any, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import PaperTradingError, PaperAccountError
from bist_signal_bot.paper.models import (
    CreateMarketOrderRequest,
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
from bist_signal_bot.paper.decision_hook import PaperDecisionHook, decision_layer_enabled

@dataclass
class PaperTradingDependencies:
    ledger_store: PaperLedgerStore
    strategy_engine: StrategyEngine
    risk_engine: Optional[RiskEngine] = None
    portfolio_risk_engine: Optional[PortfolioRiskEngine] = None
    execution_simulator: Optional[PaperExecutionSimulator] = None
    data_service: Optional[MarketDataService] = None
    settings: Optional[Settings] = None
    notifier: Optional[Any] = None
    logger: Optional[logging.Logger] = None

class PaperTradingEngine:
    def __init__(self, deps: PaperTradingDependencies):
        self.settings = deps.settings or Settings()
        self.ledger_store = deps.ledger_store
        self.strategy_engine = deps.strategy_engine
        self.risk_engine = deps.risk_engine or RiskEngine(settings=self.settings)
        self.portfolio_risk_engine = deps.portfolio_risk_engine or PortfolioRiskEngine(settings=self.settings)
        self.execution_simulator = deps.execution_simulator or PaperExecutionSimulator(settings=self.settings)
        self.data_service = deps.data_service or MarketDataService(self.settings)
        self.notifier = deps.notifier
        self.logger = deps.logger or logging.getLogger("bist_signal_bot.paper.engine")
        self.account_manager = PaperAccountManager(self.settings)
        self.order_manager = PaperOrderManager()
        self.kill_switch = KillSwitchManager(self.settings, get_data_dir(self.settings))
        # Per-order DecisionLayer hook (only used when RUNTIME_USE_DECISION_LAYER is True).
        self.decision_guard = None  # optional shared DailyLossGuard (set by the orchestrator)
        self.decision_clock = None  # optional injectable clock for replays/tests
        self._decision_hook: Optional[PaperDecisionHook] = None
        # Point-in-time replay support (default off => behavior unchanged).
        self.as_of = None  # optional pandas Timestamp/date: frames are truncated to index <= as_of
        self.data_override: Optional[dict] = None  # optional {SYMBOL: DataFrame} used instead of the data service

    def _hook(self) -> Optional[PaperDecisionHook]:
        if not decision_layer_enabled(self.settings):
            return None
        if self._decision_hook is None:
            self._decision_hook = PaperDecisionHook(self.settings, guard=self.decision_guard, clock=self.decision_clock)
        if self.decision_guard is not None and self._decision_hook.guard is not self.decision_guard:
            self._decision_hook.guard = self.decision_guard
        self._decision_hook.clock = self.decision_clock
        return self._decision_hook

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

        state, result = self._initialize_run(request.account_id)
        hook = self._hook()
        if hook is not None:
            hook.sync_guard(state, hook.now(None, request.metadata))

        data_frames, all_signals = self._collect_data_and_signals(request, result)
        approved_candidates = self._evaluate_trade_risk(request, all_signals, result, state)
        portfolio_approved = self._evaluate_portfolio_risk(request, state, approved_candidates, result)

        state = self._execute_orders(request, state, portfolio_approved, data_frames, result)
        state = self._finalize_run(start_time, state, data_frames, result)
        if hook is not None:
            hook.sync_guard(state, hook.now(None, request.metadata))
            result.metadata["realized_pnl_today"] = hook.realized_today(state, hook.now(None, request.metadata))
        self._notify_and_log(result)

        return result

    def run(self, strategy_name: str, **kw) -> dict:
        """Orchestrator adapter: ensure the account, run one paper iteration, return a summary dict. No real order sent."""
        from bist_signal_bot.data.symbol_universe import DEFAULT_SEED_SYMBOLS
        acc_id = kw.get("account_id") or self.settings.PAPER_DEFAULT_ACCOUNT_ID
        extra = {"no_real_order_sent": True, "message": "No real order sent."}
        try:
            if not self.ledger_store.exists(acc_id):
                self.initialize_account(acc_id)
            raw = kw.get("symbols") or list(DEFAULT_SEED_SYMBOLS)
            symbols = [str(getattr(s, "symbol", s)).upper() for s in raw]
            source = kw.get("source") or "local"
            timeframe = kw.get("timeframe") or "1d"
            req = PaperRunRequest(
                account_id=acc_id, symbols=symbols, strategy_name=strategy_name or self.settings.RUNTIME_DEFAULT_STRATEGY,
                source=source, timeframe=timeframe, execution_mode=PaperExecutionMode.LATEST_CLOSE_RESEARCH,
                use_trade_risk=kw.get("use_trade_risk", True), use_portfolio_risk=kw.get("use_portfolio_risk", True),
                params=kw.get("params") or {}, metadata=kw.get("metadata") or {})
            result = self.run_once(req)
            out = result.summary()
            out["status"] = str(getattr(result.status, "value", result.status))
            out["error"] = getattr(result, "error", None)
            acc = result.account
            out.update(
                equity=acc.equity, cash=acc.cash, realized_pnl=acc.realized_pnl,
                open_positions=len(result.positions), symbols_requested=len(symbols),
                issues=list(result.issues)[:20], disclaimer=result.disclaimer)
            out.update(extra)
            return out
        except Exception as e:  # never raise into the orchestrator
            self.logger.warning("Paper run failed: %s", e)
            return {"account_id": acc_id, "status": "ERROR", "error": str(e), "signals_count": 0,
                    "orders_count": 0, "fills_count": 0, **extra}

    def _initialize_run(self, account_id: str) -> tuple[PaperLedgerState, PaperRunResult]:
        state = self.load_state(account_id)
        if state.account.status != PaperAccountStatus.ACTIVE:
            raise PaperAccountError(f"Account {account_id} is not ACTIVE")
        result = PaperRunResult(account=state.account, status="SUCCESS")
        return state, result

    @staticmethod
    def _intent(sig: Any) -> str:
        intent = getattr(sig, "intent", None)
        val = getattr(intent, "value", intent)
        if val is None:
            direction = getattr(sig, "direction", None)
            val = getattr(direction, "value", direction)
        return str(val or "").upper()

    def _load_frame(self, symbol: str, request: PaperRunRequest, rows: int = 200) -> Optional[pd.DataFrame]:
        """Point-in-time wrapper: optional data_override and as_of truncation (both default off)."""
        if self.data_override is None and self.as_of is None:
            return self._load_frame_raw(symbol, request, rows)
        if self.data_override is not None:
            df = self.data_override.get(symbol.upper())
            if df is None:
                return None
        else:
            df = self._load_frame_raw(symbol, request, 10**9)
        if df is not None and self.as_of is not None:
            cut = pd.Timestamp(self.as_of)
            idx = df.index
            if getattr(idx, "tz", None) is not None and cut.tzinfo is None:
                cut = cut.tz_localize(idx.tz)
            elif getattr(idx, "tz", None) is None and cut.tzinfo is not None:
                cut = cut.tz_localize(None)
            df = df[idx <= cut]
        return df.tail(rows) if df is not None else None

    def _load_frame_raw(self, symbol: str, request: PaperRunRequest, rows: int = 200) -> Optional[pd.DataFrame]:
        """Load OHLCV for a symbol (legacy get_data or MarketDataService.get_ohlcv; local source never hits the network)."""
        svc = self.data_service
        if hasattr(svc, "get_data"):
            return svc.get_data(symbol, request.source, request.timeframe, rows=rows)
        from bist_signal_bot.data.models import Timeframe
        tf = Timeframe(request.timeframe)
        local = request.source in {"local", "local_file"}
        if local:
            store = getattr(svc, "store", None)
            vendor = getattr(getattr(svc, "provider", None), "vendor", None)
            if store is None or vendor is None or not store.exists(symbol, vendor, tf):
                return None
        md = svc.get_ohlcv(symbol, timeframe=tf, refresh=False, save=False, allow_provider_fallback=not local)
        data = getattr(md, "data", md)
        return data.tail(rows) if data is not None else None

    def _run_strategy(self, symbol: str, df: pd.DataFrame, request: PaperRunRequest) -> list:
        eng = self.strategy_engine
        if hasattr(eng, "run"):
            res = eng.run(symbol=symbol, data=df, strategy_name=request.strategy_name, params=request.params)
            return list(getattr(res, "signals", []) or [])
        res = eng.run_strategy_on_data(
            strategy_name=request.strategy_name, symbol=symbol, data=df,
            params=request.params, timeframe=request.timeframe)
        if getattr(res, "status", "success") == "error":
            msgs = "; ".join(getattr(i, "message", str(i)) for i in getattr(res, "issues", []))
            raise PaperTradingError(msgs or "strategy error")
        cand = getattr(res, "candidate", None)
        return [cand] if cand is not None else []

    def _collect_data_and_signals(self, request: PaperRunRequest, result: PaperRunResult) -> tuple[dict, list]:
        symbols = [s.upper() for s in request.symbols]
        data_frames = {}
        all_signals = []

        for symbol in symbols:
            try:
                df = self._load_frame(symbol, request)
                if df is None or df.empty:
                    result.issues.append(f"No data for {symbol}")
                    continue
                data_frames[symbol] = df

                for sig in self._run_strategy(symbol, df, request):
                    if self._intent(sig) in ("LONG", "SHORT"):
                        all_signals.append((symbol, sig, df))

            except Exception as e:
                 result.issues.append(f"Strategy error for {symbol}: {str(e)}")

        result.signals = [s[1] for s in all_signals]
        return data_frames, all_signals

    @staticmethod
    def _open_positions(state: Optional[PaperLedgerState]) -> list:
        return [p for p in (state.positions if state else []) if p.is_open]

    def build_risk_context(self, state: PaperLedgerState, n_signals: int = 0):
        """RiskContext from the paper ledger: equity, free cash, open positions (symbol -> qty/value/side)."""
        from bist_signal_bot.risk.models import RiskContext
        open_pos = self._open_positions(state)
        equity = float(state.account.equity)
        invested = sum(float(p.market_value) for p in open_pos)
        return RiskContext(
            equity=equity if equity > 0 else float(state.account.initial_cash),
            available_cash=max(0.0, float(state.account.cash)),
            current_positions={p.symbol: {"quantity": p.quantity, "value": p.market_value, "side": p.side.value} for p in open_pos},
            open_position_count=len(open_pos),
            daily_signal_count=n_signals,
            portfolio_risk_pct=(invested / equity * 100.0) if equity > 0 else 0.0,
            metadata={"account_id": state.account.account_id},
        )

    @staticmethod
    def _risk_reasons(dec: Any) -> list:
        fr = getattr(dec, "filter_result", None)
        reasons = [str(getattr(r, "value", r)) for r in (getattr(fr, "reject_reasons", None) or [])]
        reasons += [str(w) for w in (getattr(fr, "warnings", None) or [])]
        return reasons

    def _evaluate_trade_risk(self, request: PaperRunRequest, all_signals: list, result: PaperRunResult,
                             state: Optional[PaperLedgerState] = None) -> list:
        """RiskEngine.evaluate_signal(signal, RiskContext, data). Fail-closed: an engine error or a non-approved
        decision rejects the entry and is recorded in result.issues + result.metadata['risk_rejections']."""
        approved_candidates = []
        if request.use_trade_risk and all_signals:
            rejections = result.metadata.setdefault("risk_rejections", [])
            for symbol, sig, df in all_signals:
                 try:
                     if state is None:
                         raise PaperTradingError("ledger state unavailable for risk context")
                     ctx = self.build_risk_context(state, len(all_signals))
                     risk_dec = self.risk_engine.evaluate_signal(sig, ctx, df)
                     result.risk_decisions.append(risk_dec)
                     if risk_dec.approved and risk_dec.status.value in ("APPROVED", "REDUCED"):
                         approved_candidates.append((symbol, sig, risk_dec, df))
                     else:
                         reasons = self._risk_reasons(risk_dec)
                         rejections.append({"symbol": symbol, "status": risk_dec.status.value, "reasons": reasons})
                         result.issues.append(f"Risk rejected {symbol}: {risk_dec.status.value} {reasons}")
                 except Exception as e:
                     rejections.append({"symbol": symbol, "status": "ERROR", "reasons": [str(e)]})
                     result.issues.append(f"Risk error for {symbol}: {str(e)}")
        else:
             for symbol, sig, df in all_signals:
                 approved_candidates.append((symbol, sig, None, df))
        return approved_candidates

    def _evaluate_portfolio_risk(self, request: PaperRunRequest, state: PaperLedgerState, approved_candidates: list, result: PaperRunResult) -> list:
        portfolio_approved = []
        if request.use_portfolio_risk and approved_candidates:
             from bist_signal_bot.portfolio.holdings import build_portfolio_state
             from bist_signal_bot.portfolio.models import PortfolioHolding, PortfolioPositionSide
             rejections = result.metadata.setdefault("risk_rejections", [])
             try:
                 equity = float(state.account.equity)
                 equity = equity if equity > 0 else float(state.account.initial_cash)
                 holdings = [PortfolioHolding(
                     symbol=p.symbol, side=PortfolioPositionSide(p.side.value), quantity=p.quantity,
                     avg_price=p.avg_entry_price, last_price=p.last_price, market_value=p.market_value,
                     weight_pct=p.market_value / equity, unrealized_pnl=p.unrealized_pnl, opened_at=p.opened_at)
                     for p in self._open_positions(state)]
                 pstate = build_portfolio_state(equity=equity, cash=max(0.0, float(state.account.cash)),
                                                holdings=holdings, daily_signal_count=len(approved_candidates))
                 port_dec = self.portfolio_risk_engine.evaluate_portfolio_signals(
                     [sig for _, sig, _, _ in approved_candidates], pstate,
                     {symbol: df for symbol, _, _, df in approved_candidates})
                 result.portfolio_decision = port_dec

                 alloc = {i.symbol: i for i in port_dec.allocation_result.items}
                 for symbol, sig, risk_dec, df in approved_candidates:
                     item = alloc.get(symbol)
                     if item is not None and item.approved and item.quantity > 0:
                         if risk_dec is not None:
                             risk_dec.metadata["recommended_size"] = float(item.quantity)
                         portfolio_approved.append((symbol, sig, risk_dec, port_dec, df))
                     else:
                         reasons = list(getattr(item, "reasons", []) or []) + [str(getattr(r, "value", r)) for r in port_dec.reject_reasons]
                         rejections.append({"symbol": symbol, "status": "PORTFOLIO_" + port_dec.status.value, "reasons": reasons})
                         result.issues.append(f"Portfolio risk rejected {symbol}: {port_dec.status.value} {reasons}")
             except Exception as e:  # fail closed: nothing is entered when the portfolio check cannot run
                 rejections.append({"symbol": "*", "status": "ERROR", "reasons": [str(e)]})
                 result.issues.append(f"Portfolio risk error: {str(e)}")
        else:
             for symbol, sig, risk_dec, df in approved_candidates:
                 portfolio_approved.append((symbol, sig, risk_dec, None, df))
        return portfolio_approved

    def _execute_orders(self, request: PaperRunRequest, state: PaperLedgerState, portfolio_approved: list, data_frames: dict, result: PaperRunResult) -> PaperLedgerState:
        open_pos_symbols = state.open_position_symbols()
        latest_prices = {symbol: float(df.iloc[-1]['close']) for symbol, df in data_frames.items()}
        hook = self._hook()

        for symbol, sig, risk_dec, port_dec, df in portfolio_approved:
            if self._intent(sig) == "LONG" and symbol not in open_pos_symbols:
                sized = None
                if risk_dec is not None:
                    sized = risk_dec.metadata.get("recommended_size") or getattr(getattr(risk_dec, "position_size", None), "quantity", None)
                qty = float(sized) if sized else (self.settings.PAPER_INITIAL_CASH * 0.1 / latest_prices.get(symbol, 1))
                if hook is not None:
                    qty, rec = hook.gate_entry(symbol, sig, df, state, qty, request.timeframe, request.metadata)
                    hook.record_into(result, rec)
                    if qty <= 0:
                        continue
                try:
                    order = self.order_manager.create_market_order(
                        request=CreateMarketOrderRequest(
                            account_id=request.account_id,
                            symbol=symbol,
                            side=PaperOrderSide.BUY,
                            quantity=qty,
                            signal=sig,
                            risk_decision=risk_dec,
                            portfolio_decision=port_dec
                        )
                    )
                    state.orders.append(order)
                    result.orders.append(order)

                    if order.status == PaperOrderStatus.CREATED:
                        self.order_manager.accept_order(order)
                        fill = self.execution_simulator.simulate_fill(
                            order=order,
                            data=df,
                            mode=request.execution_mode
                        )
                        result.fills.append(fill)
                        state = self.execution_simulator.apply_fill_to_ledger(state, fill)
                except Exception as e:
                     result.issues.append(f"Execution error for {symbol}: {str(e)}")
        return state

    def _finalize_run(self, start_time: datetime, state: PaperLedgerState, data_frames: dict, result: PaperRunResult) -> PaperLedgerState:
        latest_prices = {symbol: float(df.iloc[-1]['close']) for symbol, df in data_frames.items()}
        state = self.execution_simulator.mark_to_market(state, latest_prices)
        self.ledger_store.save(state)

        result.positions = state.open_positions()
        result.account = state.account
        result.events = state.events
        result.elapsed_seconds = (datetime.now() - start_time).total_seconds()

        if result.issues:
             result.status = "COMPLETED_WITH_ISSUES"
        return state

    def _notify_and_log(self, result: PaperRunResult):
        if self.settings.PAPER_SEND_TELEGRAM_SUMMARY:
            self.send_paper_summary(result)

        if self.settings.ENABLE_RESEARCH_LEDGER and self.settings.RESEARCH_AUTO_LOG_PAPER:
            try:
                from ..app.research_app import create_research_event_builder, create_research_ledger
                ledger = create_research_ledger(self.settings)
                builder = create_research_event_builder(self.settings)
                run_obj = builder.from_paper_run_result(result)
                ledger.append_run(run_obj)
            except Exception as e:
                self.logger.warning(f"Failed to log paper run to research ledger: {e}")

    def close_position(self, account_id: str, symbol: str, execution_mode: PaperExecutionMode = PaperExecutionMode.LATEST_CLOSE_RESEARCH, data: Optional[pd.DataFrame] = None, manual_price: Optional[float] = None) -> PaperRunResult:
        state = self.load_state(account_id)

        positions = [p for p in state.positions if p.is_open and p.symbol == symbol]
        if not positions:
            raise PaperTradingError(f"No open position found for {symbol}")

        pos = positions[0]
        hook = self._hook()  # exits are reduce-only: never gated, only fed to the guard
        if hook is not None:
            hook.sync_guard(state)

        order = self.order_manager.create_market_order(
            request=CreateMarketOrderRequest(
                account_id=account_id,
                symbol=symbol,
                side=PaperOrderSide.SELL,
                quantity=pos.quantity
            )
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
        if hook is not None:
            hook.sync_guard(state)

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
