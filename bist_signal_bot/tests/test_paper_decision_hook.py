"""DecisionLayer hooked into PaperTradingEngine per entry order (offline, tmp dirs). No real order sent."""
import json
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.intraday.sessions import IST
from bist_signal_bot.paper.engine import PaperTradingDependencies, PaperTradingEngine
from bist_signal_bot.paper.ledger import PaperLedgerStore
from bist_signal_bot.paper.models import (
    CreateMarketOrderRequest,
    PaperExecutionMode, PaperPosition, PaperPositionSide, PaperRunRequest, PaperRunResult,
)
from bist_signal_bot.risk.daily_loss import DailyLossGuard
from bist_signal_bot.security.kill_switch import KillSwitchManager
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection
from bist_signal_bot.strategies.engine import StrategyEngine
from bist_signal_bot.data.data_service import MarketDataService

NOW = datetime(2026, 3, 9, 11, 0, tzinfo=IST)  # Monday, continuous session


class Sig(SignalCandidate):
    intent: Any = None


class NoAudit:
    def log_event(self, e):
        pass


def make_sig(edge=300.0):
    class _I:
        value = "LONG"
    return Sig(symbol="ASELS", strategy_name="t", direction=SignalDirection.LONG, confidence=80.0,
               metadata={"expected_edge_bps": edge}, intent=_I())


def make_df(volume=1_000_000, n=60, price=100.0):
    rng = np.random.default_rng(1)
    close = price * np.exp(np.cumsum(rng.normal(0, 0.005, n)))
    close = close / close[-1] * price
    return pd.DataFrame({"close": close, "volume": np.full(n, float(volume))},
                        index=pd.date_range("2026-01-01", periods=n, freq="D"))


def build(tmp_path, tmp_data_dir, flag, **over):
    s = Settings(DATA_DIR=str(tmp_data_dir), RUNTIME_USE_DECISION_LAYER=flag, PAPER_INITIAL_CASH=100000.0, **over)
    eng = PaperTradingEngine(PaperTradingDependencies(
        ledger_store=PaperLedgerStore(s, base_dir=tmp_path), strategy_engine=StrategyEngine(s),
        data_service=MarketDataService(s), settings=s))
    state = eng.initialize_account("acc", 100000)
    return s, eng, state


def req():
    return PaperRunRequest(account_id="acc", symbols=["ASELS"], strategy_name="x", source="mock", timeframe="1d",
                           metadata={"decision_now": NOW.isoformat()})


def run_entry(eng, state, df, edge=300.0):
    res = PaperRunResult(account=state.account, status="SUCCESS")
    state = eng._execute_orders(req(), state, [("ASELS", make_sig(edge), None, None, df)], {"ASELS": df}, res)
    return state, res


def test_illiquid_entry_rejected_with_reason_and_logged(tmp_path, tmp_data_dir):
    s, eng, state = build(tmp_path, tmp_data_dir, True)
    state, res = run_entry(eng, state, make_df(volume=100))  # ADV ~10k TRY << 5M
    assert res.orders == [] and res.fills == []
    dec = res.metadata["decisions"]
    assert len(dec) == 1 and dec[0]["allowed"] is False
    assert "sizing_rejected" in dec[0]["reasons"] and "illiquid" in dec[0]["reasons"]
    assert res.metadata["rejection_reasons"]["illiquid"] == 1
    summ = res.summary()
    assert summ["decisions"] and summ["rejection_reasons"]["illiquid"] == 1
    lines = (tmp_data_dir / "paper" / "decisions.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["symbol"] == "ASELS"
    assert "No real order sent." in lines[0]


def test_binding_constraint_sizes_below_legacy(tmp_path, tmp_data_dir):
    df = make_df(volume=1_000_000)
    # legacy size first (flag off)
    (tmp_path / "off").mkdir()
    (tmp_data_dir / "off").mkdir()
    _, eng_off, st_off = build(tmp_path / "off", tmp_data_dir / "off", False)
    _, res_off = run_entry(eng_off, st_off, df)
    legacy_qty = res_off.orders[0].quantity

    (tmp_path / "on").mkdir()
    (tmp_data_dir / "on").mkdir()
    _, eng, st = build(tmp_path / "on", tmp_data_dir / "on", True, RISK_MAX_POSITION_PCT=0.02)
    _, res = run_entry(eng, st, df)
    d = res.metadata["decisions"][0]
    assert d["allowed"] is True, d
    assert d["binding_constraint"] == "max_position"
    assert 0 < res.orders[0].quantity < legacy_qty
    assert res.orders[0].quantity == d["qty"] and d["legacy_qty"] == legacy_qty


def test_flag_off_identical_no_artifacts(tmp_path, tmp_data_dir):
    s, eng, state = build(tmp_path, tmp_data_dir, False)
    state, res = run_entry(eng, state, make_df(volume=100))  # would be rejected if layer were on
    assert len(res.orders) == 1 and len(res.fills) == 1
    assert "decisions" not in res.metadata and "decisions" not in res.summary()
    assert not (tmp_data_dir / "paper" / "decisions.jsonl").exists()
    assert set(res.summary()) == {"account_id", "signals_count", "risk_decisions_count", "orders_count",
                                  "fills_count", "cash", "equity", "status", "issues_count"}


def test_guard_trip_stops_entries_but_allows_exits(tmp_path, tmp_data_dir):
    s, eng, state = build(tmp_path, tmp_data_dir, True)
    ks = KillSwitchManager(s, tmp_data_dir)
    guard = DailyLossGuard(s, state_path=tmp_data_dir / "risk" / "g.json", kill_switch=ks, audit=NoAudit())
    eng.decision_guard = guard
    eng.decision_clock = lambda: NOW
    # open a position for the exit leg
    state.positions.append(PaperPosition(position_id="p1", account_id="acc", symbol="THYAO",
                                         side=PaperPositionSide.LONG, quantity=10, avg_entry_price=50.0,
                                         last_price=50.0, market_value=500.0))
    eng.ledger_store.save(state)
    guard.update(100_000, 0, NOW)
    guard.update(97_000, -3_000, NOW)
    assert guard.state["state"] == "HALTED_FOR_DAY"

    state, res = run_entry(eng, eng.load_state("acc"), make_df())
    d = res.metadata["decisions"][0]
    assert not d["allowed"] and any(r.startswith("guard_halted") for r in d["reasons"])
    assert res.orders == []

    out = eng.close_position("acc", "THYAO", manual_price=55.0, execution_mode=PaperExecutionMode.MANUAL_PRICE)
    assert len(out.fills) == 1 and out.positions == []


def test_closed_trade_pnl_feeds_guard_consecutive_losses(tmp_path, tmp_data_dir):
    s, eng, state = build(tmp_path, tmp_data_dir, True, RISK_MAX_CONSECUTIVE_LOSSES=2)
    ks = KillSwitchManager(s, tmp_data_dir)
    guard = DailyLossGuard(s, state_path=tmp_data_dir / "risk" / "g2.json", kill_switch=ks, audit=NoAudit())
    eng.decision_guard = guard
    eng.decision_clock = lambda: NOW
    guard.max_consecutive = 2
    for i, sym in enumerate(["AAA", "BBB"]):
        state = eng.load_state("acc")
        # entry fill then losing exit via the engine
        df = make_df()
        res = PaperRunResult(account=state.account, status="SUCCESS")
        sig = make_sig()
        sig.symbol = sym
        state = eng._execute_orders(req(), state, [(sym, sig, None, None, df)], {sym: df}, res)
        eng.ledger_store.save(state)
        assert res.orders, res.metadata
        eng.close_position("acc", sym, manual_price=99.5, execution_mode=PaperExecutionMode.MANUAL_PRICE)
    assert guard.state["consecutive_losses"] >= 2
    assert guard.state["state"] == "HALTED_FOR_DAY"
    assert guard.state["trip_kind"] in ("consecutive_losses", "daily_loss")
