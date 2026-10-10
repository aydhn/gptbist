"""Forward SHADOW paper trading daily job. Simulation only; no real order is ever sent.

Flow: lock -> frozen portfolios -> kill switch -> incremental daily archive refresh (no universe sync) -> freshness
gate -> outcomes (entries/exits, hash-chained) -> decisions (hash-chained, written BEFORE outcomes exist) -> NAV
replay -> state/heartbeat/alerts. Idempotent: re-running the same day writes nothing new.
"""
from __future__ import annotations

import json
import os
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from bist_signal_bot.forward import NO_ORDER
from bist_signal_bot.forward.chain import HashChain
from bist_signal_bot.forward.config import (PRIMARY, SCENARIOS, ForwardConfig, freeze_portfolios,
                                            load_portfolios, utcnow_iso)

SURVIVORSHIP = "Survivorship bias in the research universe; forward results are the unbiased test."


# ---------------- time / freshness ----------------
def _ist(now: Optional[datetime]) -> datetime:
    from bist_signal_bot.intraday.sessions import to_istanbul
    if now is None:
        from bist_signal_bot.core.time_utils import istanbul_now
        return istanbul_now()
    return to_istanbul(now)


def expected_session(now: datetime, ready_time: str = "18:30") -> date:
    """Newest session whose daily bar must be complete at ``now`` (Istanbul)."""
    from bist_signal_bot.intraday.sessions import is_trading_day, previous_trading_day
    now = _ist(now)
    hh, mm = (int(x) for x in ready_time.split(":"))
    d = now.date()
    if is_trading_day(d) and (now.hour, now.minute) >= (hh, mm):
        return d
    return previous_trading_day(d)


def session_lag(last: Optional[date], expected: date) -> int:
    """Trading sessions between the newest bar and the expected session (0 = fresh)."""
    from bist_signal_bot.intraday.sessions import is_trading_day
    if last is None:
        return 999
    n, d = 0, last
    while d < expected and n < 400:
        d += timedelta(days=1)
        if is_trading_day(d):
            n += 1
    return n


def series_freshness(archive, expected: date, min_cov: float = 0.8) -> dict:
    """Per-series freshness from the daily archive: panel (max / coverage), XU100, USDTRY."""
    from bist_signal_bot.daily.fetch import BENCHMARKS, INTERVAL
    syms = [s for s in archive.symbols(INTERVAL) if s not in BENCHMARKS]
    lasts = {}
    for s in syms:
        ts = archive.last_ts(s, INTERVAL)
        if ts is not None:
            lasts[s] = ts.date()
    out: dict = {"expected_session": str(expected), "n_symbols": len(lasts)}
    if lasts:
        usable = sorted((d for d in lasts.values() if d <= expected), reverse=True)
        n_all = len(lasts)
        mx = None
        for k, d in enumerate(usable, 1):  # newest date that >= min_cov of ALL symbols have reached
            if k / n_all >= min_cov:
                mx = d
                break
        if mx is None and usable:
            mx = usable[-1]
        out["panel_last"] = str(mx) if mx else None
        out["panel_lag_sessions"] = session_lag(mx, expected)
        out["coverage"] = (sum(1 for d in usable if d >= mx) / n_all) if mx else 0.0
        out["newest_raw_bar"] = str(max(lasts.values()))
    else:
        out.update(panel_last=None, panel_lag_sessions=999, coverage=0.0, newest_raw_bar=None)
    for b in BENCHMARKS:
        ts = archive.last_ts(b, INTERVAL)
        last = ts.date() if ts is not None else None
        out[b] = {"last": str(last) if last else None, "lag_sessions": session_lag(last, expected)}
    return out


# ---------------- context / decisions ----------------
def build_ctx(archive, settings, as_of: Optional[pd.Timestamp] = None):
    """DailyContext from the archive, every series truncated to <= as_of (causality)."""
    from bist_signal_bot.daily.panel import load_benchmark, load_daily_panel
    from bist_signal_bot.edge_validation.xsection import DailyContext
    panel = load_daily_panel(archive)
    bm, fx = load_benchmark(archive, "XU100"), load_benchmark(archive, "USDTRY")
    return ctx_from_panel(panel, bm, fx, settings, as_of)


def ctx_from_panel(panel, bm, fx, settings, as_of=None):
    from bist_signal_bot.edge_validation.xsection import DailyContext
    if as_of is not None:
        a = pd.Timestamp(as_of)
        panel = {s: d[d.index <= a] for s, d in panel.items()}
        panel = {s: d for s, d in panel.items() if len(d)}
        bm = bm[bm.index <= a] if bm is not None and len(bm) else bm
        fx = fx[fx.index <= a] if fx is not None and len(fx) else fx
    return DailyContext.from_panel(panel, bm["close"] if bm is not None and len(bm) else None, settings,
                                   usdtry=fx["close"] if fx is not None and len(fx) else None)


def compute_decision(ctx, family, params: dict, top_n: int, as_of, capital: float, score_cache: dict = None) -> dict:
    """Top-N picks at the close of ``as_of`` using only data <= as_of (ctx must not hold later rows)."""
    a = pd.Timestamp(as_of)
    if a not in ctx.index:
        raise ValueError(f"as_of {a.date()} not a session of the context")
    key = (family.name, json.dumps(params, sort_keys=True))
    if score_cache is not None and key in score_cache:
        S = score_cache[key]
    else:
        S = family.score(ctx, params).reindex(index=ctx.index, columns=ctx.symbols)
        if score_cache is not None:
            score_cache[key] = S
    i = ctx.index.get_loc(a)
    row, mask = S.iloc[i].to_numpy(float), ctx.universe_mask.iloc[i].to_numpy(bool)
    cand = np.flatnonzero(mask & np.isfinite(row))
    order = np.lexsort((cand, -row[cand]))
    pick = cand[order][:top_n]
    adv = ctx.adv.iloc[i].to_numpy(float)
    picks = [{"symbol": ctx.symbols[j], "rank": r, "score": float(row[j]), "price": float(ctx.close.iloc[i, j]),
              "adv": float(adv[j]), "order_value": capital / top_n} for r, j in enumerate(pick, 1)]
    return {"as_of": str(a.date()), "picks": picks, "eligible_n": int(len(cand)), "n_symbols": len(ctx.symbols)}


def is_due(prev_as_of: Optional[str], as_of, horizon: int, index: pd.DatetimeIndex) -> bool:
    if prev_as_of is None:
        return True
    a, p = pd.Timestamp(as_of), pd.Timestamp(prev_as_of)
    if a <= p:
        return False
    return int(((index > p) & (index <= a)).sum()) >= int(horizon)


# ---------------- misc helpers ----------------
def _json_append(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, sort_keys=True, default=str) + "\n")


def read_state(cfg: ForwardConfig) -> dict:
    try:
        return json.loads(cfg.state_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def write_state(cfg: ForwardConfig, st: dict) -> None:
    tmp = cfg.state_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=2, sort_keys=True, default=str), encoding="utf-8")
    os.replace(tmp, cfg.state_path)


class RunLock:
    def __init__(self, path: Path, stale_seconds: int = 7200):
        self.path, self.stale = Path(path), stale_seconds
        self.fd = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists() and time.time() - self.path.stat().st_mtime > self.stale:
            self.path.unlink(missing_ok=True)
        try:
            self.fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise RuntimeError("forward run already in progress (lock held)")
        os.write(self.fd, f"{os.getpid()} {utcnow_iso()}".encode())
        return self

    def __exit__(self, *a):
        if self.fd is not None:
            os.close(self.fd)
        self.path.unlink(missing_ok=True)


def kill_switch_state(cfg: ForwardConfig) -> dict:
    """Enabled if the ALL / PAPER / SCHEDULER scope is active. Corrupt file fails closed (security module)."""
    from bist_signal_bot.security.kill_switch import KillSwitchManager
    from bist_signal_bot.security.models import KillSwitchScope
    km = KillSwitchManager(cfg.settings, cfg.data_dir)
    st = km.status()
    active = any(km.is_active(sc) for sc in (KillSwitchScope.ALL, KillSwitchScope.PAPER, KillSwitchScope.SCHEDULER))
    return {"active": bool(active), "reason": st.get("reason"), "scopes": st.get("scopes"),
            "activated_at": st.get("activated_at")}


def ensure_chains(cfg: ForwardConfig, doc: dict):
    """Create decisions/outcomes chains with a header (plan + decision rule written BEFORE any data)."""
    dec, out = HashChain(cfg.decisions_path), HashChain(cfg.outcomes_path)
    for ch, name in ((dec, "decisions"), (out, "outcomes")):
        if not ch.path.exists() or ch.verify()["n"] == 0:
            ch.append("header", {"ledger": name, "created_at": utcnow_iso(), "plan": cfg.plan(),
                                 "portfolios_hash": doc["content_hash"], "n_portfolios": doc["n_portfolios"],
                                 "planned_start_date": str(_ist(None).date()), "survivorship": SURVIVORSHIP,
                                 "disclaimer": NO_ORDER})
    return dec, out


def cost_models(settings) -> dict:
    from bist_signal_bot.edge_validation.costs_daily import DailyCostModel
    return {s: DailyCostModel.from_settings(settings, scenario=s) for s in SCENARIOS}


def refresh_archive(cfg: ForwardConfig, archive, fetch_fn=None) -> dict:
    """Incremental refresh of the symbols already archived (+ XU100/USDTRY). No universe sync."""
    from bist_signal_bot.daily.fetch import BENCHMARKS, INTERVAL, DailyFetcher, DailyUpdater
    syms = [s for s in archive.symbols(INTERVAL) if s not in BENCHMARKS]
    if not syms:
        return {"error": "empty_archive", "failures": 0}
    rep = DailyUpdater(archive, DailyFetcher(fetch_fn=fetch_fn, settings=cfg.settings, archive=archive)).update(
        syms, include_benchmarks=True)
    return {"symbols": len(syms), "inserted": rep.inserted, "updated": rep.updated, "failures": len(rep.failures),
            "failure_sample": dict(list(rep.failures.items())[:5])}


# ---------------- main job ----------------
def run_daily(cfg: ForwardConfig, now: Optional[datetime] = None, fetch: bool = True, fetch_fn=None,
              archive=None, now_override: bool = False) -> dict:
    """One idempotent pass. Returns a summary dict (also appended to runs.jsonl)."""
    from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
    from bist_signal_bot.forward import health as H
    from bist_signal_bot.intraday.archive import BarArchive
    cfg.ensure()
    t0 = time.time()
    res: dict = {"started_at": utcnow_iso(), "disclaimer": NO_ORDER, "decisions_written": 0, "entries_written": 0,
                 "exits_written": 0, "errors": [], "status": "OK", "decisions": [], "skipped": []}
    own_archive = archive is None
    try:
        with RunLock(cfg.lock_path):
            doc = freeze_portfolios(cfg)
            res["portfolios_frozen"] = doc["n_portfolios"]
            dec_ch, out_ch = ensure_chains(cfg, doc)
            for ch in (dec_ch, out_ch):
                v = ch.verify()
                if not v["ok"]:
                    raise RuntimeError(f"hash chain broken: {ch.path.name} {v['error']} line {v['line']}")
            ks = kill_switch_state(cfg)
            res["kill_switch"] = ks
            if own_archive:
                archive = BarArchive(path=cfg.archive_path, settings=cfg.settings)
            try:
                if fetch:
                    try:
                        res["fetch"] = refresh_archive(cfg, archive, fetch_fn)
                    except Exception as exc:  # noqa: BLE001 - stale gate below protects decisions
                        res["fetch"] = {"error": f"{type(exc).__name__}: {exc}"}
                        res["errors"].append(f"fetch: {exc}")
                ready = cfg.s("FORWARD_SESSION_READY_TIME", "18:30")
                exp = expected_session(now, ready)
                fr = series_freshness(archive, exp, cfg.f("FORWARD_MIN_COVERAGE", 0.8))
                res["freshness"] = fr
                cut = pd.Timestamp(fr["panel_last"] or exp)
                ctx_full = build_ctx(archive, cfg.settings, cut)
                L = ctx_full.index[-1]
                gate_ok = (fr["panel_lag_sessions"] <= cfg.i("FORWARD_MAX_LAG_SESSIONS", 0)
                           and fr["coverage"] >= cfg.f("FORWARD_MIN_COVERAGE", 0.8))
                res["as_of"] = str(L.date())
                res["freshness_gate"] = "PASS" if gate_ok else "STALE"
                _process(cfg, doc, ctx_full, L, gate_ok, ks, dec_ch, out_ch, res, now, now_override,
                         DAILY_FAMILIES)
            finally:
                if own_archive:
                    archive.close()
            if not gate_ok:
                res["status"] = "STALE"
            elif ks["active"]:
                res["status"] = "KILL_SWITCH"
    except Exception as exc:  # noqa: BLE001
        res["status"] = "FAILED"
        res["errors"].append(f"{type(exc).__name__}: {exc}")
    res["finished_at"], res["elapsed_s"] = utcnow_iso(), round(time.time() - t0, 2)
    try:
        H.after_run(cfg, res, now)
    except Exception as exc:  # noqa: BLE001
        res["errors"].append(f"after_run: {exc}")
    return res


def _process(cfg, doc, ctx, L, gate_ok, ks, dec_ch, out_ch, res, now, now_override, families) -> None:
    capital = cfg.f("FORWARD_CAPITAL_TRY", 100000.0)
    cms = cost_models(cfg.settings)
    dec_recs = list(dec_ch.iter_type("decision"))
    entries = {r["decision_hash"]: r for r in out_ch.iter_type("entry")}
    exits = {r["decision_hash"]: r for r in out_ch.iter_type("exit")}
    by_pf: dict = {}
    for d in dec_recs:
        by_pf.setdefault(d["portfolio_id"], []).append(d)
    score_cache: dict = {}
    for p in doc["portfolios"]:
        pid = p["id"]
        decs = sorted(by_pf.get(pid, []), key=lambda r: r["as_of"])
        # 1) outcomes for existing decisions (entries blocked while the kill switch is active; exits allowed)
        blocked = {d["hash"] for d in decs if ks["active"] and d["hash"] not in entries}
        nav, new = (None, [])
        if decs:
            nav, new = _replay_safe(ctx, decs, entries, exits, cms, capital, blocked)
            for typ, rec in new:
                out_ch.append(typ, rec)
                res["entries_written" if typ == "entry" else "exits_written"] += 1
        # 2) new decision (only on a fresh gate, kill switch off, and when due)
        if gate_ok and not ks["active"]:
            fam = families.get(p["family"])
            if fam is None:
                res["skipped"].append([pid, "family_not_registered"])
            elif any(d["as_of"] == str(L.date()) for d in decs):
                res["skipped"].append([pid, "already_decided"])
            elif not _mask_ok(fam, ctx, p["params"], L, score_cache):
                res["skipped"].append([pid, "rebalance_mask_off"])
            elif not is_due(decs[-1]["as_of"] if decs else None, L, p["horizon"], ctx.index):
                res["skipped"].append([pid, "not_due"])
            else:
                try:
                    body = compute_decision(ctx, fam, p["params"], p["top_n"], L, capital, score_cache)
                    rec = out = dec_ch.append("decision", {
                        "portfolio_id": pid, "family": p["family"], "params": p["params"],
                        "horizon": p["horizon"], "top_n": p["top_n"], "decided_at": utcnow_iso(),
                        "now_override": bool(now_override),
                        "data_last_dates": {"panel": res["freshness"].get("panel_last"),
                                            "XU100": res["freshness"].get("XU100", {}).get("last"),
                                            "USDTRY": res["freshness"].get("USDTRY", {}).get("last")},
                        "entry_rule": "next session open", "exit_rule": f"close of as_of+{p['horizon']} sessions",
                        "disclaimer": NO_ORDER, **body})
                    res["decisions_written"] += 1
                    res["decisions"].append([pid, body["as_of"], len(body["picks"])])
                    decs.append(rec)
                except Exception as exc:  # noqa: BLE001
                    res["errors"].append(f"decision {pid}: {type(exc).__name__}: {exc}")
        elif not gate_ok:
            res["skipped"].append([pid, "stale_data"])
        else:
            res["skipped"].append([pid, "kill_switch_active"])
        # 3) NAV csv (derived artifact, rewritten)
        if decs:
            nav, new = _replay_safe(ctx, decs, entries, exits, cms, capital, blocked)
            for typ, rec in new:  # only entries/exits that became due in this very pass (none normally)
                out_ch.append(typ, rec)
            if nav is not None:
                nav.index.name = "date"
                nav.to_csv(cfg.nav_dir / f"{pid}.csv", float_format="%.6f")


def _replay_safe(ctx, decs, entries, exits, cms, capital, blocked):
    from bist_signal_bot.forward.sim import replay
    return replay(ctx, decs, entries, exits, cms, capital, blocked)


def _mask_ok(fam, ctx, params, L, cache) -> bool:
    """Calendar families expose a causal ``rebalance_mask``; a basket may only start where it is True."""
    fn = getattr(fam, "rebalance_mask", None)
    if not callable(fn):
        return True
    key = ("mask", fam.name, json.dumps(params, sort_keys=True))
    if key not in cache:
        cache[key] = fn(ctx, params)
    m = cache[key]
    try:
        return bool(m.reindex(ctx.index).fillna(False).loc[L])
    except Exception:  # noqa: BLE001
        return False
