"""Point-in-time historical replay of the PAPER engine (research only).

For each trading day D in [start, end] the paper engine is run "as of D's close" on data truncated to
bars <= D (``PaperTradingEngine.as_of`` + ``data_override``), against ONE isolated fresh account whose
ledger lives in a temp directory. Exits (non-LONG signal on an open position) are executed through
``PaperTradingEngine.close_position`` (the engine's ``run_once`` itself only opens positions).

Paper/simulation only. No real order sent.
"""

from __future__ import annotations

import shutil
import tempfile
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Optional

import pandas as pd

NO_ORDER = "No real order sent."


@dataclass
class ReplayTrade:
    symbol: str
    entry_date: date
    entry_price: float          # raw fill price
    quantity: float
    entry_cost: float
    exit_date: Optional[date] = None
    exit_price: Optional[float] = None
    exit_cost: float = 0.0

    @property
    def closed(self) -> bool:
        return self.exit_date is not None

    @property
    def net_pnl(self) -> Optional[float]:
        if not self.closed:
            return None
        return (self.exit_price - self.entry_price) * self.quantity - self.entry_cost - self.exit_cost


@dataclass
class ReplayResult:
    strategy: str
    symbols: list[str]
    start: date
    end: date
    execution_mode: str
    use_decision_layer: bool
    initial_cash: float
    equity_curve: pd.DataFrame = field(default_factory=pd.DataFrame)  # index=date; equity, cash, open_positions
    trades: list[ReplayTrade] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)               # one dict per replayed day
    fills: list[dict] = field(default_factory=list)
    rejections: list[dict] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    days: int = 0
    disclaimer: str = NO_ORDER
    cash_interest_enabled: bool = False
    cash_interest_total: float = 0.0
    cash_benchmark: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))  # cash-only compounding of initial_cash

    @property
    def equity_ex_cash(self) -> pd.Series:
        """Equity with cumulative credited cash interest removed."""
        if self.equity_curve.empty:
            return pd.Series(dtype=float)
        if "interest_cum" not in self.equity_curve:
            return self.equity_curve["equity"].copy()
        return self.equity_curve["equity"] - self.equity_curve["interest_cum"]

    @property
    def cash_benchmark_return_pct(self) -> float:
        return (float(self.cash_benchmark.iloc[-1]) / self.initial_cash - 1) * 100 if len(self.cash_benchmark) and self.initial_cash else 0.0

    @property
    def excess_over_cash_pct(self) -> float:
        return (self.final_equity / self.initial_cash - 1) * 100 - self.cash_benchmark_return_pct if self.initial_cash else 0.0

    @property
    def final_equity(self) -> float:
        return float(self.equity_curve["equity"].iloc[-1]) if not self.equity_curve.empty else self.initial_cash

    @property
    def total_costs(self) -> float:
        return float(sum(f["total_cost"] for f in self.fills))

    def summary(self) -> dict:
        closed = [t for t in self.trades if t.closed]
        return {
            "strategy": self.strategy, "symbols": len(self.symbols), "days": self.days,
            "start": str(self.start), "end": str(self.end), "execution_mode": self.execution_mode,
            "decision_layer": self.use_decision_layer, "trades": len(self.trades), "closed_trades": len(closed),
            "orders": sum(d["orders"] for d in self.decisions), "fills": len(self.fills),
            "rejections": len(self.rejections), "initial_cash": self.initial_cash,
            "final_equity": round(self.final_equity, 2),
            "return_pct": round((self.final_equity / self.initial_cash - 1) * 100, 4),
            "total_costs": round(self.total_costs, 2),
            "cash_interest_enabled": self.cash_interest_enabled, "cash_interest_total": round(self.cash_interest_total, 2),
            "cash_benchmark_return_pct": round(self.cash_benchmark_return_pct, 4),
            "excess_over_cash_pct": round(self.excess_over_cash_pct, 4), "disclaimer": self.disclaimer,
        }


# ------------------------------------------------------------------ data helpers
def _as_date(d: Any) -> date:
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    return pd.Timestamp(d).date()


def load_local_frames(settings: Any, symbols: list[str], vendor: str = "yfinance", timeframe: str = "1d") -> dict[str, pd.DataFrame]:
    """Read daily OHLCV from the local store only (never the network)."""
    from bist_signal_bot.data.models import Timeframe
    from bist_signal_bot.storage.local_store import LocalMarketDataStore

    store = LocalMarketDataStore(settings=settings)
    tf = Timeframe(timeframe)
    out: dict[str, pd.DataFrame] = {}
    for s in symbols:
        s = s.upper()
        try:
            if store.exists(s, vendor, tf):
                df = store.read_ohlcv(s, vendor, tf).data.copy()
                df.sort_index(inplace=True)
                out[s] = df[~df.index.duplicated(keep="last")]
        except Exception:
            continue
    return out


def trading_dates(frames: dict[str, pd.DataFrame], start: date, end: date, use_calendar: bool = True) -> list[date]:
    """Trading days present in the data within [start, end] (also filtered by the BIST calendar)."""
    days: set[date] = set()
    for df in frames.values():
        days.update(pd.DatetimeIndex(df.index).date)
    out = sorted(d for d in days if start <= d <= end)
    if use_calendar:
        try:
            from bist_signal_bot.intraday.sessions import is_trading_day
            out = [d for d in out if is_trading_day(d)]
        except Exception:
            pass
    return out


def _decision_now(d: date) -> datetime:
    """A timestamp inside D's continuous session just before the close (decision-layer clock)."""
    from bist_signal_bot.intraday.sessions import IST, session_bounds
    try:
        b = session_bounds(d)
        if b:
            return b[1] - pd.Timedelta(minutes=5).to_pytimedelta()
    except Exception:
        pass
    return datetime.combine(d, time(17, 55), tzinfo=IST)


@contextmanager
def _setting(settings: Any, key: str, value: Any):
    try:
        old = getattr(settings, key)
    except Exception:
        old = None
    setattr(settings, key, value)
    try:
        yield
    finally:
        setattr(settings, key, old)


def _intent(sig: Any) -> str:
    from bist_signal_bot.paper.engine import PaperTradingEngine
    return PaperTradingEngine._intent(sig)


# ------------------------------------------------------------------ replay
def replay_paper(
    strategy: str,
    symbols: list[str],
    start: Any,
    end: Any,
    account_id: Optional[str] = None,
    settings: Any = None,
    use_decision_layer: bool = False,
    execution_mode: Any = None,
    frames: Optional[dict[str, pd.DataFrame]] = None,
    use_trade_risk: bool = True,
    use_portfolio_risk: bool = True,
    exit_on_non_long: bool = True,
    close_open_at_end: bool = False,
    initial_cash: Optional[float] = None,
    ledger_dir: Optional[Path] = None,
    cash_interest: Optional[bool] = None,
) -> ReplayResult:
    """Replay the paper engine day by day with point-in-time data. No real order sent.

    Idle-cash interest (``cash_interest``; default BACKTEST_CASH_INTEREST_ENABLED) is credited per replayed day with the
    paper ledger's own ``apply_cash_interest`` on the replay date (PAPER_CASH_INTEREST_ANNUAL/WITHHOLDING); the engine's
    wall-clock accrual is neutralised during the replay."""
    from bist_signal_bot.config.settings import Settings
    from bist_signal_bot.paper.engine import PaperTradingDependencies, PaperTradingEngine
    from bist_signal_bot.paper.ledger import PaperLedgerStore
    from bist_signal_bot.paper.models import PaperExecutionMode, PaperRunRequest
    from bist_signal_bot.strategies.engine import StrategyEngine

    settings = settings or Settings()
    execution_mode = execution_mode or PaperExecutionMode.LATEST_CLOSE_RESEARCH
    if isinstance(execution_mode, str):
        execution_mode = PaperExecutionMode(execution_mode)
    symbols = [s.upper() for s in symbols]
    start_d, end_d = _as_date(start), _as_date(end)
    frames = frames if frames is not None else load_local_frames(settings, symbols)
    frames = {s: frames[s] for s in symbols if s in frames}
    cash0 = float(initial_cash if initial_cash is not None else settings.PAPER_INITIAL_CASH)
    from bist_signal_bot.backtesting.cash import CashParams, cash_benchmark_curve
    from bist_signal_bot.paper.cash_interest import apply_cash_interest
    cparams = CashParams(enabled=bool(getattr(settings, "BACKTEST_CASH_INTEREST_ENABLED", True)) if cash_interest is None else bool(cash_interest),
                         annual=float(getattr(settings, "PAPER_CASH_INTEREST_ANNUAL", 0.0)),
                         withholding=float(getattr(settings, "PAPER_CASH_INTEREST_WITHHOLDING", 0.0)))
    interest_total, last_interest_day = 0.0, None

    own_dir = ledger_dir is None
    base = Path(ledger_dir) if ledger_dir else Path(tempfile.mkdtemp(prefix="replay_ledger_"))
    acc = account_id or f"replay_{uuid.uuid4().hex[:10]}"
    res = ReplayResult(strategy=strategy, symbols=symbols, start=start_d, end=end_d,
                       execution_mode=execution_mode.value, use_decision_layer=use_decision_layer, initial_cash=cash0)
    missing = [s for s in symbols if s not in frames]
    if missing:
        res.issues.append(f"No local data for: {', '.join(missing)}")

    try:
        with _setting(settings, "RUNTIME_USE_DECISION_LAYER", bool(use_decision_layer)), \
             _setting(settings, "PAPER_REJECT_IF_INSUFFICIENT_CASH", True),              _setting(settings, "PAPER_CASH_INTEREST_ANNUAL", 0.0):  # engine accrues on wall-clock today(); replay accrues on d
            engine = PaperTradingEngine(PaperTradingDependencies(
                ledger_store=PaperLedgerStore(settings, base_dir=base),
                strategy_engine=StrategyEngine(settings=settings),
                data_service=object(),   # unused: data_override supplies every frame
                settings=settings))
            engine.data_override = frames
            engine.initialize_account(acc, initial_cash=cash0, overwrite=False)
            days = trading_dates(frames, start_d, end_d)
            open_trades: dict[str, ReplayTrade] = {}
            rows = []
            for i, d in enumerate(days):
                engine.as_of = pd.Timestamp(datetime.combine(d, time(23, 59, 59)))
                now = _decision_now(d)
                engine.decision_clock = lambda now=now: now
                md = {"decision_now": now.isoformat()}
                req = PaperRunRequest(account_id=acc, symbols=symbols, strategy_name=strategy, source="local",
                                      timeframe="1d", execution_mode=execution_mode, use_trade_risk=use_trade_risk,
                                      use_portfolio_risk=use_portfolio_risk, metadata=md)
                day = {"date": str(d), "signals": 0, "orders": 0, "fills": 0, "exits": 0, "rejections": 0, "issues": []}
                try:
                    # 1) exits first (mirrors the backtest ordering: close on non-LONG signal)
                    if exit_on_non_long:
                        for sym in list(open_trades):
                            df = engine._load_frame(sym, req)
                            if df is None or df.empty:
                                continue
                            sigs = engine._run_strategy(sym, df, req)
                            if sigs and _intent(sigs[0]) != "LONG":
                                _close(engine, acc, sym, execution_mode, df, d, open_trades, res, day)
                    # 2) entries via the real engine path
                    r = engine.run_once(req)
                    day["signals"] = len(r.signals)
                    day["orders"] = len(r.orders)
                    day["status"] = str(getattr(r.status, "value", r.status))
                    if getattr(r, "error", None):
                        day["issues"].append(str(r.error))
                    day["issues"].extend(str(x) for x in r.issues)
                    for f in r.fills:
                        _record_fill(f, d, open_trades, res)
                        day["fills"] += 1
                    for rj in r.metadata.get("risk_rejections", []):
                        if rj.get("status") == "ERROR":
                            res.rejections.append({"date": str(d), "stage": "risk_engine_error", "symbol": rj.get("symbol"), "status": "ERROR",
                                                   "reasons": [str(x)[:200] for x in rj.get("reasons", [])][:3]})
                        elif str(rj.get("status", "")).startswith("PORTFOLIO_"):
                            res.rejections.append({"date": str(d), "stage": "portfolio_risk", "symbol": rj.get("symbol"), "status": rj["status"],
                                                   "reasons": [str(x) for x in rj.get("reasons", [])][:3]})
                        else:
                            res.rejections.append({"date": str(d), "stage": "trade_risk", "symbol": rj.get("symbol"), "status": rj.get("status"),
                                                   "reasons": [str(x) for x in rj.get("reasons", [])][:3]})
                    for x in r.issues:
                        sx = str(x)
                        if "Insufficient cash" in sx or "Execution error" in sx:
                            res.rejections.append({"date": str(d), "stage": "execution", "status": "REJECTED", "reasons": [sx[:200]]})
                    for ev in (r.metadata.get("decision_records") or []) if hasattr(r, "metadata") else []:
                        if isinstance(ev, dict) and not ev.get("approved", True):
                            res.rejections.append({"date": str(d), "stage": "decision_layer", **{k: ev.get(k) for k in ("symbol", "reason", "status")}})
                    day["rejections"] = sum(1 for x in res.rejections if x["date"] == str(d))
                except Exception as e:  # a bad day must not abort the replay
                    day["issues"].append(f"{type(e).__name__}: {e}")
                    r = None
                if close_open_at_end and i == len(days) - 1:
                    for sym in list(open_trades):
                        df = engine._load_frame(sym, req)
                        try:
                            _close(engine, acc, sym, execution_mode, df, d, open_trades, res, day)
                        except Exception as e:
                            day["issues"].append(f"final close {sym}: {e}")
                st = engine.load_state(acc)
                if cparams.enabled:
                    if last_interest_day is None:
                        st.account.metadata.pop("last_interest_date", None)
                    else:
                        st.account.metadata["last_interest_date"] = last_interest_day.isoformat()
                    amt = apply_cash_interest(st.account, d, cparams.annual, cparams.withholding)
                    last_interest_day = d
                    if amt > 0:
                        interest_total += amt
                        engine.ledger_store.save(st)
                rows.append({"date": d, "equity": float(st.account.equity), "cash": float(st.account.cash),
                             "open_positions": len(st.open_positions()), "interest_cum": interest_total})
                res.decisions.append(day)
            res.days = len(days)
            res.cash_interest_enabled, res.cash_interest_total = cparams.enabled, interest_total
            res.cash_benchmark = cash_benchmark_curve(days, cash0, cparams) if days else pd.Series(dtype=float)
            res.equity_curve = pd.DataFrame(rows).set_index("date") if rows else pd.DataFrame(columns=["equity", "cash", "open_positions", "interest_cum"])
            res.trades = [t for t in res.trades] + list(open_trades.values())
            res.trades.sort(key=lambda t: (t.entry_date, t.symbol))
    finally:
        if own_dir:
            shutil.rmtree(base, ignore_errors=True)
    for d_ in res.decisions:
        res.issues.extend(f"{d_['date']}: {m}" for m in d_["issues"][:2])
    res.issues = res.issues[:50]
    return res


def _record_fill(f: Any, d: date, open_trades: dict, res: ReplayResult) -> None:
    side = str(getattr(f.side, "value", f.side))
    rec = {"date": str(d), "symbol": f.symbol, "side": side, "quantity": float(f.quantity),
           "fill_price": float(f.fill_price), "effective_price": float(f.effective_price),
           "total_cost": float(f.total_cost), "mode": str(getattr(f.execution_mode, "value", f.execution_mode))}
    res.fills.append(rec)
    if side == "BUY":
        open_trades[f.symbol] = ReplayTrade(f.symbol, d, float(f.fill_price), float(f.quantity), float(f.total_cost))
    else:
        t = open_trades.pop(f.symbol, None)
        if t is not None:
            t.exit_date, t.exit_price, t.exit_cost = d, float(f.fill_price), float(f.total_cost)
            res.trades.append(t)


def _close(engine, acc, sym, mode, df, d, open_trades, res, day) -> None:
    r = engine.close_position(acc, sym, execution_mode=mode, data=df)
    for f in r.fills:
        _record_fill(f, d, open_trades, res)
        day["fills"] += 1
        day["exits"] += 1
