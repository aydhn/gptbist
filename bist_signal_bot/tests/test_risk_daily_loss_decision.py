"""Daily-loss guard, decision layer and risk CLI (offline, fake clock)."""
import json
from datetime import datetime
from types import SimpleNamespace

import pytest

from bist_signal_bot.cli import risk_cli
from bist_signal_bot.cli.main import run_cli
from bist_signal_bot.intraday.sessions import IST
from bist_signal_bot.risk.daily_loss import ACTIVE, HALTED_FOR_DAY, DailyLossGuard
from bist_signal_bot.risk.decision import DecisionLayer
from bist_signal_bot.security.kill_switch import KillSwitchManager
from bist_signal_bot.security.models import KillSwitchScope


class NoAudit:
    def __init__(self):
        self.events = []

    def log_event(self, e):
        self.events.append(e)


def at(day, h=11, m=0):
    return datetime(2026, 3, day, h, m, tzinfo=IST)  # 2=Mon ... 6=Fri 7=Sat 9=Mon


@pytest.fixture
def env(tmp_data_dir, settings_factory):
    s = settings_factory()
    ks = KillSwitchManager(s, tmp_data_dir)
    audit = NoAudit()

    def make(**kw):
        return DailyLossGuard(s, state_path=tmp_data_dir / "risk" / "st.json", kill_switch=ks, audit=audit, **kw)
    return SimpleNamespace(s=s, ks=ks, audit=audit, make=make, path=tmp_data_dir / "risk" / "st.json")


def test_daily_loss_boundary(env):
    g = env.make()
    g.update(100_000, 0, at(2))
    g.update(98_001, -1999, at(2))  # -1.999%
    assert g.state["state"] == ACTIVE
    g.update(98_000, -2000, at(2))  # exactly -2.0%
    assert g.state["state"] == HALTED_FOR_DAY and g.state["trip_kind"] == "daily_loss"
    ok, why = g.can_open_new_position(at(2))
    assert not ok and "daily_loss" in why
    assert env.ks.is_active(KillSwitchScope.PAPER)
    assert any(e.event_type.value == "RISK_GUARD_TRIPPED" for e in env.audit.events)


def test_consecutive_losses_trip(env):
    g = env.make()
    g.update(100_000, 0, at(2))
    r = 0.0
    for _ in range(6):
        assert g.state["state"] == ACTIVE
        r -= 10
        g.update(100_000 + r, r, at(2))
    assert g.state["trip_kind"] == "consecutive_losses"


def test_win_resets_streak(env):
    g = env.make()
    g.update(100_000, 0, at(2))
    for r in (-10, -20, -30, -40, -50):
        g.update(100_000 + r, r, at(2))
    g.update(100_000, 10, at(2))
    assert g.state["consecutive_losses"] == 0 and g.state["state"] == ACTIVE


def test_drawdown_needs_explicit_reset(env):
    g = env.make()
    g.update(100_000, 0, at(2))
    g.update(110_000, 10_000, at(2))
    g.update(100_000, 5_000, at(2))  # -9.09% from peak
    assert g.state["trip_kind"] == "drawdown"
    ok, _ = g.can_open_new_position(at(3, 10, 30))  # next trading day open: no auto reset
    assert not ok
    with pytest.raises(ValueError):
        g.reset()
    g.reset(confirm=True, equity=100_000, now=at(3))
    assert g.can_open_new_position(at(3))[0]
    assert not env.ks.is_active(KillSwitchScope.PAPER)


def test_daily_trip_auto_reset_next_trading_day_not_weekend(env):
    g = env.make()
    g.update(100_000, 0, at(6))  # Friday
    g.update(97_000, -3000, at(6))
    assert g.state["state"] == HALTED_FOR_DAY
    assert not g.can_open_new_position(at(7, 11))[0]  # Saturday
    assert not g.can_open_new_position(at(9, 9, 0))[0]  # Monday before open
    assert g.can_open_new_position(at(9, 10, 0))[0]  # Monday open
    assert g.state["state"] == ACTIVE
    assert not env.ks.is_active(KillSwitchScope.PAPER)  # guard-owned switch cleared
    g.update(97_000, 0, at(9, 10, 5))
    assert g.state["start_equity"] == 97_000


def test_exits_allowed_when_halted_and_killswitch_engaged(env):
    g = env.make()
    g.update(100_000, 0, at(2))
    g.update(90_000, -10_000, at(2))
    assert env.ks.is_active(KillSwitchScope.PAPER)
    layer = DecisionLayer(env.s, sizer=None, limits=None, guard=g)
    d = layer.decide({"symbol": "THYAO", "qty": 10, "reduce_only": True}, {"now": at(2), "price": 100.0})
    assert d.allowed and d.qty == 10 and "exit_allowed_despite_halt" in d.reasons and d.no_real_order_sent


def test_manual_kill_switch_not_cleared(env):
    env.ks.activate([KillSwitchScope.ALL], "manual stop", activated_by="human")
    g = env.make()
    g.update(100_000, 0, at(6))
    g.update(90_000, -10_000, at(6))
    assert g.state["state"] == HALTED_FOR_DAY and not g.state["ks_engaged_by_guard"]
    assert env.ks.load_state().activated_by == "human"  # not overwritten
    g.can_open_new_position(at(9, 10, 5))  # guard auto-resets
    assert g.state["state"] == ACTIVE
    assert env.ks.is_active(KillSwitchScope.PAPER)  # still manual
    assert g.can_open_new_position(at(9, 10, 6)) == (False, "kill_switch_active")


def test_persistence_roundtrip_and_corrupt_fails_closed(env):
    g = env.make()
    g.update(100_000, 0, at(2))
    g.update(99_000, -1000, at(2))
    g2 = env.make()
    assert g2.state["start_equity"] == 100_000 and g2.state["equity"] == 99_000
    env.path.write_text("{not json", encoding="utf-8")
    g3 = env.make()
    assert g3.state["state"] == HALTED_FOR_DAY and g3.state["trip_kind"] == "corrupt_state"
    assert not g3.can_open_new_position(at(9, 10, 30))[0]  # no auto-reset for corrupt
    g3.reset(confirm=True)
    assert json.loads(env.path.read_text())["state"] == ACTIVE


# ---- decision layer
class FakeSizer:
    def __init__(self, allowed=True):
        self.allowed = allowed

    def size(self, **kw):
        return SimpleNamespace(allowed=self.allowed, qty=100, notional=10_000.0, reasons=["fake"], risk_bps=5)


class FakeLimits:
    def __init__(self, allowed=True):
        self.allowed = allowed

    def check(self, *a, **k):
        return SimpleNamespace(allowed=self.allowed, reasons=[] if self.allowed else ["max_open_positions"])


def layer(env, limits_ok=True, sizer_ok=True):
    return DecisionLayer(env.s, FakeSizer(sizer_ok), FakeLimits(limits_ok), env.make())


def ctx(now, **kw):
    c = {"now": now, "price": 100.0, "equity": 100_000.0, "bar_value_try": 5_000_000.0,
         "edge_stats": {"expected_edge_bps": 100.0}}
    c.update(kw)
    return c


SIG = {"symbol": "THYAO", "confidence": 1.0}


def test_decision_allows_in_session(env):
    d = layer(env).decide(SIG, ctx(at(2, 11)))
    assert d.allowed and d.qty == 100 and d.no_real_order_sent


def test_decision_blocks_closed_and_auction(env):
    L = layer(env)
    assert L.decide(SIG, ctx(at(7, 11))).reasons == ["market_closed"]
    assert L.decide(SIG, ctx(at(2, 8, 0))).reasons == ["market_closed"]
    assert L.decide(SIG, ctx(at(2, 18, 3))).reasons == ["auction_window_entry_blocked"]
    assert L.decide(SIG, ctx(at(2, 9, 45))).reasons == ["auction_window_entry_blocked"]


def test_decision_guard_first_and_audited(env):
    L = layer(env)
    L.guard.update(100_000, 0, at(2))
    L.guard.update(90_000, -10_000, at(2))
    d = L.decide(SIG, ctx(at(2, 11)))
    assert not d.allowed and d.reasons[0].startswith("guard_halted")
    assert any(e.event_type.value == "RISK_DECISION_REJECTED" for e in env.audit.events)


def test_decision_sizing_limits_and_cost(env):
    assert "sizing_rejected" in layer(env, sizer_ok=False).decide(SIG, ctx(at(2))).reasons
    assert "portfolio_limit" in layer(env, limits_ok=False).decide(SIG, ctx(at(2))).reasons
    d = layer(env).decide(SIG, ctx(at(2), edge_stats={"expected_edge_bps": 5.0}))
    assert not d.allowed and d.reasons[0].startswith("edge_below_cost")
    assert layer(env).decide(SIG, ctx(at(2), edge_stats=None)).reasons == ["no_edge_estimate"]


def test_decision_with_real_sizer_and_limits(env):
    from bist_signal_bot.risk.portfolio_limits import PortfolioLimits
    from bist_signal_bot.risk.sizing_intraday import IntradaySizer
    L = DecisionLayer(env.s, IntradaySizer(env.s), PortfolioLimits(env.s), env.make())
    c = ctx(at(2), asset_vol_annual=0.4, adv_value_try=50_000_000.0, spread_bps=5.0, open_positions=[])
    d = L.decide({"symbol": "THYAO", "confidence": 0.7}, c)
    assert d.no_real_order_sent and d.sizing is not None and d.limits is not None or not d.allowed


# ---- CLI
def test_cli_parser_and_simulate(capsys):
    assert risk_cli.build_parser().parse_args(["reset", "--confirm"]).confirm
    assert run_cli(["risk", "simulate-day"]) == 0
    out = capsys.readouterr().out
    assert "TRIPPED" in out and out.strip().endswith("No real order sent.")


def test_cli_reset_requires_confirm(capsys, monkeypatch, settings_factory):
    monkeypatch.setattr(risk_cli, "get_settings", lambda: settings_factory())
    assert risk_cli.main(["reset"]) == 2
    assert "No real order sent." in capsys.readouterr().out
    assert risk_cli.main(["status"]) == 0
