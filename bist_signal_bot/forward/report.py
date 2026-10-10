"""Forward report: per portfolio / benchmark stats + overlap-aware significance. Simulation only; no real order sent."""
from __future__ import annotations

import json
import math
from statistics import NormalDist

import numpy as np
import pandas as pd

from bist_signal_bot.forward import NO_ORDER
from bist_signal_bot.forward.chain import HashChain
from bist_signal_bot.forward.config import PRIMARY, SCENARIOS, ForwardConfig, load_portfolios, utcnow_iso


def nw_tstat(x, lag: int) -> dict:
    """t-stat of the mean with Newey-West (Bartlett) variance; lag >= holding horizon covers basket overlap."""
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 3:
        return {"n": n, "mean": float("nan"), "t": float("nan"), "lag": lag}
    m = x.mean()
    xm = x - m
    L = min(int(lag), n - 1)
    v = float(xm @ xm) / n
    for k in range(1, L + 1):
        v += 2.0 * (1.0 - k / (L + 1.0)) * float(xm[k:] @ xm[:-k]) / n
    t = m / math.sqrt(v / n) if v > 0 else float("nan")
    return {"n": n, "mean": float(m), "t": float(t), "lag": L}


def _maxdd(nav: pd.Series) -> float:
    return float((1.0 - nav / nav.cummax()).max()) if len(nav) else 0.0


def crit_z(k: int, alpha: float = 0.05) -> float:
    return NormalDist().inv_cdf(1.0 - alpha / max(1, k))


def portfolio_stats(cfg: ForwardConfig, p: dict, K: int, exits: list) -> dict:
    f = cfg.nav_dir / f"{p['id']}.csv"
    out = {"id": p["id"], "family": p["family"], "horizon": p["horizon"], "params": p["params"]}
    if not f.exists():
        return {**out, "days_live": 0, "verdict": "INSUFFICIENT", "reason": "no NAV yet"}
    df = pd.read_csv(f, index_col=0, parse_dates=True)
    days = len(df) - 1
    out.update(days_live=days, first_date=str(df.index[0].date()), last_date=str(df.index[-1].date()),
               calendar_days=int((df.index[-1] - df.index[0]).days))
    r = df.pct_change().fillna(0.0)
    res = {}
    for s in SCENARIOS:
        nav = df[f"nav_{s}"]
        res[s] = {"nav": float(nav.iloc[-1]), "total_return": float(nav.iloc[-1] / nav.iloc[0] - 1),
                  "max_drawdown": _maxdd(nav)}
    out["scenarios"] = res
    bm = {}
    for b in ("ew_nav", "xu100_nav", "cash_nav"):
        if b in df:
            bm[b] = {"nav": float(df[b].iloc[-1]), "total_return": float(df[b].iloc[-1] / df[b].iloc[0] - 1)}
    out["benchmarks"] = bm
    pr = r[f"nav_{PRIMARY}"]
    exc = {}
    for b in ("ew_nav", "xu100_nav", "cash_nav"):
        if b in df:
            ex = (pr - r[b]).iloc[1:]
            exc[b] = {"cum_excess": float(df[f"nav_{PRIMARY}"].iloc[-1] / df[f"nav_{PRIMARY}"].iloc[0]
                                          - df[b].iloc[-1] / df[b].iloc[0]),
                      "mean_daily": float(ex.mean()) if len(ex) else None,
                      "hit_rate_days": float((ex > 0).mean()) if len(ex) else None,
                      "roll20_sum": float(ex.tail(20).sum()), "roll60_sum": float(ex.tail(60).sum())}
    out["excess"] = exc
    lag = max(int(p["horizon"]), int(4 * (max(days, 1) / 100) ** (2 / 9)))
    nw = nw_tstat((pr - r["ew_nav"]).iloc[1:], lag) if "ew_nav" in r else {"t": float("nan"), "n": 0}
    out["nw_excess_vs_ew"] = nw
    # basket-level hit rate vs EW (closed baskets of this portfolio)
    wins, nb = 0, 0
    for e in exits:
        if e["portfolio_id"] != p["id"]:
            continue
        try:
            a = df.index[df.index < pd.Timestamp(e["entry_date"])][-1]
            b = pd.Timestamp(e["exit_date"])
            pf = df.loc[b, f"nav_{PRIMARY}"] / df.loc[a, f"nav_{PRIMARY}"]
            ew = df.loc[b, "ew_nav"] / df.loc[a, "ew_nav"]
        except (IndexError, KeyError):
            continue
        nb += 1
        wins += int(pf > ew)
    out["baskets_closed"], out["basket_hit_rate_vs_ew"] = nb, (wins / nb if nb else None)
    # verdict (rule fixed in advance; see docs/runbooks/forward_paper_plan.md)
    min_d, min_c = cfg.i("FORWARD_MIN_LIVE_DAYS", 60), cfg.i("FORWARD_MIN_CALENDAR_DAYS", 90)
    tcrit = max(cfg.f("FORWARD_MIN_TSTAT", 2.0), crit_z(K))
    out["t_critical"] = tcrit
    if days < min_d or out["calendar_days"] < min_c:
        out.update(verdict="INSUFFICIENT", reason=f"need >= {min_d} live days and >= {min_c} calendar days "
                                                   f"(have {days} / {out['calendar_days']})")
        return out
    crit = {"cum_excess_ew>0": exc["ew_nav"]["cum_excess"] > 0,
            "alpha_vs_cash>0": exc["cash_nav"]["cum_excess"] > 0,
            f"nw_t>={tcrit:.2f}": bool(nw["t"] >= tcrit),
            "baskets>=min_and_hit>=50%": nb >= cfg.i("FORWARD_MIN_BASKETS", 6) and (wins / max(nb, 1)) >= 0.5,
            "maxdd<limit": res[PRIMARY]["max_drawdown"] < cfg.f("FORWARD_MAX_DD_PASS", 0.20)}
    out["criteria"] = crit
    out["verdict"] = "PASS" if all(crit.values()) else "FAIL"
    return out


def build_report(cfg: ForwardConfig) -> dict:
    doc = load_portfolios(cfg)
    exits = list(HashChain(cfg.outcomes_path).iter_type("exit"))
    K = doc["n_portfolios"]
    rows = [portfolio_stats(cfg, p, K, exits) for p in doc["portfolios"]]
    return {"generated_at": utcnow_iso(), "n_portfolios": K, "plan": cfg.plan(), "portfolios": rows,
            "n_pass": sum(r["verdict"] == "PASS" for r in rows),
            "n_insufficient": sum(r["verdict"] == "INSUFFICIENT" for r in rows),
            "disclaimer": NO_ORDER, "note": "Shadow simulation; survivorship-free forward evidence only."}


def format_report(rep: dict) -> str:
    L = [f"FORWARD REPORT {rep['generated_at']}  portfolios={rep['n_portfolios']} pass={rep['n_pass']} "
         f"insufficient={rep['n_insufficient']}", f"rule: {rep['plan']['decision_rule']}"]
    for r in rep["portfolios"]:
        if not r.get("days_live"):
            L.append(f"- {r['id']}: no data yet [{r['verdict']}]")
            continue
        sc, ex = r["scenarios"][PRIMARY], r["excess"]
        L.append(f"- {r['id']}: days={r['days_live']} NAV={sc['nav']:.0f} ret={sc['total_return']:+.2%} "
                 f"dd={sc['max_drawdown']:.1%} exEW={ex['ew_nav']['cum_excess']:+.2%} "
                 f"exXU100={ex['xu100_nav']['cum_excess']:+.2%}" if "xu100_nav" in ex else f"- {r['id']}")
        L.append(f"    exCash={ex['cash_nav']['cum_excess']:+.2%} hit={ex['ew_nav']['hit_rate_days']:.0%} "
                 f"NW t={r['nw_excess_vs_ew']['t']:.2f} baskets={r['baskets_closed']} [{r['verdict']}] "
                 f"{r.get('reason', '')}")
    L.append(NO_ORDER)
    return "\n".join(L)


def save_report(cfg: ForwardConfig, rep: dict):
    cfg.reports_dir.mkdir(parents=True, exist_ok=True)
    day = rep["generated_at"][:10].replace("-", "")
    p = cfg.reports_dir / f"report_{day}.json"
    p.write_text(json.dumps(rep, indent=2, sort_keys=True, default=str), encoding="utf-8")
    return p
