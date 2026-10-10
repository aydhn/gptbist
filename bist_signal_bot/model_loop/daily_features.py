"""Causal cross-sectional feature panel (date x symbol) for the multi-day ML research path.

Research/paper only. No real order is ever sent.

Causality contract: every cell at row t depends on rows <= t of the DailyContext only (truncating future rows never
changes earlier feature rows; see tests). Cross-sectional features are winsorised (1%/99% per date) and then
rank-normalised per date to a clipped normal score, so level/scale/regime drift of the raw features cannot leak
into the model. Market-level features (identical for every symbol on a date) cannot be rank-normalised
cross-sectionally; they are turned into a causal *expanding percentile* (or a bounded flag) instead.

Sector proxy: there is no sector map in the archive, so peers are correlation clusters re-estimated every
``CLUSTER_REFRESH`` sessions from the trailing ``CLUSTER_WINDOW`` sessions only (refresh positions are absolute
row positions, hence identical for truncated contexts).

Panel layout: ``FeaturePanel.X`` has shape (n_dates, n_symbols, n_features) float32 with NaN where a feature is
unavailable; ``Z`` is the model-ready version (NaN -> 0 after normalisation, 0 = cross-sectional median).
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.xsection import DailyContext

NO_ORDER = "No real order sent."
# Bump whenever FEATURE_COLUMNS / feature definitions change; it is part of ML trial ids so ledger rows computed on a
# different feature set are never conflated. v2: market-residual clusters with size limits (v1 was degenerate: one
# cluster) and rs_xu_20/60 (identical to ret_20/60 after per-date rank-normalisation) replaced by res_xu_20/60.
FEATURES_VERSION = 2
CLUSTER_WINDOW = 250
CLUSTER_REFRESH = 60
CLUSTER_MIN_SIZE = 5
CLUSTER_MAX_FRAC = 0.4   # no cluster may hold more than max(2*min_size, ceil(frac*m)) symbols
CLUSTER_K_MAX = 10
WINSOR = (0.01, 0.99)
Z_CLIP = 3.0
MIN_FINITE_FRAC = 0.75  # a (date, symbol) row is usable when >= this share of features is finite

# cross-sectional (per symbol) features
CS_FEATURES: List[str] = [
    "ret_5", "ret_20", "ret_60", "ret_120", "ret_250",
    "mom_20_5", "mom_60_5", "mom_120_5", "mom_250_21",
    "vol_20", "vol_60", "vol_120",
    "beta_120", "idio_vol_60", "drawdown_250", "dist_high_252",
    "volume_shock_5", "volume_shock_1",
    "res_xu_20", "res_xu_60", "rs_cluster_20", "rs_cluster_60",
    "usdtry_beta_120",
]
# market-level features (same value for every symbol on a date)
MKT_FEATURES: List[str] = [
    "mkt_trend", "mkt_vol_high", "mkt_breadth_long", "mkt_ret_20_pct", "usdtry_trend_20_pct",
    "cal_turn_of_month", "cal_days_to_month_end",
]
FEATURE_COLUMNS: List[str] = CS_FEATURES + MKT_FEATURES


@dataclass
class FeaturePanel:
    X: np.ndarray              # raw (n, m, F) float32 (cross-sectional features winsorised+rank-normalised already)
    Z: np.ndarray              # model-ready (n, m, F) float32, NaN -> 0
    valid: np.ndarray          # (n, m) bool: universe_mask & enough finite features
    index: pd.DatetimeIndex
    symbols: List[str]
    columns: List[str]

    def rows(self, pos: np.ndarray, j: np.ndarray) -> np.ndarray:
        return self.Z[pos, j, :]


# ----------------------------------------------------------------------------- helpers
def _rets(ctx: DailyContext) -> pd.DataFrame:
    return ctx.close.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)


def winsorize_rows(a: np.ndarray, lo: float = WINSOR[0], hi: float = WINSOR[1]) -> np.ndarray:
    """Clip each row (date) to its own [lo, hi] quantiles (NaN-safe). Pure row-local => causal."""
    out = a.copy()
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        ql = np.nanquantile(a, lo, axis=1)
        qh = np.nanquantile(a, hi, axis=1)
    ok = np.isfinite(ql) & np.isfinite(qh)
    out[ok] = np.clip(a[ok], ql[ok, None], qh[ok, None])
    return out


def rank_normalize_rows(a: np.ndarray, clip: float = Z_CLIP) -> np.ndarray:
    """Per-row rank -> (0,1) -> normal score, clipped. NaN stays NaN. Ties get the average rank."""
    from scipy.special import ndtri
    df = pd.DataFrame(a)
    r = df.rank(axis=1, method="average", pct=False)
    n = df.notna().sum(axis=1).to_numpy(float)
    u = (r.to_numpy(float) - 0.5) / np.maximum(n, 1.0)[:, None]
    z = ndtri(np.clip(u, 1e-6, 1 - 1e-6))
    z[~np.isfinite(a)] = np.nan
    z[n < 5] = np.nan  # too few names for a meaningful cross-section
    return np.clip(z, -clip, clip)


def _expanding_pct(s: pd.Series, min_periods: int = 60) -> pd.Series:
    """Causal percentile of s_t within s_{<=t} (in [0,1])."""
    return s.expanding(min_periods=min_periods).rank(pct=True)


def _market_residual(R: np.ndarray) -> np.ndarray:
    """Remove the (equal-weight cross-sectional mean) market factor from a (T, m) return window: R - beta_i * mkt,
    beta_i = cov(R_i, mkt)/var(mkt) over the window. Without this every stock is highly correlated with the market
    and average-linkage clustering collapses into one cluster. Window-local => causal when the window ends at t."""
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mkt = np.nanmean(R, axis=1)
    mkt = np.nan_to_num(mkt, nan=0.0)
    var = float(np.var(mkt))
    if var <= 0:
        return R
    Rc = np.where(np.isfinite(R), R, np.nan)
    with np.errstate(all="ignore"), warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        mu = np.nanmean(Rc, axis=0)
        beta = np.nansum((Rc - mu) * (mkt - mkt.mean())[:, None], axis=0) / (len(mkt) * var)
    return Rc - np.nan_to_num(beta, nan=1.0)[None, :] * mkt[:, None]


def _bisect(idx: np.ndarray, D: np.ndarray, min_size: int) -> List[np.ndarray]:
    """Split a cluster in two: average-linkage 2-cut; if that is degenerate (a side < min_size, i.e. chaining) fall
    back to a balanced split along the first principal axis of the member similarity matrix."""
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import squareform
    sub = D[np.ix_(idx, idx)]
    lab = fcluster(linkage(squareform(sub, checks=False), method="average"), t=2, criterion="maxclust")
    a, b = idx[lab == 1], idx[lab != 1]
    if len(a) < min_size or len(b) < min_size:
        w, v = np.linalg.eigh(1.0 - sub)
        order = np.argsort(v[:, -1], kind="stable")
        half = len(idx) // 2
        a, b = idx[order[:half]], idx[order[half:]]
    return [a, b]


def _corr_clusters(R: np.ndarray, k_max: int = CLUSTER_K_MAX, min_size: int = CLUSTER_MIN_SIZE,
                   max_frac: float = CLUSTER_MAX_FRAC) -> np.ndarray:
    """Cluster labels (m,) from the correlation of MARKET-RESIDUAL returns in the (T, m) window (NaN -> 0 corr).
    Deterministic. Recursive bisection of the largest cluster until every cluster has <= max_size symbols
    (max_size = max(2*min_size, ceil(max_frac*m))) or ``k_max`` clusters exist; every produced cluster has
    >= min_size symbols (a bisection is only accepted if both sides do). Universes with m < 2*min_size symbols stay
    a single cluster (a cluster peer-relative feature is meaningless there)."""
    m = R.shape[1]
    if m < 4:
        return np.zeros(m, dtype=int)
    C = pd.DataFrame(_market_residual(R)).corr(min_periods=30).to_numpy(float)
    C = np.nan_to_num(C, nan=0.0)
    np.fill_diagonal(C, 1.0)
    D = np.clip(1.0 - C, 0.0, 2.0)
    D = (D + D.T) / 2.0
    np.fill_diagonal(D, 0.0)
    max_size = max(2 * min_size, int(np.ceil(max_frac * m)))
    clusters: List[np.ndarray] = [np.arange(m)]
    while len(clusters) < k_max:
        bi = max(range(len(clusters)), key=lambda i: len(clusters[i]))
        big = clusters[bi]
        if len(big) <= max_size or len(big) < 2 * min_size:
            break
        clusters = clusters[:bi] + clusters[bi + 1:] + _bisect(big, D, min_size)
    lab = np.zeros(m, dtype=int)
    for cid, members in enumerate(sorted(clusters, key=lambda a: int(a.min()))):
        lab[members] = cid
    return lab


def cluster_labels(ctx: DailyContext, window: int = CLUSTER_WINDOW, refresh: int = CLUSTER_REFRESH) -> np.ndarray:
    """(n, m) int cluster id known at the close of each row (-1 before the first refresh). Causal."""
    n, m = len(ctx.index), len(ctx.symbols)
    out = np.full((n, m), -1, dtype=int)
    R = _rets(ctx).to_numpy(float)
    pos = window
    while pos < n:
        lab = _corr_clusters(R[pos - window + 1:pos + 1])
        out[pos:min(pos + refresh, n)] = lab[None, :]
        pos += refresh
    return out


def _cluster_mean(a: np.ndarray, lab: np.ndarray) -> np.ndarray:
    """Row-wise mean of ``a`` over the symbols that share the symbol's cluster (NaN-safe; lab -1 -> NaN)."""
    out = np.full(a.shape, np.nan)
    for cid in np.unique(lab[lab >= 0]):
        msk = lab == cid
        v = np.where(msk, a, np.nan)
        with np.errstate(all="ignore"), warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            mu = np.nanmean(v, axis=1)
        out = np.where(msk, mu[:, None], out)
    return out


# ----------------------------------------------------------------------------- raw features
def raw_features(ctx: DailyContext) -> Dict[str, np.ndarray]:
    """name -> (n, m) raw arrays (cross-sectional features) and (n,) arrays (market-level)."""
    idx = ctx.index
    c, v = ctx.close, ctx.volume
    r = _rets(ctx)
    out: Dict[str, np.ndarray] = {}

    def ret(lb: int, sk: int = 0) -> pd.DataFrame:
        return (c.shift(sk) / c.shift(lb) - 1.0).replace([np.inf, -np.inf], np.nan)

    for lb in (5, 20, 60, 120, 250):
        out[f"ret_{lb}"] = ret(lb).to_numpy(float)
    for lb, sk in ((20, 5), (60, 5), (120, 5), (250, 21)):
        out[f"mom_{lb}_{sk}"] = ret(lb, sk).to_numpy(float)
    for w in (20, 60, 120):
        out[f"vol_{w}"] = r.rolling(w, min_periods=w).std().to_numpy(float)
    peak = c.rolling(250, min_periods=120).max()
    out["drawdown_250"] = (c / peak - 1.0).to_numpy(float)
    out["dist_high_252"] = (c / c.rolling(252, min_periods=120).max() - 1.0).to_numpy(float)
    adv60 = v.rolling(60, min_periods=60).mean()
    out["volume_shock_5"] = (v.rolling(5, min_periods=5).mean() / adv60.where(adv60 > 0)).to_numpy(float)
    out["volume_shock_1"] = (v / adv60.where(adv60 > 0)).to_numpy(float)

    nan = np.full((len(idx), len(ctx.symbols)), np.nan)
    if ctx.benchmark is not None:
        rm = ctx.benchmark.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)
        cov = r.rolling(120, min_periods=120).cov(rm)
        var = rm.rolling(120, min_periods=120).var()
        beta = cov.div(var.where(var > 0), axis=0)
        out["beta_120"] = beta.to_numpy(float)
        r60 = r.rolling(60, min_periods=60)
        cov60 = r60.cov(rm)
        var60 = rm.rolling(60, min_periods=60).var()
        beta60 = cov60.div(var60.where(var60 > 0), axis=0)
        resid = (r60.var() - beta60.mul(cov60)).clip(lower=0.0)
        out["idio_vol_60"] = np.sqrt(resid).to_numpy(float)
        bm = ctx.benchmark
        for w in (20, 60):  # beta-adjusted residual vs XU100 (a plain ret - xu100 is rank-identical to ret per date)
            res = ret(w).sub(beta.mul(bm / bm.shift(w) - 1.0, axis=0))
            out[f"res_xu_{w}"] = res.replace([np.inf, -np.inf], np.nan).to_numpy(float)
        out["mkt_ret_20_raw"] = (bm / bm.shift(20) - 1.0).to_numpy(float)
    else:
        for k in ("beta_120", "idio_vol_60", "res_xu_20", "res_xu_60"):
            out[k] = nan.copy()
        out["mkt_ret_20_raw"] = np.full(len(idx), np.nan)

    lab = cluster_labels(ctx)
    for w in (20, 60):
        a = ret(w).to_numpy(float)
        out[f"rs_cluster_{w}"] = a - _cluster_mean(a, lab)

    if ctx.usdtry is not None:
        rf = ctx.usdtry.pct_change(fill_method=None).replace([np.inf, -np.inf], np.nan)
        cov = r.rolling(120, min_periods=120).cov(rf)
        var = rf.rolling(120, min_periods=120).var()
        out["usdtry_beta_120"] = cov.div(var.where(var > 0), axis=0).to_numpy(float)
        out["usdtry_trend_20_raw"] = (ctx.usdtry / ctx.usdtry.shift(20) - 1.0).to_numpy(float)
    else:
        out["usdtry_beta_120"] = nan.copy()
        out["usdtry_trend_20_raw"] = np.full(len(idx), np.nan)
    return out


def market_features(ctx: DailyContext, raw: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """(n,) market-level / calendar features, all causal."""
    idx = ctx.index
    n = len(idx)
    nanv = np.full(n, np.nan)
    out = {k: nanv.copy() for k in MKT_FEATURES}
    if ctx.benchmark is not None and ctx.benchmark.notna().sum() > 260:
        from bist_signal_bot.edge_validation.regime_labels import label_regimes
        lr = label_regimes(ctx.benchmark.dropna())
        if len(lr):
            lr = lr.set_index("date")
            trend = lr["trend"].map({"bull": 1.0, "neutral": 0.0, "bear": -1.0}).reindex(idx)
            out["mkt_trend"] = trend.to_numpy(float)
            out["mkt_vol_high"] = (lr["vol"] == "high").astype(float).reindex(idx).to_numpy(float)
    cm = ctx.close
    sma = cm.rolling(200, min_periods=200).mean()
    ok = sma.notna() & cm.notna()
    cnt = ok.sum(axis=1)
    out["mkt_breadth_long"] = ((cm > sma) & ok).sum(axis=1).div(cnt.where(cnt >= 5)).to_numpy(float)
    out["mkt_ret_20_pct"] = _expanding_pct(pd.Series(raw["mkt_ret_20_raw"], index=idx)).to_numpy(float)
    out["usdtry_trend_20_pct"] = _expanding_pct(pd.Series(raw["usdtry_trend_20_raw"], index=idx)).to_numpy(float)
    dom = np.asarray(idx.day, float)
    dtm = np.asarray(idx.days_in_month, float) - dom  # calendar days to month end (pure function of the date)
    out["cal_turn_of_month"] = ((dom <= 4) | (dtm <= 3)).astype(float)
    out["cal_days_to_month_end"] = np.minimum(dtm, 31.0) / 31.0
    return out


# ----------------------------------------------------------------------------- panel
def build_feature_panel(ctx: DailyContext) -> FeaturePanel:
    n, m = len(ctx.index), len(ctx.symbols)
    raw = raw_features(ctx)
    mk = market_features(ctx, raw)
    X = np.full((n, m, len(FEATURE_COLUMNS)), np.nan, dtype=np.float32)
    for f, name in enumerate(FEATURE_COLUMNS):
        if name in CS_FEATURES:
            a = raw[name]
            a = np.where(np.isfinite(a), a, np.nan)
            X[:, :, f] = rank_normalize_rows(winsorize_rows(a)).astype(np.float32)
        else:
            X[:, :, f] = mk[name].astype(np.float32)[:, None]
    mask = ctx.universe_mask.to_numpy(bool)
    cs_idx = [FEATURE_COLUMNS.index(c) for c in CS_FEATURES]
    frac = np.isfinite(X[:, :, cs_idx]).mean(axis=2)
    valid = mask & (frac >= MIN_FINITE_FRAC)
    Z = np.nan_to_num(X, nan=0.0).astype(np.float32)
    return FeaturePanel(X, Z, valid, ctx.index, list(ctx.symbols), list(FEATURE_COLUMNS))


def cluster_diagnostics(ctx: DailyContext, window: int = CLUSTER_WINDOW) -> dict:
    """Real-data check: cluster the LAST ``window`` sessions and report sizes (must be > 1 cluster, sizes within the
    configured limits). Returns {n_clusters, sizes, ok, reason}. Use on the real archive context."""
    n, m = len(ctx.index), len(ctx.symbols)
    if n < 60 or m < 2 * CLUSTER_MIN_SIZE:
        return {"n_clusters": 1, "sizes": [m], "ok": False, "reason": "too few sessions/symbols"}
    lab = _corr_clusters(_rets(ctx).to_numpy(float)[max(0, n - window):])
    sizes = np.bincount(lab).tolist()
    max_size = max(2 * CLUSTER_MIN_SIZE, int(np.ceil(CLUSTER_MAX_FRAC * m)))
    ok = len(sizes) > 1 and min(sizes) >= CLUSTER_MIN_SIZE and max(sizes) <= max_size
    return {"n_clusters": len(sizes), "sizes": sizes, "ok": bool(ok), "max_size_allowed": max_size,
            "reason": "" if ok else "degenerate or size limits violated", "features_version": FEATURES_VERSION}


def get_feature_panel(ctx: DailyContext) -> FeaturePanel:
    """Per-context cache so grid combinations / horizons share one panel."""
    fp = getattr(ctx, "_ml_feature_panel", None)
    if fp is None:
        fp = build_feature_panel(ctx)
        ctx._ml_feature_panel = fp
    return fp
