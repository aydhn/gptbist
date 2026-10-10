"""Forward report: per portfolio / benchmark stats + overlap-aware significance. Simulation only; no real order sent."""
from __future__ import annotations

import json
import math
from statistics import NormalDist

import numpy as np
import pandas as pd

from bist_signal_bot.forward import NO_ORDER
from bist_signal_bot.forward.chain import HashChain
from bist_signal_bot.forward.config import (PRIMARY, ROLE_PLACEBO, SCENARIOS, TIER_CANDIDATE, TIER_WATCH, ForwardConfig,
                                            load_portfolios, portfolio_tier, utcnow_iso)


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


def _nav(cfg: ForwardConfig, pid: str):
    f = cfg.nav_dir / f"{pid}.csv"
    return pd.read_csv(f, index_col=0, parse_dates=True) if f.exists() else None


def vs_placebo(df: pd.DataFrame, plc: pd.DataFrame, lag: int) -> dict:
    """Cumulative excess of the portfolio over a placebo shadow (same dates) + NW t of the daily return difference."""
    a = df[f"nav_{PRIMARY}"]
    b = plc[f"nav_{PRIMARY}"].reindex(a.index).ffill()
    ok = b.notna()
    a, b = a[ok], b[ok]
    if len(a) < 4:
        return {"n": int(len(a)), "cum_excess": None, "t": float("nan")}
    d = (a.pct_change() - b.pct_change()).iloc[1:]
    return {"n": int(len(d)), "cum_excess": float(a.iloc[-1] / a.iloc[0] - b.iloc[-1] / b.iloc[0]),
            "t": nw_tstat(d, lag)["t"]}


def portfolio_stats(cfg: ForwardConfig, p: dict, K: int, exits: list, placebo_nav: pd.DataFrame = None) -> dict:
    f = cfg.nav_dir / f"{p['id']}.csv"
    tier = portfolio_tier(p)
    out = {"id": p["id"], "family": p["family"], "horizon": p["horizon"], "params": p["params"], "tier": tier,
           "role": p.get("role"), "v2_verdict": p.get("v2_verdict"), "v2_robust": p.get("v2_robust")}
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
    if tier in (TIER_CANDIDATE, TIER_WATCH):  # criterion 6 (watch: informational): must beat the same-horizon placebo shadow
        if placebo_nav is None:
            crit["beats_placebo"] = False
            out["vs_placebo"] = {"note": "no placebo portfolio frozen"}
        else:
            vp = vs_placebo(df, placebo_nav, lag)
            out["vs_placebo"] = vp
            mt = cfg.f("FORWARD_MIN_TSTAT", 2.0)
            crit["beats_placebo"] = bool(vp["cum_excess"] is not None and vp["cum_excess"] > 0 and vp["t"] >= mt)
    out["criteria"] = crit
    ok = "PASS" if all(crit.values()) else "FAIL"
    if tier == TIER_CANDIDATE:
        out["verdict"] = ok
    else:  # watch / controls are informational: they never carry a PASS/FAIL weight
        out["verdict"], out["informational_verdict"] = ("WATCH" if tier == TIER_WATCH else "CONTROL"), ok
        if p.get("role") == ROLE_PLACEBO:
            out["placebo_edge"] = bool(nw["t"] >= cfg.f("FORWARD_MIN_TSTAT", 2.0))
    return out


def build_report(cfg: ForwardConfig) -> dict:
    doc = load_portfolios(cfg)
    exits = list(HashChain(cfg.outcomes_path).iter_type("exit"))
    pfs = doc["portfolios"]
    K = max(1, sum(portfolio_tier(p) == TIER_CANDIDATE for p in pfs))  # Bonferroni over candidate-tier only
    plc = {p["horizon"]: _nav(cfg, p["id"]) for p in pfs if p.get("role") == ROLE_PLACEBO}
    anyplc = next((v for v in plc.values() if v is not None), None)
    rows = [portfolio_stats(cfg, p, K, exits, plc.get(p["horizon"]) if plc.get(p["horizon"]) is not None else anyplc)
            for p in pfs]
    cand = [r for r in rows if r["tier"] == TIER_CANDIDATE]
    plcr = [r for r in rows if r.get("role") == ROLE_PLACEBO]
    placebo_edge = any(r.get("placebo_edge") for r in plcr)
    n_pass = sum(r["verdict"] == "PASS" for r in cand)
    if n_pass and not placebo_edge and all(r.get("days_live") for r in plcr):
        overall = "SUCCESS"
    elif n_pass and placebo_edge:
        overall = "INCONCLUSIVE_PLACEBO_EDGE"
    elif not cand:
        overall = "NO_CANDIDATE"  # only watch/control/placebo tracked until an explicit new freeze version
    elif cand and all(r["verdict"] == "FAIL" for r in cand):
        overall = "FAIL"
    else:
        overall = "INSUFFICIENT"
    return {"generated_at": utcnow_iso(), "n_portfolios": doc["n_portfolios"], "n_candidates": len(cand), "n_watch": sum(r["tier"] == TIER_WATCH for r in rows),
            "freeze_version": doc.get("freeze_version"), "plan": cfg.plan(), "portfolios": rows,
            "n_pass": n_pass, "n_insufficient": sum(r["verdict"] == "INSUFFICIENT" for r in cand),
            "placebo_edge": placebo_edge, "overall": overall, "disclaimer": NO_ORDER,
            "note": "Shadow simulation; forward testing has no survivorship bias (real test)."}


def format_report(rep: dict) -> str:
    L = [f"FORWARD REPORT {rep['generated_at']}  portfolios={rep['n_portfolios']} candidates={rep['n_candidates']} "
         f"pass={rep['n_pass']} insufficient={rep['n_insufficient']} placebo_edge={rep['placebo_edge']} "
         f"OVERALL={rep['overall']}", f"rule: {rep['plan']['decision_rule']}"]
    for r in rep["portfolios"]:
        if not r.get("days_live"):
            L.append(f"- [{r['tier']}] {r['id']}: no data yet [{r['verdict']}]")
            continue
        sc, ex = r["scenarios"][PRIMARY], r["excess"]
        L.append(f"- [{r['tier']}/{r.get('role')} v2={r.get('v2_verdict')}] {r['id']}: days={r['days_live']} NAV={sc['nav']:.0f} ret={sc['total_return']:+.2%} "
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
