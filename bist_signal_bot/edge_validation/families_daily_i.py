"""Block-I composite / conditional daily families (self-registering). Research only; no real order is sent.

Every score at row t uses data <= t. Cross-sectional ranks are percentile ranks WITHIN the point-in-time universe
(``ctx.universe_mask``); ineligible cells are NaN. Grids are tiny on purpose: each combination is one ledger trial.
Existing families are reused through the ``DAILY_FAMILIES`` registry (looked up lazily), not copied.

Honest notes
  * ``regime_labels.py`` is breadth/exposure oriented, so the XU100 regime here is computed directly from
    ``ctx.benchmark`` (close vs MA, 20d realised vol percentile) with causal rolling windows only.
  * ``xs_turnover_damped_momentum`` smooths the SCORE (EMA of ranks) to lower rank churn; it is NOT a portfolio-level
    turnover constraint (top-N / rebalance rules and costs are applied downstream).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.families_daily import register_family
from bist_signal_bot.edge_validation.xsection import DailyContext


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    return df.replace([np.inf, -np.inf], np.nan)


def _prank(ctx: DailyContext, s: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional percentile rank (0..1, higher = better) among eligible names; NaN elsewhere."""
    return _clean(s).where(ctx.universe_mask).rank(axis=1, pct=True)


def _fam(name: str):
    from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
    return DAILY_FAMILIES[name]


def _mom121(ctx: DailyContext, lookback: int = 250, skip: int = 21) -> pd.DataFrame:
    return _fam("xs_momentum_12_1").score(ctx, {"lookback": lookback, "skip": skip, "vol_scaled": 0})


def _lowvol(ctx: DailyContext, window: int) -> pd.DataFrame:
    return _fam("xs_low_vol").score(ctx, {"window": window})


class XSLowVolXMomentum:
    """Interaction: average of percentile ranks of low-vol (-std of daily returns over ``vol_window``) and 12-1 style
    momentum (return over [t-mom_lookback, t-21]). Hypothesis: the low-vol and momentum premia are complementary
    (negatively correlated), so names good on both are less crash-prone (Blitz-van Vliet 2007; Asness et al. 2013).
    Both ranks required, else NaN. Grid 2x2 = 4."""
    name = "xs_lowvol_x_momentum"
    default_grid = {"vol_window": [60, 120], "mom_lookback": [250, 126]}
    SKIP = 21

    def valid(self, params: dict) -> bool:
        return int(params.get("vol_window", 0)) >= 20 and int(params.get("mom_lookback", 0)) > self.SKIP

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        if not self.valid(params):
            raise ValueError("need vol_window >= 20 and mom_lookback > 21")
        rv = _prank(ctx, _lowvol(ctx, int(params["vol_window"])))
        rm = _prank(ctx, _mom121(ctx, int(params["mom_lookback"]), self.SKIP))
        return ((rv + rm) / 2.0).where(rv.notna() & rm.notna())


class XSMultiHorizonEnsemble:
    """Average of cross-sectional percentile ranks of existing price signals (all members required, else NaN).
    variant 'A': momentum 1-6 + momentum 12-1 + relative strength vs XU100 (beta-adjusted, 60d);
    variant 'B': A + quality proxy (max drawdown, 250d; price-based stand-in, NOT true quality).
    Hypothesis: averaging weakly-correlated horizons reduces single-signal noise (score-averaging ensembles; Jegadeesh-
    Titman 1993 multiple horizons). Needs XU100 (member raises without it). Grid: 2."""
    name = "xs_multi_horizon_ensemble"
    default_grid = {"variant": ["A", "B"]}

    def valid(self, params: dict) -> bool:
        return params.get("variant") in ("A", "B")

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        if not self.valid(params):
            raise ValueError("variant must be 'A' or 'B'")
        parts = [_fam("xs_momentum_1_6").score(ctx, {"lookback": 126, "skip": 5, "vol_scaled": 0}),
                 _fam("xs_momentum_12_1").score(ctx, {"lookback": 250, "skip": 21, "vol_scaled": 0}),
                 _fam("xs_rel_strength_index").score(ctx, {"lookback": 60, "adjust": "beta"})]
        if params["variant"] == "B":
            parts.append(_fam("xs_quality_proxy").score(ctx, {"method": "maxdd", "window": 250}))
        ranks = [_prank(ctx, p) for p in parts]
        ok = ranks[0].notna()
        tot = ranks[0].copy()
        for r in ranks[1:]:
            ok = ok & r.notna()
            tot = tot + r
        return (tot / len(ranks)).where(ok)


class XSRegimeMomentum:
    """XU100 regime switch. risk-on (benchmark close > MA(ma_window) AND 20d realised-vol percentile, ranked against
    the trailing 252 sessions, < vol_thr): score = rank of 12-1 momentum. Otherwise (risk-off): score = rank of
    low vol (60d). Regime at t uses benchmark data <= t only. Without a benchmark, or while the regime is undefined
    (insufficient history), the score is NaN. Hypothesis: momentum pays in calm uptrends and crashes in
    rebounds/high vol (Daniel-Moskowitz 2016); defensive low-vol is preferred otherwise. Grid: 2."""
    name = "xs_regime_momentum"
    default_grid = {"ma_window": [100, 200], "vol_thr": [0.8]}
    PCT_WINDOW = 252

    def valid(self, params: dict) -> bool:
        return int(params.get("ma_window", 0)) >= 20 and 0.0 < float(params.get("vol_thr", 0)) <= 1.0

    def regime_on(self, ctx: DailyContext, ma_window: int, vol_thr: float) -> pd.Series:
        """Float series: 1.0 risk-on, 0.0 risk-off, NaN undefined."""
        b = ctx.benchmark.ffill()
        ma = b.rolling(ma_window, min_periods=ma_window).mean()
        vol = b.pct_change(fill_method=None).rolling(20, min_periods=20).std()
        pct = vol.rolling(self.PCT_WINDOW, min_periods=self.PCT_WINDOW // 2).apply(
            lambda x: float((x <= x[-1]).mean()), raw=True)
        defined = ma.notna() & pct.notna() & b.notna()
        on = ((b > ma) & (pct < vol_thr)).astype(float)
        return on.where(defined)

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        if not self.valid(params):
            raise ValueError("need ma_window >= 20 and 0 < vol_thr <= 1")
        if ctx.benchmark is None:
            raise ValueError("xs_regime_momentum needs the XU100 benchmark in the context")
        reg = self.regime_on(ctx, int(params["ma_window"]), float(params["vol_thr"]))
        rm = _prank(ctx, _mom121(ctx))
        rv = _prank(ctx, _lowvol(ctx, 60))
        on = (reg == 1.0).to_numpy()[:, None]
        s = pd.DataFrame(np.where(on, rm.to_numpy(float), rv.to_numpy(float)), index=ctx.index, columns=ctx.symbols)
        known = np.repeat(reg.notna().to_numpy()[:, None], len(ctx.symbols), axis=1)
        return s.where(pd.DataFrame(known, index=ctx.index, columns=ctx.symbols))


class XSSectorRSLiquid:
    """``xs_rel_strength_sector`` (data-driven peer clusters, NOT real sectors) restricted to liquid names: only
    names whose ADV is >= the ``adv_q`` cross-sectional quantile of ADV among the eligible universe on that date
    keep a score (others NaN). Peer means are still computed over the full universe. Hypothesis: lead-lag/industry
    momentum is cheaper to harvest in liquid names. Grid: lookback {20,60} x adv_q {0.5} -> 2 combos."""
    name = "xs_sector_rs_liquid"
    default_grid = {"lookback": [20, 60], "adv_q": [0.5], "n_clusters": [8], "corr_window": [250]}

    def valid(self, params: dict) -> bool:
        return (int(params.get("lookback", 0)) >= 2 and 0.0 <= float(params.get("adv_q", -1)) < 1.0
                and int(params.get("n_clusters", 0)) >= 2 and int(params.get("corr_window", 0)) >= 60)

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        if not self.valid(params):
            raise ValueError("bad params")
        s = _fam("xs_rel_strength_sector").score(ctx, {
            "lookback": int(params["lookback"]), "n_clusters": int(params.get("n_clusters", 8)),
            "corr_window": int(params.get("corr_window", 250))})
        adv = ctx.adv.where(ctx.universe_mask)
        thr = adv.quantile(float(params["adv_q"]), axis=1)
        liquid = adv.ge(thr, axis=0)
        return _clean(s).where(liquid & ctx.universe_mask)


class XSTurnoverDampedMomentum:
    """Momentum (return over [t-lookback, t-5]) percentile rank smoothed by an exponential moving average over time
    (``halflife`` sessions) to cut rank churn / turnover (cost-aware score). This damps the SCORE only; it is NOT a
    portfolio-level turnover constraint. EMA is causal (adjust=False); NaN gaps carry the last value but ineligible
    cells are masked. Grid: halflife {1,3,5} -> 3 combos."""
    name = "xs_turnover_damped_momentum"
    default_grid = {"halflife": [1, 3, 5], "lookback": [120]}
    SKIP = 5

    def valid(self, params: dict) -> bool:
        return float(params.get("halflife", 0)) > 0 and int(params.get("lookback", 0)) > self.SKIP

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        if not self.valid(params):
            raise ValueError("need halflife > 0 and lookback > 5")
        lb = int(params["lookback"])
        raw = _fam("xs_momentum").score(ctx, {"lookback": lb, "skip": self.SKIP})
        r = _prank(ctx, raw)
        sm = r.ewm(halflife=float(params["halflife"]), adjust=False, ignore_na=True).mean()
        return sm.where(r.notna())


for _f in (XSLowVolXMomentum(), XSMultiHorizonEnsemble(), XSRegimeMomentum(), XSSectorRSLiquid(),
           XSTurnoverDampedMomentum()):
    register_family(_f, overwrite=True)
