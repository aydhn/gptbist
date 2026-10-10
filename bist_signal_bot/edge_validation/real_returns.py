"""Real (CPI-adjusted) return report vs CPI, XU100, deposit/cash and USDTRY. Research only; no real order sent.

Only measured evidence is reported. CPI is never assumed: with no CPI series the real fields are None and a
warning is emitted; where CPI coverage ends (e.g. the FRED/OECD series stops 2025-04) the evaluation window is
TRUNCATED to the covered span, never extrapolated.

CPI modes (``price_level``):
  * ``interpolate`` (default, ex-post measurement): monthly index anchored at month start, log-linear daily
    interpolation. Uses the next month's print for days inside a month, so it is a MEASUREMENT deflator, not
    something a trader could know in real time.
  * ``causal``: step function; the index of month M becomes known at the start of month M+1+lag_months
    (``lag_months`` = publication lag, default 1). Use it to check that conclusions survive a publication lag.
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.cash_benchmark import daily_cash_returns

logger = logging.getLogger(__name__)
NO_ORDER = "No real order sent."
SURVIVORSHIP_NOTE = ("Survivorship bias: the archive holds currently listed names only, so all stock results are "
                     "OPTIMISTIC (delisted losers are absent).")
STOPAJ_NOTE = ("Deposit/cash comparator is shown gross and after withholding tax (stopaj) on interest; the stopaj "
               "rate (REAL_REPORT_DEPOSIT_WITHHOLDING) is an unverified placeholder.")


def _get(settings, key, default):
    try:
        v = getattr(settings, key, default)
    except Exception:
        return default
    return default if v is None else v


def price_level(cpi: pd.Series, index, mode: str = "interpolate", lag_months: int = 1) -> pd.Series:
    """Daily CPI level on ``index``; NaN outside coverage (no extrapolation)."""
    if mode not in ("interpolate", "causal"):
        raise ValueError("mode must be 'interpolate' or 'causal'")
    if cpi is None or len(cpi) == 0:
        raise ValueError("price_level requires a CPI series (refusing to assume)")
    idx = pd.DatetimeIndex(index).normalize()
    c = pd.Series(cpi).astype(float).sort_index()
    c.index = pd.DatetimeIndex(c.index).to_period("M").to_timestamp()
    c = c[~c.index.duplicated(keep="last")]
    if mode == "interpolate":
        x = c.index.values.astype("datetime64[D]").astype(float)
        xi = idx.values.astype("datetime64[D]").astype(float)
        y = np.interp(xi, x, np.log(c.to_numpy()))
        out = np.exp(y)
        out[(xi < x[0]) | (xi > x[-1])] = np.nan
        return pd.Series(out, index=pd.DatetimeIndex(index), name="cpi_level")
    avail = c.index + pd.DateOffset(months=1 + int(lag_months))
    s = pd.Series(c.to_numpy(), index=avail)
    out = s.reindex(s.index.union(idx)).ffill().reindex(idx)
    return pd.Series(out.to_numpy(), index=pd.DatetimeIndex(index), name="cpi_level")


def _cagr(total: float, years: float) -> float:
    if years <= 0 or total <= -1.0:
        return float("nan")
    return float((1.0 + total) ** (1.0 / years) - 1.0)


def _max_dd(r: pd.Series) -> float:
    nav = (1.0 + r).cumprod()
    return float((nav / nav.cummax() - 1.0).min()) if len(nav) else float("nan")


def _years(idx) -> float:
    return (idx[-1] - idx[0]).days / 365.25


def _window_cagr(r: pd.Series) -> float:
    """CAGR of returns r[1:] measured from the close of r.index[0] to the close of r.index[-1]."""
    if len(r) < 3:
        return float("nan")
    return _cagr(float((1.0 + r.iloc[1:]).prod() - 1.0), _years(r.index))


def real_cagr(nominal_returns: pd.Series, cpi: pd.Series, mode: str = "interpolate", lag_months: int = 1) -> Dict[str, Any]:
    """Nominal/real CAGR over the part of ``nominal_returns`` covered by CPI (truncated, never extrapolated)."""
    r = pd.Series(nominal_returns).astype(float).dropna()
    if len(r) < 3:
        raise ValueError("need >= 3 return observations")
    p = price_level(cpi, r.index, mode, lag_months)
    ok = p.notna()
    if ok.sum() < 3:
        raise ValueError("CPI does not overlap the return window")
    r, p = r[ok], p[ok]
    yrs = _years(r.index)
    nom_total = float((1.0 + r.iloc[1:]).prod() - 1.0)
    infl_total = float(p.iloc[-1] / p.iloc[0] - 1.0)
    real_total = (1.0 + nom_total) / (1.0 + infl_total) - 1.0
    return {"start": r.index[0], "end": r.index[-1], "years": yrs, "nominal_cagr": _cagr(nom_total, yrs),
            "inflation_cagr": _cagr(infl_total, yrs), "real_cagr": _cagr(real_total, yrs),
            "nominal_total": nom_total, "real_total": real_total, "cpi_mode": mode}


def _rolling12(r: pd.Series, p: Optional[pd.Series], target: float, win: int = 252) -> Dict[str, Any]:
    nav = (1.0 + r).cumprod()
    if len(nav) <= win:
        return {"n": 0}
    nom = (nav / nav.shift(win) - 1.0).dropna()
    d: Dict[str, Any] = {"n": int(len(nom)), "worst_nominal": float(nom.min()), "median_nominal": float(nom.median()),
                         "pct_nominal_ge_target": float((nom >= target).mean())}
    if p is not None:
        real = ((1.0 + nom) / (p / p.shift(win)).reindex(nom.index) - 1.0).dropna()
        if len(real):
            d.update({"worst_real": float(real.min()), "median_real": float(real.median()),
                      "p10_real": float(real.quantile(0.10)), "p90_real": float(real.quantile(0.90)),
                      "pct_real_ge_target": float((real >= target).mean())})
    return d


def build_real_report(returns: pd.Series, ctx, cpi: Optional[pd.Series] = None, *, label: str = "strategy",
                      settings=None, cpi_mode: str = "interpolate", lag_months: Optional[int] = None,
                      exposure: Optional[pd.Series] = None) -> Dict[str, Any]:
    """RealReturnReport (dict). ``ctx`` is a DailyContext (benchmark XU100, usdtry, cash_rate)."""
    if settings is None:
        from bist_signal_bot.config.settings import get_settings
        settings = get_settings()
    target = float(_get(settings, "REAL_REPORT_TARGET_REAL_CAGR", 0.75))
    stopaj = float(_get(settings, "REAL_REPORT_DEPOSIT_WITHHOLDING", 0.15))
    lag = int(_get(settings, "REAL_REPORT_CPI_LAG_MONTHS", 1)) if lag_months is None else int(lag_months)
    r = pd.Series(returns).astype(float).dropna()
    warns = []
    p = None
    if cpi is None or len(cpi) == 0:
        warns.append("CPI MISSING: real CAGR not computed (no assumed inflation).")
    else:
        p = price_level(cpi, r.index, cpi_mode, lag)
        ok = p.notna()
        if ok.sum() < 3:
            warns.append("CPI does not overlap the return window: real CAGR not computed.")
            p = None
        elif (~ok).any():
            warns.append(f"CPI covers only {r.index[ok][0].date()}..{r.index[ok][-1].date()}; "
                         f"{int((~ok).sum())} sessions outside coverage excluded (no extrapolation).")
            r, p = r[ok], p[ok]
    if len(r) < 3:
        raise ValueError("need >= 3 return observations in the evaluation window")
    idx = r.index
    yrs = _years(idx)
    nom_cagr = _window_cagr(r)
    rep: Dict[str, Any] = {"label": label, "window": [str(idx[0].date()), str(idx[-1].date())], "n_sessions": int(len(r)),
                           "years": float(yrs), "nominal_cagr": nom_cagr, "max_drawdown": _max_dd(r),
                           "target_real_cagr": target, "cpi_mode": cpi_mode if p is not None else None,
                           "cpi_lag_months": lag if cpi_mode == "causal" else 0, "warnings": warns}
    if exposure is not None:
        e = exposure.reindex(idx).dropna()
        rep["avg_exposure"] = float(e.mean()) if len(e) else None
    comp: Dict[str, Any] = {}

    def add(name, ser):
        s = pd.Series(ser).reindex(idx).fillna(0.0)
        cg = _window_cagr(s)
        comp[name] = {"cagr": cg, "excess_cagr": nom_cagr - cg}

    if ctx.benchmark is not None:
        add("xu100", ctx.benchmark.pct_change(fill_method=None))
    else:
        warns.append("XU100 missing in context: no index comparison.")
    add("cash_gross", daily_cash_returns(idx, ctx.cash_rate, 0.0))
    add("deposit_net_stopaj", daily_cash_returns(idx, ctx.cash_rate, stopaj))
    comp["deposit_net_stopaj"]["withholding"] = stopaj
    if ctx.usdtry is not None:
        fx = ctx.usdtry.pct_change(fill_method=None).reindex(idx).fillna(0.0)
        add("usdtry", fx)
        usd_r = (1.0 + r) / (1.0 + fx) - 1.0
        rep["usd_cagr"] = _window_cagr(usd_r)
        rep["usd_max_drawdown"] = _max_dd(usd_r)
    else:
        warns.append("USDTRY missing in context: no USD view.")
    rep["comparators"] = comp
    if p is not None:
        infl = float(p.iloc[-1] / p.iloc[0] - 1.0)
        rep["inflation_cagr"] = _cagr(infl, yrs)
        real_total = (1.0 + float((1.0 + r.iloc[1:]).prod() - 1.0)) / (1.0 + infl) - 1.0
        rep["real_cagr"] = _cagr(real_total, yrs)
        rep["excess_vs_cpi"] = rep["real_cagr"]
        rep["target_reached"] = bool(rep["real_cagr"] >= target)
    else:
        rep["real_cagr"] = rep["inflation_cagr"] = rep["excess_vs_cpi"] = rep["target_reached"] = None
    rep["rolling_12m"] = _rolling12(r, p, target)
    rep["worst_12m_nominal"] = rep["rolling_12m"].get("worst_nominal")
    rep["worst_12m_real"] = rep["rolling_12m"].get("worst_real")
    rep["pct_12m_real_ge_target"] = rep["rolling_12m"].get("pct_real_ge_target")
    if rep["real_cagr"] is None:
        rep["target_statement"] = f"Target real CAGR >= {target:.0%}: CANNOT BE EVALUATED (no CPI)."
    elif rep["target_reached"]:
        rep["target_statement"] = (f"Target real CAGR >= {target:.0%} reached in-sample ({rep['real_cagr']:.1%}); "
                                   "optimistic (survivorship, in-sample).")
    else:
        rep["target_statement"] = f"Target real CAGR >= {target:.0%} NOT REACHED, best measured {rep['real_cagr']:.1%}."
    from bist_signal_bot.edge_validation.survivorship import HONESTY_STATEMENT, count_young_symbols
    rep["survivorship"] = {"statement": HONESTY_STATEMENT, "measurable": False,
                           "n_symbols_lt_2y_history": count_young_symbols(ctx)}
    warns.extend([SURVIVORSHIP_NOTE, HONESTY_STATEMENT, STOPAJ_NOTE])
    rep["no_real_order"] = NO_ORDER
    return rep


def report_for_nav(nav_returns, ctx, *, cpi: Optional[pd.Series] = None, regime_scale: Optional[pd.Series] = None,
                   overlay: bool = True, overlay_cfg=None, settings=None, cpi_mode: str = "interpolate",
                   load_cpi_if_missing: bool = True, start=None) -> Dict[str, Any]:
    """Report for a NAV-return stream (DataFrame with 'ret' from xsection.nav_returns, or a Series), with and
    without the exposure overlay. No ledger writes; CPI is loaded via daily.macro unless given."""
    from bist_signal_bot.risk.daily_overlay import OverlayConfig, apply_overlay
    if settings is None:
        from bist_signal_bot.config.settings import get_settings
        settings = get_settings()
    r = nav_returns["ret"] if isinstance(nav_returns, pd.DataFrame) else pd.Series(nav_returns)
    r = r.astype(float)
    if start is not None:
        r = r[r.index >= pd.Timestamp(start)]
    cpi_src = "given" if cpi is not None else None
    top_warn = []
    if cpi is None and load_cpi_if_missing:
        from bist_signal_bot.daily.macro import CPIUnavailable, load_cpi
        try:
            cpi, cpi_src = load_cpi(settings)
        except CPIUnavailable as exc:
            logger.error("CPI unavailable: %s", exc)
            top_warn.append(f"CPI unavailable: {exc}")
    out: Dict[str, Any] = {"cpi_source": cpi_src, "warnings": top_warn,
                           "base": build_real_report(r, ctx, cpi, label="no_overlay", settings=settings,
                                                     cpi_mode=cpi_mode)}
    if overlay:
        cfg = overlay_cfg or OverlayConfig.from_settings(settings)
        res = apply_overlay(r, regime_scale, ctx.cash_ret, cfg)
        out["overlay"] = build_real_report(res.returns, ctx, cpi, label="with_overlay", settings=settings,
                                           cpi_mode=cpi_mode, exposure=res.exposure)
        out["overlay_summary"] = {"avg_exposure": float(res.exposure.mean()),
                                  "n_halts": sum(1 for e in res.events if e["kind"] == "halt"),
                                  "n_reentries": sum(1 for e in res.events if e["kind"] == "reenter"),
                                  "pct_days_flat": float((res.exposure < 1e-9).mean()),
                                  "max_dd_cfg": cfg.max_dd, "warnings": res.warnings}
    return out
