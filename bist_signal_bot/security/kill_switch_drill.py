"""Automated kill-switch drill. Runs ONLY in an isolated temporary data dir (never touches real data/kill switch).

Steps: activate -> paper entries refused (PaperDecisionHook + forward run-daily KILL_SWITCH, no decisions/entries)
-> reduce-only exits still allowed -> deactivate -> resume verified. Returns a Turkish report.
Simulation only; no real order is ever sent."""
from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

NO_ORDER = "No real order sent."
_D_END = "2026-09-30"
_PF = json.dumps([{"family": "xs_momentum", "params": {"lookback": 20, "skip": 0}, "horizon": 5, "top_n": 5}])


def _frames(end: str, days: int = 160, n_sym: int = 25, seed: int = 3) -> dict:
    import numpy as np
    import pandas as pd
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(end=end, periods=days)
    out = {}
    for k in range(n_sym):
        c = 50 * np.exp(np.cumsum(rng.normal(0.0005, 0.015, days)))
        o = np.concatenate([[50.0], c[:-1]]) * (1 + rng.normal(0, 0.003, days))
        out[f"S{k:02d}"] = pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.001, "low": np.minimum(o, c) * 0.999,
                                         "close": c, "volume": rng.uniform(0.8, 1.2, days) * 2e6}, index=idx)
    c = 100 * np.exp(np.cumsum(rng.normal(0, .01, days)))
    mkt = pd.DataFrame({"close": c}, index=idx)
    mkt["open"] = mkt["close"].shift(1).fillna(100.0)
    mkt["high"], mkt["low"] = mkt[["open", "close"]].max(axis=1) * 1.001, mkt[["open", "close"]].min(axis=1) * 0.999
    mkt["volume"] = 1e6
    out["XU100"], out["USDTRY"] = mkt, mkt.copy()
    return out


def run_kill_switch_drill(settings=None, workdir=None) -> dict:
    """Run the drill. ``settings`` only supplies the Settings class/other values; DATA_DIR is always an isolated tmp dir.
    Returns {ok, checks: [(name, ok, detail)], report_tr, workdir}."""
    from bist_signal_bot.config.settings import Settings
    from bist_signal_bot.daily.fetch import SOURCE, clean_daily
    from bist_signal_bot.forward import shadow as S
    from bist_signal_bot.forward.chain import HashChain
    from bist_signal_bot.forward.config import ForwardConfig
    from bist_signal_bot.intraday.archive import BarArchive
    from bist_signal_bot.intraday.sessions import IST
    from bist_signal_bot.paper.decision_hook import PaperDecisionHook
    from bist_signal_bot.risk.daily_loss import DailyLossGuard
    from bist_signal_bot.security.kill_switch import KillSwitchManager
    from bist_signal_bot.security.models import KillSwitchScope

    own = None
    if workdir is None:
        own = tempfile.TemporaryDirectory(prefix="ks_drill_")
        workdir = own.name
    root = Path(workdir)
    checks: list = []

    def chk(name, ok, detail=""):
        checks.append((name, bool(ok), str(detail)))

    arch = None
    try:
        cls = type(settings) if settings is not None else Settings
        st = cls(DATA_DIR=str(root / "data"), FORWARD_PORTFOLIOS=_PF, RUNTIME_USE_DAILY_OVERLAY=False)
        ks = KillSwitchManager(st, root / "data")
        chk("izole_veri_dizini", ks.file_path.resolve().is_relative_to(root.resolve()), ks.file_path)
        chk("baslangic_pasif", not ks.is_active(KillSwitchScope.PAPER))

        # synthetic daily archive (isolated)
        frames = _frames(_D_END)
        arch = BarArchive(path=root / "bars.sqlite")
        for sym, df in frames.items():
            arch.upsert_bars(clean_daily(df), sym, "1d", SOURCE, adjusted=True)
        cfg = ForwardConfig.from_settings(st, forward_dir=root / "fwd", archive_path=root / "bars.sqlite",
                                          ledger_path=root / "no_ledger.sqlite")
        now = datetime.fromisoformat(f"{_D_END}T19:30:00")

        # paper hook fixtures (Tuesday-Friday 11:00 Istanbul, inside the continuous session)
        t_in = datetime(2026, 9, 30, 11, 0, tzinfo=IST)
        hook = PaperDecisionHook(st, guard=DailyLossGuard(st, state_path=root / "risk_state.json"),
                                 log_path=root / "paper_decisions.jsonl")
        px = frames["S00"].tail(80).copy()
        state = SimpleNamespace(account=SimpleNamespace(equity=100000.0, cash=100000.0), positions=[], trades=[])
        sig = SimpleNamespace(confidence=0.9, metadata={"expected_edge_bps": 200.0}, params={})
        meta = {"decision_now": t_in.isoformat()}

        # 1) activate
        ks.activate([KillSwitchScope.ALL], "kill-switch-drill")
        chk("aktivasyon", ks.is_active(KillSwitchScope.PAPER) and ks.is_active(KillSwitchScope.ALL))

        # 2) entries refused
        qty, rec = hook.gate_entry("S00", sig, px, state, 100.0, "1d", meta)
        chk("paper_giris_reddedildi", qty == 0 and not rec["allowed"], rec.get("reasons"))
        chk("red_nedeni_kill_switch", any("kill_switch" in str(r) for r in rec.get("reasons", [])), rec.get("reasons"))

        # 3) forward run-daily -> KILL_SWITCH, no decisions / entries
        r = S.run_daily(cfg, now=now, fetch=False, archive=arch)
        n_dec = len([x for x in HashChain(cfg.decisions_path).records() if x.get("type") == "decision"])
        chk("forward_status_KILL_SWITCH", r["status"] == "KILL_SWITCH", r["status"])
        chk("forward_karar_yok", n_dec == 0 and r["decisions_written"] == 0 and r["entries_written"] == 0,
            f"decisions={n_dec}")

        # 4) exits allowed (reduce-only)
        ex = hook.layer.decide(SimpleNamespace(symbol="S00", confidence=1.0, price=50.0, reduce_only=True,
                                               qty=10, expected_edge_bps=None),
                               {"now": t_in, "price": 50.0, "qty": 10, "reduce_only": True})
        chk("cikis_serbest_reduce_only", bool(ex.allowed) and "reduce_only_exit" in ex.reasons, ex.reasons)

        # 5) deactivate + resume
        ks.deactivate(confirm=True)
        chk("deaktivasyon", not ks.is_active(KillSwitchScope.ALL) and not ks.is_active(KillSwitchScope.PAPER))
        hook2 = PaperDecisionHook(st, guard=DailyLossGuard(st, state_path=root / "risk_state2.json"),
                                  log_path=root / "paper_decisions2.jsonl")
        ok_guard, why = hook2.guard.can_open_new_position(t_in)
        chk("paper_giris_yolu_acik", ok_guard, why)
        r2 = S.run_daily(cfg, now=now, fetch=False, archive=arch)
        n_dec2 = len([x for x in HashChain(cfg.decisions_path).records() if x.get("type") == "decision"])
        chk("forward_devam_OK", r2["status"] == "OK" and n_dec2 > 0, f"status={r2['status']} decisions={n_dec2}")
    except Exception as e:  # noqa: BLE001 - fail closed: a drill that crashes is a FAILED drill
        chk("drill_hatasiz_calisti", False, f"{type(e).__name__}: {e}")
    finally:
        if arch is not None:
            arch.close()
        if own is not None:
            own.cleanup()

    ok = bool(checks) and all(c[1] for c in checks)
    lines = ["Kill-switch tatbikati (izole gecici dizin, gercek veriye dokunulmadi)",
             f"Sonuc: {'BASARILI' if ok else 'BASARISIZ'}"]
    lines += [f"  [{'OK' if o else 'HATA'}] {n}" + (f" - {d}" if d and not o else "") for n, o, d in checks]
    lines.append("Not: Yalnizca paper/simulasyon; " + NO_ORDER)
    return {"ok": ok, "checks": checks, "report_tr": "\n".join(lines), "disclaimer": NO_ORDER}
