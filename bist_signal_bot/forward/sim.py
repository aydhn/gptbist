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

from bist_signal_bot.edge_validation.fills_daily import get_fills
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

    v2 semantics (same ``fills_daily`` rules as the research layer, via ``DailyContext.semantics``):
    * an entry that is unfillable at the next open (zero volume, open at/above limit-up, H==L lock) is NOT bought and the
      slot stays in cash;
    * a symbol whose nominal exit close is locked limit-down (or NaN) is sold at the first later unlocked close; the
      basket exit record is written once every symbol is sold (positions keep being marked to market meanwhile).
    nav_df index = sessions from the first decision date; columns nav_<scenario>, ew_nav, xu100_nav, cash_nav.
    """
    blocked = blocked or set()
    if not decisions:
        return None, []
    sess = ctx.index
    pos = {pd.Timestamp(d): i for i, d in enumerate(sess)}
    n = len(sess)
    col = {s: j for j, s in enumerate(ctx.symbols)}
    fl = get_fills(ctx)
    OP, CL = ctx.open.to_numpy(float), ctx.close.ffill().to_numpy(float)
    RAW = ctx.close.to_numpy(float)
    good = np.isfinite(RAW)
    pick = good & ~fl.locked_down if ctx.semantics.exit_lock_defer else good
    cash_ret = ctx.cash_ret.to_numpy(float)
    ent_at = defaultdict(list)
    first = None
    for d in decisions:
        i = pos.get(pd.Timestamp(d["as_of"]))
        if i is None:
            continue
        first = i if first is None else min(first, i)
        if i + 1 < n:
            ent_at[i + 1].append((d, i))
    if first is None:
        return None, []
    cash = {s: float(capital) for s in SCENARIOS}
    held = {s: {} for s in SCENARIOS}  # decision hash -> {sym: dict}
    active: dict = {}                  # hash -> (decision, nominal exit row) not yet closed
    done: dict = defaultdict(lambda: {s: {} for s in SCENARIOS})  # per-symbol realised exits of open baskets
    new: list = []
    nav = {s: np.full(n, np.nan) for s in SCENARIOS}
    for s in SCENARIOS:
        nav[s][first] = cash[s]

    def exit_row(h, sym, j, x, rec_exit):
        """Row at which ``sym`` of basket ``h`` is sold (None = not yet resolvable)."""
        if rec_exit is not None:
            ed = None
            for s in SCENARIOS:
                ed = ((rec_exit["results"].get(s) or {}).get("positions", {}).get(sym) or {}).get("exit_date")
                if ed:
                    break
            ed = ed or rec_exit.get("exit_date")
            return pos.get(pd.Timestamp(ed)) if ed else None
        if x >= n:
            return None
        y = int(fl.exit_next[x, j])
        return y if (y >= 0 and pick[y, j]) else None

    for t in range(first + 1, n):
        for d, i in ent_at.get(t, []):
            rec = entries.get(d["hash"])
            if rec is None:
                rec = _compute_entry(d, t, ctx, OP, col, cash, cost_models, blocked, fl)
                new.append(("entry", rec))
                entries[d["hash"]] = rec
            x = i + int(d["horizon"])
            rec_exit = exits.get(d["hash"])
            for s in SCENARIOS:
                fills = (rec["fills"].get(s) or {})
                cash[s] -= sum(f["cash_out"] for f in fills.values())
                held[s][d["hash"]] = {
                    sym: dict(f, open_cur=float(OP[t, col[sym]]), x_nom=x,
                              x_row=exit_row(d["hash"], sym, col[sym], x, rec_exit)) for sym, f in fills.items()}
            active[d["hash"]] = (d, x)
        for s in SCENARIOS:
            cash[s] *= 1.0 + (cash_ret[t] if np.isfinite(cash_ret[t]) else 0.0)
        for h, (d, x) in list(active.items()):
            rec_exit = exits.get(h)
            adv = {p["symbol"]: float(p["adv"]) for p in d["picks"]}
            for s in SCENARIOS:
                for sym, f in list((held[s].get(h) or {}).items()):
                    if f["x_row"] != t:
                        continue
                    j = col[sym]
                    if rec_exit is not None:
                        r = ((rec_exit["results"].get(s) or {}).get("positions") or {}).get(sym) or {}
                        proceeds = float(r.get("proceeds", 0.0))
                        res = r
                    else:
                        close = float(RAW[t, j])
                        ratio = close / f["open_cur"] if (np.isfinite(close) and f["open_cur"] > 0) else 1.0
                        value = f["shares"] * f["px"] * ratio
                        bps = _sell_bps(cost_models[s], close, value, adv.get(sym, float("nan")))
                        proceeds = value * (1.0 - bps / 1e4)
                        res = {"value": value, "cost_bps": bps, "proceeds": proceeds, "exit_close": close,
                               "exit_date": str(pd.Timestamp(sess[t]).date()), "deferred_sessions": int(t - x),
                               "shares": f["shares"], "cash_out": f["cash_out"]}
                    cash[s] += proceeds
                    done[h][s][sym] = res
                    held[s][h].pop(sym)
            if t >= x and all(not held[s].get(h) for s in SCENARIOS):
                if rec_exit is None:
                    rec_exit = {"portfolio_id": d["portfolio_id"], "decision_hash": h, "as_of": d["as_of"],
                                "entry_date": entries[h]["entry_date"], "exit_date": str(pd.Timestamp(sess[t]).date()),
                                "results": {}}
                    for s in SCENARIOS:
                        pr = done[h][s]
                        tot = sum(v["proceeds"] for v in pr.values())
                        spent = sum(v["cash_out"] for v in pr.values())
                        rec_exit["results"][s] = {"positions": pr, "total_proceeds": tot, "cash_out": spent,
                                                  "basket_return": (tot / spent - 1.0) if spent > 0 else None}
                    new.append(("exit", rec_exit))
                    exits[h] = rec_exit
                active.pop(h)
                done.pop(h, None)
        for s in SCENARIOS:
            mv = 0.0
            for hb in held[s].values():
                for sym, f in hb.items():
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


def _compute_entry(d, t, ctx, OP, col, cash, cost_models, blocked, fills) -> dict:
    rec = {"portfolio_id": d["portfolio_id"], "decision_hash": d["hash"], "as_of": d["as_of"],
           "entry_date": str(pd.Timestamp(ctx.index[t]).date()), "blocked": d["hash"] in blocked,
           "semantics": "v2_fills", "fills": {s: {} for s in SCENARIOS}, "dropped": {s: [] for s in SCENARIOS}}
    if rec["blocked"]:
        return rec
    top_n = int(d["top_n"])
    flag_policy = ctx.semantics.entry_policy == "flag"
    for s in SCENARIOS:
        slot = cash[s] / top_n
        cm = cost_models[s]
        for p in d["picks"]:
            j = col.get(p["symbol"])
            px = float(OP[t, j]) if j is not None else float("nan")
            if j is None or not bool(fills.base_ok[t, j]) or not (np.isfinite(px) and px > 0):
                rec["dropped"][s].append([p["symbol"], "no_open_or_no_volume"])
                continue
            at_limit = not bool(fills.entry_ok[t, j])  # open at/above limit-up or H==L lock
            if at_limit and not flag_policy:
                rec["dropped"][s].append([p["symbol"], "unfillable_entry_price_limit"])  # slot stays in cash
                continue
            bps = cm.cost_bps(px, slot, float(p["adv"]), "buy", at_limit)  # flag policy -> NaN (disallowed)
            if not np.isfinite(bps):
                rec["dropped"][s].append([p["symbol"], "price_limit_flag" if at_limit else "cost_model_disallowed"])
                continue
            c = bps / 1e4
            shares = int(math.floor(slot / (px * (1.0 + c))))
            if shares < 1:
                rec["dropped"][s].append([p["symbol"], "lot_too_small"])
                continue
            rec["fills"][s][p["symbol"]] = {"shares": shares, "px": px, "cost_bps": float(bps),
                                           "cash_out": shares * px * (1.0 + c)}
    return rec
