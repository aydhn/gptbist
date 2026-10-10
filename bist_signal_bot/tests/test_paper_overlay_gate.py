"""Daily overlay wired into PaperDecisionHook.gate_entry (offline). No real order sent."""
from datetime import datetime
from types import SimpleNamespace

import numpy as np
import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.intraday.sessions import IST
from bist_signal_bot.paper.decision_hook import PaperDecisionHook
from bist_signal_bot.risk.overlay_gate import OverlayGate

NOW = datetime(2026, 3, 9, 11, 0, tzinfo=IST)


def nav_series(vals, end="2026-03-06"):
    idx = pd.bdate_range(end=end, periods=len(vals))
    return pd.Series(vals, index=idx)


FLAT = nav_series([100000.0] * 30)
DRAWDOWN = nav_series(list(np.linspace(100000, 100000, 20)) + list(np.linspace(100000, 84000, 10)))  # -16% dd


def make_hook(tmp_path, flag, nav, layer_qty=100.0, **over):
    s = Settings(RUNTIME_USE_DAILY_OVERLAY=flag, **over)
    hook = PaperDecisionHook(s, guard=object(), log_path=tmp_path / "decisions.jsonl")
    hook._layer = SimpleNamespace(decide=lambda sv, ctx: SimpleNamespace(
        allowed=True, qty=layer_qty, reasons=[], sizing=SimpleNamespace(method="x"), guard_state={"state": "OK"}))
    hook._overlay = OverlayGate(s, nav_history=nav)
    return hook


def run(hook, legacy=100.0):
    df = pd.DataFrame({"close": [100.0] * 60, "volume": [1e6] * 60},
                      index=pd.date_range("2026-01-01", periods=60, freq="D"))
    state = SimpleNamespace(account=SimpleNamespace(equity=84000.0, cash=1e6), positions=[], trades=[])
    sig = SimpleNamespace(confidence=80.0, metadata={}, params={})
    return hook.gate_entry("ASELS", sig, df, state, legacy, "1d", {"decision_now": NOW.isoformat()})


def test_flag_off_unchanged(tmp_path):
    qty, rec = run(make_hook(tmp_path, False, DRAWDOWN))
    assert qty == 100.0 and "overlay" not in rec


def test_drawdown_shrinks_qty_floor_never_up(tmp_path):
    qty, rec = run(make_hook(tmp_path, True, DRAWDOWN))
    assert 0 < qty < 100.0 and qty == int(qty)
    assert rec["overlay"]["qty_after"] <= rec["overlay"]["qty_before"]
    assert "drawdown derisk" in rec["overlay"]["reasons"]
    assert any(str(r).startswith("overlay_scale") for r in rec["reasons"])
    assert "No real order sent." in (tmp_path / "decisions.jsonl").read_text(encoding="utf-8")


def test_flat_nav_never_increases(tmp_path):
    qty, rec = run(make_hook(tmp_path, True, FLAT))
    assert qty == 100.0 and rec["overlay"]["scale"] <= 1.0


def test_warmup_scale_one(tmp_path):
    h = make_hook(tmp_path, True, nav_series([100000.0]))
    qty, rec = run(h)
    assert qty == 100.0 and rec["overlay"]["reasons"] == ["warmup"]


def test_halt_rejects_entry(tmp_path):
    nav = nav_series([100000.0] * 10 + [75000.0] * 3)
    qty, rec = run(make_hook(tmp_path, True, nav))
    assert qty == 0 and rec["allowed"] is False
    assert "overlay_scale" in rec["reasons"] and "halt" in rec["overlay"]["reasons"]


def test_today_not_used_causality(tmp_path):
    g = OverlayGate(Settings(), nav_history=DRAWDOWN)
    a = g.current_scale(NOW).scale
    g.record(NOW, 1.0)  # absurd intraday equity of the same day must not matter
    assert g.current_scale(NOW).scale == a


def test_exception_falls_back_to_half(tmp_path):
    h = make_hook(tmp_path, True, FLAT)

    class Boom:
        def record(self, *a):
            pass

        def current_scale(self, *a):
            raise RuntimeError("boom")
    h._overlay = Boom()
    qty, rec = run(h)
    assert qty == 50.0 and any("overlay_error" in r for r in rec["overlay"]["reasons"])

    g = OverlayGate(Settings(DAILY_OVERLAY_MAX_DD=0.2), nav_history=FLAT)
    g._nav[list(g._nav)[3]] = 0.0  # corrupt history -> internal error path
    r = g.current_scale(NOW)
    assert r.scale == 0.5 and r.reasons[0].startswith("overlay_error")


def test_exits_not_gated(tmp_path):
    # Exits never call gate_entry; the hook exposes the overlay only through gate_entry.
    import inspect
    from bist_signal_bot.paper import engine
    src = inspect.getsource(engine)
    assert src.count("gate_entry(") == 1
