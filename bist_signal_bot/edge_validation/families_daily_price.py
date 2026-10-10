"""Price/volume-only daily cross-sectional score families (momentum, reversal, risk anomalies, volume shock).

Research only; no real order is ever sent. Every score at row t uses data <= t (verified by
``check_score_causality`` in tests). Higher score = better (long-only). Rows/cells with insufficient history are
NaN (never filled). Grids are deliberately small: every (params, horizon) combination is a ledger trial and raises
the multiple-testing bar (DSR/PBO/BH).

Self-registers on import (``families_daily`` imports this module).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.families_daily import register_family
from bist_signal_bot.edge_validation.xsection import DailyContext


def _rets(ctx: DailyContext) -> pd.DataFrame:
    return ctx.close.pct_change(fill_method=None)


def _bench_rets(ctx: DailyContext):
    return None if ctx.benchmark is None else ctx.benchmark.pct_change(fill_method=None)


def _nan(ctx: DailyContext) -> pd.DataFrame:
    return pd.DataFrame(np.nan, index=ctx.index, columns=ctx.symbols)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    return df.replace([np.inf, -np.inf], np.nan)


def _rolling_beta_cov(ctx: DailyContext, w: int):
    """(beta, cov_im, var_m) of daily returns vs XU100 over the last ``w`` sessions ending at t."""
    rm = _bench_rets(ctx)
    r = _rets(ctx)
    cov = r.rolling(w, min_periods=w).cov(rm)
    var = rm.rolling(w, min_periods=w).var()
    beta = cov.div(var.where(var > 0), axis=0)
    return beta, cov, var


class _Mom:
    """Shared momentum implementation: return over [t-lookback, t-skip], optionally divided by trailing vol."""
    name = ""
    default_grid: dict = {}

    def valid(self, params: dict) -> bool:
        return 0 <= params.get("skip", 0) < params.get("lookback", 1)

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        lb, sk = int(params["lookback"]), int(params["skip"])
        if not self.valid({"lookback": lb, "skip": sk}):
            raise ValueError("need 0 <= skip < lookback")
        c = ctx.close
        s = c.shift(sk) / c.shift(lb) - 1.0
        if int(params.get("vol_scaled", 0)):
            vw = int(params.get("vol_window", 60))
            s = s / _rets(ctx).rolling(vw, min_periods=vw).std().where(lambda v: v > 0)
        return _clean(s)


class XSMomentum121(_Mom):
    """12-1 momentum: cumulative return t-250..t-21 (skip the most recent month).

    Hypothesis: investors under-react to information, so past winners keep winning over 3-12 months; the last month
    is skipped because of short-term reversal / microstructure noise. Jegadeesh & Titman (1993, J. Finance);
    Carhart (1997); Asness-Moskowitz-Pedersen (2013) for the vol-scaled/risk-adjusted variant. Grid: lookback around
    250, skip 21, vol_scaled in {0,1} (divide by 60d daily-return std) -> 6 combos.
    """
    name = "xs_momentum_12_1"
    default_grid = {"lookback": [250, 200, 150], "skip": [21], "vol_scaled": [0, 1]}


class XSMomentum16(_Mom):
    """Intermediate momentum: return over t-126..t-5 (skip one week).

    Hypothesis: same under-reaction story at a 6-month horizon with a shorter skip (a week) to still avoid the
    1-week reversal. Jegadeesh & Titman (1993) 6-month formation; Moskowitz-Ooi-Pedersen (2012). Grid: lookback
    around 126, skip 5, vol_scaled in {0,1} -> 6 combos.
    """
    name = "xs_momentum_1_6"
    default_grid = {"lookback": [126, 100, 60], "skip": [5], "vol_scaled": [0, 1]}


class XSReversal:
    """Short-term reversal: score = -(return over the last l days).

    Hypothesis: liquidity-provision / overreaction; last week's losers rebound (Jegadeesh 1990; Lehmann 1990; Avramov,
    Chordia & Goyal 2006: profits concentrate in illiquid, high-turnover names and mostly vanish after costs). Hence
    ``min_adv_try`` (stricter than the universe ADV floor: 2e7 / 5e7 TRY) restricts to names that can actually be
    traded. Optional ``mkt_stop`` (default 0 = off): when XU100's 20-day return < -mkt_stop all scores are NaN, i.e.
    the rebalance is skipped and the slot stays in cash (reversal is weakest/riskiest in market-wide selloffs).
    Grid: l in {1,2,3,5} x min_adv_try in {2e7, 5e7} -> 8 combos (mkt_stop not in grid; set it explicitly).
    """
    name = "xs_reversal"
    default_grid = {"l": [1, 2, 3, 5], "min_adv_try": [2e7, 5e7], "mkt_stop": [0.0]}

    def valid(self, params: dict) -> bool:
        return params.get("l", 0) >= 1 and params.get("min_adv_try", 0) >= 0 and params.get("mkt_stop", 0) >= 0

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        l = int(params["l"])
        if not self.valid(params):
            raise ValueError("need l >= 1, min_adv_try >= 0, mkt_stop >= 0")
        s = -(ctx.close / ctx.close.shift(l) - 1.0)
        s = _clean(s).where(ctx.adv >= float(params.get("min_adv_try", 0.0)))
        stop = float(params.get("mkt_stop", 0.0))
        if stop > 0 and ctx.benchmark is not None:
            bad = (ctx.benchmark / ctx.benchmark.shift(20) - 1.0) < -stop
            s[bad.reindex(ctx.index).fillna(False).to_numpy(bool)] = np.nan
        return s


class XSLowVol:
    """Low-volatility anomaly: score = -(std of daily returns over ``window`` days).

    Hypothesis: leverage constraints and lottery preferences make high-vol stocks overpriced; low-vol names earn
    higher risk-adjusted returns. Ang-Hodrick-Xing-Zhang (2006); Baker-Bradley-Wurgler (2011); Frazzini-Pedersen
    (2014). Grid: window in {60,120,250}.
    """
    name = "xs_low_vol"
    default_grid = {"window": [60, 120, 250]}

    def valid(self, params: dict) -> bool:
        return params.get("window", 0) >= 20

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        w = int(params["window"])
        if not self.valid(params):
            raise ValueError("window must be >= 20")
        return _clean(-_rets(ctx).rolling(w, min_periods=w).std())


class XSLowBeta:
    """Betting-against-beta (long-only leg): score = -(rolling beta to XU100 over ``window`` days).

    Hypothesis: investors who cannot lever overpay for high-beta stocks, flattening the security market line.
    Black-Jensen-Scholes (1972); Frazzini-Pedersen (2014). Beta is a plain causal rolling cov/var of daily returns
    (no shrinkage). Needs XU100 in the context; otherwise all-NaN. Grid: window in {120,250}.
    """
    name = "xs_low_beta"
    default_grid = {"window": [120, 250]}

    def valid(self, params: dict) -> bool:
        return params.get("window", 0) >= 60

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        w = int(params["window"])
        if not self.valid(params):
            raise ValueError("window must be >= 60")
        if ctx.benchmark is None:
            return _nan(ctx)
        return _clean(-_rolling_beta_cov(ctx, w)[0])


class XSQualityProxy:
    """Quality PROXY from return stability only. TRUE quality (profitability, leverage, accruals from financial
    statements) is NOT available in this system; this is a price-based stand-in and must not be reported as
    'quality'.

    Hypothesis: stable, shallow-drawdown, low-idiosyncratic-risk names behave like high-quality firms (Asness-
    Frazzini-Pedersen 2019 'Quality minus Junk'; Ang et al. 2006 for idiosyncratic vol). ``method``:
      * ``maxdd``  : worst drawdown from the rolling-``window`` peak over the last ``window`` days (less negative = better)
      * ``sortino``: mean daily return / downside deviation over ``window`` days
      * ``idio_vol``: -(std of residual vs XU100: sqrt(var_i - beta*cov_im)) over ``window`` days (needs XU100)
    Grid: method x window in {120,250} -> 6 combos.
    """
    name = "xs_quality_proxy"
    default_grid = {"method": ["maxdd", "sortino", "idio_vol"], "window": [120, 250]}
    _methods = ("maxdd", "sortino", "idio_vol")

    def valid(self, params: dict) -> bool:
        return params.get("method") in self._methods and params.get("window", 0) >= 60

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        w, m = int(params["window"]), params["method"]
        if not self.valid(params):
            raise ValueError(f"method must be one of {self._methods}, window >= 60")
        if m == "maxdd":
            c = ctx.close
            peak = c.rolling(w, min_periods=w).max()
            dd = c / peak - 1.0
            return _clean(dd.rolling(w, min_periods=w).min())
        r = _rets(ctx)
        if m == "sortino":
            mean = r.rolling(w, min_periods=w).mean()
            dsd = np.sqrt((r.clip(upper=0.0) ** 2).where(r.notna()).rolling(w, min_periods=w).mean())
            return _clean(mean / dsd.where(dsd > 0))
        if ctx.benchmark is None:
            return _nan(ctx)
        beta, cov, _ = _rolling_beta_cov(ctx, w)
        var_i = r.rolling(w, min_periods=w).var()
        resid = (var_i - beta * cov).clip(lower=0.0)
        return _clean(-np.sqrt(resid))


class XSVolumeShock:
    """Abnormal-volume shock signed by price direction.

    score = mean over the last ``l`` days of z(volume) (z vs the trailing 60-day mean/std, window ending at t),
    multiplied by sign(return over the last l days); ``invert``=1 flips the sign.
    Hypothesis: a volume spike with a positive return signals informed buying / attention that continues (Gervais-
    Kaniel-Mingelgrin 2001 high-volume return premium; Lee-Swaminathan 2000); the inverted version tests the
    attention-overreaction (reversal) alternative (Barber-Odean 2008). Grid: l in {1,3,5} x invert in {0,1} -> 6.
    """
    name = "xs_volume_shock"
    default_grid = {"l": [1, 3, 5], "invert": [0, 1]}
    ADV_WINDOW = 60

    def valid(self, params: dict) -> bool:
        return params.get("l", 0) >= 1 and params.get("invert", 0) in (0, 1, False, True)

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        l = int(params["l"])
        if not self.valid(params):
            raise ValueError("need l >= 1, invert in {0,1}")
        w = self.ADV_WINDOW
        v = ctx.volume
        mu, sd = v.rolling(w, min_periods=w).mean(), v.rolling(w, min_periods=w).std()
        z = ((v - mu) / sd.where(sd > 0)).rolling(l, min_periods=l).mean()
        sign = np.sign(ctx.close / ctx.close.shift(l) - 1.0)
        s = z * sign
        return _clean(-s if int(params.get("invert", 0)) else s)


for _fam in (XSMomentum121(), XSMomentum16(), XSReversal(), XSLowVol(), XSLowBeta(), XSQualityProxy(),
             XSVolumeShock()):
    register_family(_fam, overwrite=True)
