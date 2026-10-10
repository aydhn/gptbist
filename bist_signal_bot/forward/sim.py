"""Deterministic shadow-portfolio simulation (integer-share lots, DailyCostModel, cash interest).

Replays a portfolio from its append-only decisions + persisted fills. Entry fills/exit proceeds are computed ONCE
(new records are returned for the caller to append) and then read back from the outcomes ledger, so the NAV does
not drift when auto-adjusted history is restated. Simulation only; no real order is ever sent.

Timing (same as the research layer): decision at the CLOSE of ``as_of``; entry at the next session OPEN; exit at the
CLOSE of ``as_of + horizon`` sessions. Between baskets the NAV sits in cash and earns the cash rate (calendar-day
compounding, ``ctx.cash_ret``). Integer lots; disallowed/odd-lot remainder stays in cash.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from bist_signal_bot.forward.config import SCENARIOS


def _sell_bps(cm, price: float, value: float, adv: float) -> float:
    """Exit cost: forced exits ignore the participation cap (still pay the modelled impact)."""
    b = cm.breakdown(price, value, adv, "sell")
    t = b.total_bps if b.allowed else (b.commission_bps + b.bsmv_bps + b.exchange_bps + b.half_spread_bps
                                       + (b.impact_bps if np.isfinite(b.impact_bps) else 0.0))
    return float(t) if np.isfinite(t) else 0.0


def replay(ctx, decisions: List[dict], entries: Dict[str, dict], exits: Dict[str, dict], cost_models: dict,
           capital: float, blocked: Optional[set] = None):
    """Return (nav_df, new_records[(type, payload)]). ``decisions`` sorted by as_of, each with ``hash``.

    nav_df index = sessions from the first decision date; columns nav_<scenario>, ew_nav, xu100_nav, cash_nav.
    """
    blocked = blocked or set()
    if not decisions:
        return None, []
    sess = ctx.index
    pos = {pd.Timestamp(d): i for i, d in enumerate(sess)}
    n = len(sess)
    col = {s: j for j, s in enumerate(ctx.symbols)}
    OP, CL = ctx.open.to_numpy(float), ctx.close.ffill().to_numpy(float)
    cash_ret = ctx.cash_ret.to_numpy(float)
    ent_at, exit_at = defaultdict(list), defaultdict(list)
    first = None
    for d in decisions:
        i = pos.get(pd.Timestamp(d["as_of"]))
        if i is None:
            continue
        first = i if first is None else min(first, i)
        if i + 1 < n:
            ent_at[i + 1].append(d)
        if i + int(d["horizon"]) < n:
            exit_at[i + int(d["horizon"])].append((d, i + 1))
    if first is None:
        return None, []
    cash = {s: float(capital) for s in SCENARIOS}
    held = {s: {} for s in SCENARIOS}  # decision hash -> {sym: dict}
    new: list = []
    nav = {s: np.full(n, np.nan) for s in SCENARIOS}
    for s in SCENARIOS:
        nav[s][first] = cash[s]
    for t in range(first + 1, n):
        for d in ent_at.get(t, []):
            rec = entries.get(d["hash"])
            if rec is None:
                rec = _compute_entry(d, t, ctx, OP, col, cash, cost_models, blocked)
                new.append(("entry", rec))
                entries[d["hash"]] = rec
            for s in SCENARIOS:
                fills = (rec["fills"].get(s) or {})
                cash[s] -= sum(f["cash_out"] for f in fills.values())
                held[s][d["hash"]] = {sym: dict(f, open_cur=float(OP[t, col[sym]])) for sym, f in fills.items()}
        for s in SCENARIOS:
            cash[s] *= 1.0 + (cash_ret[t] if np.isfinite(cash_ret[t]) else 0.0)
        for d, e in exit_at.get(t, []):
            if d["hash"] not in entries:
                continue
            rec = exits.get(d["hash"])
            if rec is None:
                rec = _compute_exit(d, t, entries[d["hash"]], held, CL, col, cost_models)
                rec["exit_date"] = str(pd.Timestamp(sess[t]).date())
                new.append(("exit", rec))
                exits[d["hash"]] = rec
            for s in SCENARIOS:
                cash[s] += float((rec["results"].get(s) or {}).get("total_proceeds", 0.0))
                held[s].pop(d["hash"], None)
        for s in SCENARIOS:
            mv = 0.0
            for h in held[s].values():
                for sym, f in h.items():
                    j = col[sym]
                    if np.isfinite(CL[t, j]) and f["open_cur"] > 0:
                        mv += f["shares"] * f["px"] * CL[t, j] / f["open_cur"]
            nav[s][t] = cash[s] + mv
    idx = sess[first:]
    out = pd.DataFrame({f"nav_{s}": nav[s][first:] for s in SCENARIOS}, index=idx)
    b = ctx.benchmarks().reindex(idx)
    for name, key in (("ew_nav", "ew_universe"), ("xu100_nav", "xu100"), ("cash_nav", "cash")):
        if key in b:
            r = b[key].fillna(0.0).to_numpy(float).copy()
            r[0] = 0.0
            out[name] = capital * np.cumprod(1.0 + r)
    return out, new


def _compute_entry(d, t, ctx, OP, col, cash, cost_models, blocked) -> dict:
    rec = {"portfolio_id": d["portfolio_id"], "decision_hash": d["hash"], "as_of": d["as_of"],
           "entry_date": str(pd.Timestamp(ctx.index[t]).date()), "blocked": d["hash"] in blocked,
           "fills": {s: {} for s in SCENARIOS}, "dropped": {s: [] for s in SCENARIOS}}
    if rec["blocked"]:
        return rec
    top_n = int(d["top_n"])
    for s in SCENARIOS:
        slot = cash[s] / top_n
        cm = cost_models[s]
        for p in d["picks"]:
            j = col.get(p["symbol"])
            px = float(OP[t, j]) if j is not None else float("nan")
            vol = float(ctx.volume.iloc[t, j]) if j is not None else 0.0
            if not (np.isfinite(px) and px > 0 and vol > 0):
                rec["dropped"][s].append([p["symbol"], "no_open_or_no_volume"])
                continue
            bps = cm.cost_bps(px, slot, float(p["adv"]), "buy")
            if not np.isfinite(bps):
                rec["dropped"][s].append([p["symbol"], "cost_model_disallowed"])
                continue
            c = bps / 1e4
            shares = int(math.floor(slot / (px * (1.0 + c))))
            if shares < 1:
                rec["dropped"][s].append([p["symbol"], "lot_too_small"])
                continue
            rec["fills"][s][p["symbol"]] = {"shares": shares, "px": px, "cost_bps": float(bps),
                                           "cash_out": shares * px * (1.0 + c)}
    return rec


def _compute_exit(d, t, entry, held, CL, col, cost_models) -> dict:
    adv = {p["symbol"]: float(p["adv"]) for p in d["picks"]}
    rec = {"portfolio_id": d["portfolio_id"], "decision_hash": d["hash"], "as_of": d["as_of"],
           "entry_date": entry["entry_date"], "exit_date": None, "results": {}}
    for s in SCENARIOS:
        cm = cost_models[s]
        res, tot, spent = {}, 0.0, 0.0
        for sym, f in (held[s].get(d["hash"]) or {}).items():
            j = col[sym]
            close = float(CL[t, j])
            ratio = close / f["open_cur"] if (np.isfinite(close) and f["open_cur"] > 0) else 1.0
            value = f["shares"] * f["px"] * ratio
            bps = _sell_bps(cm, close, value, adv.get(sym, float("nan")))
            proceeds = value * (1.0 - bps / 1e4)
            res[sym] = {"value": value, "cost_bps": bps, "proceeds": proceeds, "exit_close": close}
            tot += proceeds
            spent += f["cash_out"]
        rec["results"][s] = {"positions": res, "total_proceeds": tot, "cash_out": spent,
                             "basket_return": (tot / spent - 1.0) if spent > 0 else None}
    return rec
