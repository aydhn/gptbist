"""Robustness layer stacked ON TOP of the CandidateGate (tightening only; no gate/GateConfig threshold is touched).

Why: a forensic audit of ``ml_xs_logit`` h=5 (gate Sharpe ~3) showed the 'edge' was one factor (limit-up tail
continuation) carried by a few hundred lottery events concentrated in 2024-26. The gate looks at the aggregate only;
this module asks whether the aggregate survives removing its best parts. All thresholds are config keys
(``EDGE_ROBUST_*`` in config/defaults.py) fixed a priori and NOT tuned to any result.

Input conventions
  * ``events``: DataFrame of per-event NET excess returns (columns ``net_ret``, ``gross_ret`` (excess, before cost),
    ``symbol``, ``t1``; optional ``order_value``). Cost = gross_ret - net_ret (NaN net = disallowed, dropped).
  * ``nav_excess``: daily NAV-level excess return series (strategy NAV minus exposure-matched EW) over the live window.
  * ``grid``: trading days of the evaluation window (gate-style sparse daily series: mean event return per exit day,
    zero on other days). Criteria (b)/(d) use this gate-consistent series (annualised Sharpe).

Criteria (gating unless marked informational; ALL must pass for ``robust``)
  a  trim_top_events      mean net excess > 0 after removing the top ``trim_event_frac`` (5%) events by excess return
  b  drop_top_symbols     after removing the ``drop_top_symbols`` (10) symbols with the largest total contribution,
                          excess Sharpe > 0 AND >= ``min_remaining_sharpe_frac`` (30%) of the original
                          (universes with < 2k event symbols use k = n_symbols // 2; reported as ``k_used``)
  c  year_stability       among calendar years with >= 60 live days: >= 60% have positive excess and no single year
                          carries > 60% of the total excess (total <= 0 or < 2 eligible years fails)
  d  cost_stress          excess Sharpe > 0 when trading costs are multiplied by ``cost_stress_mult`` (2x)
  e  event_cap            mean net excess > 0 after winsorising events at +``event_cap`` (20%)
  f  breadth_topk         INFORMATIONAL: a top-20 basket must not be negative (reported, not gating)
  g  global_dsr           GATING: global-multiplicity DSR (``global_multiplicity.global_dsr_robust``: same-suffix pool,
                          MAD-trimmed Sharpe dispersion, honest N) >= the gate's ``dsr_min``. Reported next to the
                          family DSR. If not supplied (pure-function use) it is 'not_evaluated' and not blocking, and
                          ``complete`` is False; the runner always supplies it and fails closed when unavailable.
Output: dict(criteria={name: {pass, ...values}}, failed=[names], robust=bool, complete=bool, config=...).
No real order is sent.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from pydantic import BaseModel

from bist_signal_bot.edge_validation import stats as st

ANN = 252.0
GATING = ("trim_top_events", "drop_top_symbols", "year_stability", "cost_stress", "event_cap", "global_dsr")
NAMES = ("trim_top_events", "drop_top_symbols", "year_stability", "cost_stress", "event_cap", "breadth_topk",
         "global_dsr")


class RobustnessConfig(BaseModel):
    trim_event_frac: float = 0.05
    drop_top_symbols: int = 10
    min_remaining_sharpe_frac: float = 0.30
    year_min_live_days: int = 60
    year_min_positive_frac: float = 0.60
    year_max_share: float = 0.60
    cost_stress_mult: float = 2.0
    event_cap: float = 0.20
    breadth_top_k: int = 20
    global_mad_k: float = 3.5

    @classmethod
    def from_settings(cls, settings=None) -> "RobustnessConfig":
        def g(key, default):
            try:
                v = getattr(settings, "EDGE_ROBUST_" + key)
                return default if v is None else v
            except AttributeError:
                return default
        d = cls()
        return cls(trim_event_frac=float(g("TRIM_EVENT_FRAC", d.trim_event_frac)),
                   drop_top_symbols=int(g("DROP_TOP_SYMBOLS", d.drop_top_symbols)),
                   min_remaining_sharpe_frac=float(g("MIN_REMAINING_SHARPE_FRAC", d.min_remaining_sharpe_frac)),
                   year_min_live_days=int(g("YEAR_MIN_LIVE_DAYS", d.year_min_live_days)),
                   year_min_positive_frac=float(g("YEAR_MIN_POSITIVE_FRAC", d.year_min_positive_frac)),
                   year_max_share=float(g("YEAR_MAX_SHARE", d.year_max_share)),
                   cost_stress_mult=float(g("COST_STRESS_MULT", d.cost_stress_mult)),
                   event_cap=float(g("EVENT_CAP", d.event_cap)),
                   breadth_top_k=int(g("BREADTH_TOP_K", d.breadth_top_k)),
                   global_mad_k=float(g("GLOBAL_MAD_K", d.global_mad_k)))


def _f(x) -> Optional[float]:
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _ann_sharpe_daily(ev: pd.DataFrame, col: str, grid: pd.DatetimeIndex) -> Optional[float]:
    """Annualised Sharpe of the gate-style daily series (mean event return per exit day, zero elsewhere)."""
    from bist_signal_bot.edge_validation.gate import daily_series
    if ev is None or len(ev) == 0 or len(grid) == 0:
        return None
    sr = st.sharpe(daily_series(ev, col, grid).to_numpy(float))
    return _f(sr * math.sqrt(ANN)) if np.isfinite(sr) else None


def _grid(events: pd.DataFrame, grid) -> pd.DatetimeIndex:
    from bist_signal_bot.edge_validation.gate import _day
    if grid is not None:
        return _day(grid)
    t1 = pd.DatetimeIndex(events["t1"])
    return _day(pd.bdate_range(t1.min().tz_localize(None) if t1.tz is not None else t1.min(),
                               t1.max().tz_localize(None) if t1.tz is not None else t1.max()))


def _crit(passed: Optional[bool], **vals) -> dict:
    return {"pass": None if passed is None else bool(passed), **{k: _f(v) if isinstance(v, (float, np.floating))
                                                                  else v for k, v in vals.items()}}


def robustness_report(events: pd.DataFrame, nav_excess: Optional[pd.Series], per_symbol: Optional[pd.Series] = None,
                      *, grid=None, cfg: Optional[RobustnessConfig] = None, global_dsr: Optional[dict] = None,
                      family_dsr: Optional[float] = None, breadth: Optional[dict] = None,
                      dsr_min: float = 0.95) -> dict:
    cfg = cfg or RobustnessConfig()
    ev = events if events is not None else pd.DataFrame(columns=["net_ret", "gross_ret", "symbol", "t1"])
    ev = ev.dropna(subset=["net_ret"]) if len(ev) else ev
    out: Dict[str, dict] = {}
    n = len(ev)
    if n == 0:
        for k in NAMES:
            out[k] = _crit(None if k in ("breadth_topk",) else False, note="no events")
        return {"criteria": out, "failed": list(GATING), "robust": False, "complete": False,
                "n_events": 0, "config": cfg.model_dump()}
    net = ev["net_ret"].to_numpy(float)
    days = _grid(ev, grid)
    base_sr = _ann_sharpe_daily(ev, "net_ret", days)

    # (a) trim the best events
    k_trim = int(math.ceil(cfg.trim_event_frac * n))
    keep = np.sort(net)[: n - k_trim]
    mean_a = float(keep.mean()) if len(keep) else float("nan")
    out["trim_top_events"] = _crit(bool(np.isfinite(mean_a) and mean_a > 0), mean_after_bps=mean_a * 1e4,
                                   mean_before_bps=float(net.mean()) * 1e4, n_removed=k_trim)

    # (b) drop the top-contributing symbols
    if per_symbol is None:
        w = ev["order_value"].to_numpy(float) if "order_value" in ev else np.ones(n)
        per_symbol = pd.Series(net * w, index=ev["symbol"].to_numpy()).groupby(level=0).sum()
    per_symbol = per_symbol.dropna().sort_values(ascending=False)
    k = int(cfg.drop_top_symbols)
    k_used = k if len(per_symbol) >= 2 * k else len(per_symbol) // 2
    if k_used >= 1 and base_sr is not None:
        drop = set(per_symbol.index[:k_used])
        rest = ev[~ev["symbol"].isin(drop)]
        sr_b = _ann_sharpe_daily(rest, "net_ret", days)
        ok_b = sr_b is not None and base_sr > 0 and sr_b > 0 and sr_b >= cfg.min_remaining_sharpe_frac * base_sr
        out["drop_top_symbols"] = _crit(ok_b, sharpe_before=base_sr, sharpe_after=sr_b, k_used=k_used,
                                        remaining_fraction=(None if sr_b is None or not base_sr else sr_b / base_sr),
                                        top_contributions=[[str(s), float(v)] for s, v in
                                                           per_symbol.head(k_used).items()][:10])
    else:
        out["drop_top_symbols"] = _crit(False, note="too few symbols / undefined Sharpe", k_used=k_used)

    # (c) calendar-year stability on the NAV-level excess series
    if nav_excess is not None and len(nav_excess.dropna()):
        r = nav_excess.dropna()
        yrs = r.groupby(r.index.year)
        live, tot = yrs.size(), yrs.sum()
        el = live[live >= cfg.year_min_live_days].index
        total = float(tot[el].sum()) if len(el) else float("nan")
        pos_frac = float((tot[el] > 0).mean()) if len(el) else float("nan")
        max_share = (float(tot[el].max() / total) if len(el) and total > 0 else float("nan"))
        ok_c = bool(len(el) >= 2 and total > 0 and pos_frac >= cfg.year_min_positive_frac
                    and max_share <= cfg.year_max_share)
        out["year_stability"] = _crit(ok_c, positive_fraction=pos_frac, max_year_share=max_share, total_excess=total,
                                      n_years=int(len(el)),
                                      by_year={str(y): [int(live[y]), float(tot[y])] for y in live.index})
    else:
        out["year_stability"] = _crit(False, note="no NAV excess series")

    # (d) cost stress: cost = gross - net, scaled
    if "gross_ret" in ev:
        stressed = ev.assign(stress_ret=ev["gross_ret"].to_numpy(float) -
                             cfg.cost_stress_mult * (ev["gross_ret"].to_numpy(float) - net))
        sr_d = _ann_sharpe_daily(stressed, "stress_ret", days)
        out["cost_stress"] = _crit(sr_d is not None and sr_d > 0, sharpe_stressed=sr_d, sharpe_base=base_sr,
                                   cost_mult=cfg.cost_stress_mult)
    else:
        out["cost_stress"] = _crit(False, note="no gross_ret column")

    # (e) winsorise at +cap
    mean_e = float(np.minimum(net, cfg.event_cap).mean())
    out["event_cap"] = _crit(mean_e > 0, mean_capped_bps=mean_e * 1e4, cap=cfg.event_cap,
                             n_capped=int((net > cfg.event_cap).sum()))

    # (f) breadth (informational)
    if breadth:
        mb = breadth.get("mean_net_bps")
        out["breadth_topk"] = _crit(None if mb is None else mb >= 0, informational=True, **breadth)
    else:
        out["breadth_topk"] = _crit(None, informational=True, note="not evaluated")

    # (g) global multiplicity DSR (gating)
    if global_dsr is None:
        out["global_dsr"] = _crit(None, note="not_evaluated")
    else:
        dg = global_dsr.get("dsr_global")
        out["global_dsr"] = _crit(dg is not None and dg >= dsr_min, dsr_global=dg,
                                  dsr_family=family_dsr if family_dsr is not None else global_dsr.get("dsr_family"),
                                  n_global=global_dsr.get("n_global"), n_family=global_dsr.get("n_family"),
                                  dsr_min=dsr_min, variance_raw=global_dsr.get("variance_raw"),
                                  variance_trimmed=global_dsr.get("variance_trimmed"))
    failed: List[str] = [k for k in GATING if out[k]["pass"] is False]
    complete = all(out[k]["pass"] is not None for k in GATING)
    return {"criteria": out, "failed": failed, "robust": not failed, "complete": complete, "n_events": n,
            "config": cfg.model_dump()}
