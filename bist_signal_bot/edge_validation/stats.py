"""Edge-validation statistics: Sharpe inference, DSR/PSR, PBO (CSCV), bootstrap, multiple testing.

numpy/pandas/stdlib only (no scipy). Functions return NaN (never raise) on degenerate
input (n < 3, zero variance); ValueError only for malformed arguments.
Sharpe ratios passed to PSR/DSR/MinTRL are PER-PERIOD (non-annualised).
"""
from __future__ import annotations

import itertools
import math
from statistics import NormalDist
from typing import Callable, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

from bist_signal_bot.core.logging_setup import get_logger

logger = get_logger(__name__)

EULER_GAMMA = 0.5772156649015329
_ND = NormalDist()
NAN = float("nan")


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_ppf(p: float) -> float:
    if not (0.0 < p < 1.0):
        return NAN
    return _ND.inv_cdf(p)


def _clean(x) -> np.ndarray:
    a = np.asarray(x, dtype=float).ravel()
    return a[np.isfinite(a)]


def _moments(r: np.ndarray) -> Tuple[float, float, float, int]:
    """(per-period sharpe, skew, non-excess kurtosis, n); NaNs if undefined."""
    n = r.size
    if n < 3:
        return NAN, NAN, NAN, n
    sd = r.std(ddof=1)
    if not np.isfinite(sd) or sd <= 1e-12 * max(abs(r.mean()), 1e-300) or sd == 0:
        return NAN, NAN, NAN, n
    m = r.mean()
    z = (r - m) / r.std(ddof=0)
    return float(m / sd), float((z ** 3).mean()), float((z ** 4).mean()), n


# --------------------------------------------------------------------------- Sharpe
def sharpe(returns, periods_per_year: Optional[float] = None) -> float:
    r = _clean(returns)
    sr, _, _, _ = _moments(r)
    if not np.isfinite(sr):
        return NAN
    return sr * math.sqrt(periods_per_year) if periods_per_year else sr


def sharpe_standard_error(sr: float, n_obs: int, skew: float = 0.0, kurt: float = 3.0) -> float:
    """Asymptotic s.e. of a per-period Sharpe (Mertens 2002); kurt is NON-excess."""
    if n_obs is None or n_obs < 3 or not np.isfinite(sr):
        return NAN
    skew = 0.0 if not np.isfinite(skew) else skew
    kurt = 3.0 if not np.isfinite(kurt) else kurt
    v = 1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr ** 2
    return math.sqrt(v / (n_obs - 1)) if v > 0 else NAN


def probabilistic_sharpe_ratio(sr: float, benchmark_sr: float, n_obs: int,
                               skew: float = 0.0, kurt: float = 3.0) -> float:
    """P(true SR > benchmark_sr), Bailey & Lopez de Prado (2012). Per-period SRs."""
    se = sharpe_standard_error(sr, n_obs, skew, kurt)
    if not np.isfinite(se) or se <= 0:
        return NAN
    return norm_cdf((sr - benchmark_sr) / se)


def expected_max_sharpe(n_trials: int, var_trials_sr: float) -> float:
    """E[max SR] over n independent null trials with cross-trial SR variance (False Strategy Theorem)."""
    if n_trials is None or n_trials < 1 or not np.isfinite(var_trials_sr) or var_trials_sr < 0:
        return NAN
    if n_trials == 1:
        return 0.0
    g = EULER_GAMMA
    return math.sqrt(var_trials_sr) * ((1 - g) * norm_ppf(1 - 1.0 / n_trials)
                                      + g * norm_ppf(1 - 1.0 / (n_trials * math.e)))


def deflated_sharpe_ratio(returns_or_sr: Union[float, Sequence[float], np.ndarray, pd.Series],
                          n_trials: int, var_trials_sr: float,
                          n_obs: Optional[int] = None, skew: float = 0.0, kurt: float = 3.0) -> float:
    """DSR probability = PSR against the expected max SR of n_trials null trials.

    Series input: SR/skew/kurt/n estimated from it (per-period). Scalar input: per-period SR,
    n_obs required. var_trials_sr = variance of PER-PERIOD SRs across trials.
    """
    if np.ndim(returns_or_sr) == 0:
        sr = float(returns_or_sr)
        if n_obs is None:
            raise ValueError("n_obs required when passing a scalar Sharpe")
    else:
        sr, skew, kurt, n_obs = _moments(_clean(returns_or_sr))
        if not np.isfinite(sr):
            return NAN
    bench = expected_max_sharpe(n_trials, var_trials_sr)
    if not np.isfinite(bench):
        return NAN
    return probabilistic_sharpe_ratio(sr, bench, n_obs, skew, kurt)


def min_track_record_length(sr: float, benchmark_sr: float = 0.0, skew: float = 0.0,
                            kurt: float = 3.0, alpha: float = 0.05) -> float:
    """Observations needed for PSR(benchmark) >= 1-alpha. inf if sr <= benchmark."""
    if not np.isfinite(sr):
        return NAN
    if sr <= benchmark_sr:
        return math.inf
    v = 1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr ** 2
    z = norm_ppf(1 - alpha)
    return 1.0 + v * (z / (sr - benchmark_sr)) ** 2


def sharpe_pvalue(returns) -> float:
    """One-sided p-value for H0: SR <= 0, with skew/kurtosis-adjusted s.e."""
    sr, sk, ku, n = _moments(_clean(returns))
    if not np.isfinite(sr):
        return NAN
    psr = probabilistic_sharpe_ratio(sr, 0.0, n, sk, ku)
    return NAN if not np.isfinite(psr) else float(1.0 - psr)


# --------------------------------------------------------------------------- PBO
def _metric_from_moments(metric: str, n: float, s: np.ndarray, q: np.ndarray) -> np.ndarray:
    mean = s / n
    if metric == "mean":
        return mean
    var = (q - n * mean ** 2) / max(n - 1, 1)
    sd = np.sqrt(np.maximum(var, 0))
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(sd > 1e-15, mean / sd, 0.0)


def probability_of_backtest_overfitting(perf_matrix, n_blocks: int = 16,
                                        metric: str = "sharpe") -> dict:
    """CSCV PBO (Bailey, Borwein, Lopez de Prado, Zhu). perf_matrix: T x N_trials per-period returns.

    Returns dict(pbo, logits, degradation_slope, prob_loss, n_combinations, n_trials).
    NaN returns are treated as 0. Too-short/1-column input -> pbo NaN.
    """
    if metric not in ("sharpe", "mean"):
        raise ValueError("metric must be 'sharpe' or 'mean'")
    if n_blocks % 2 or n_blocks < 2:
        raise ValueError("n_blocks must be an even integer >= 2")
    X = np.nan_to_num(np.asarray(perf_matrix, dtype=float), nan=0.0)
    nan_res = dict(pbo=NAN, logits=np.array([]), degradation_slope=NAN, prob_loss=NAN,
                   n_combinations=0, n_trials=0)
    if X.ndim != 2 or X.shape[1] < 2:
        return nan_res
    T, N = X.shape
    if T < n_blocks * 2:
        return {**nan_res, "n_trials": N}
    L = T // n_blocks
    blocks = X[:L * n_blocks].reshape(n_blocks, L, N)
    bs, bq = blocks.sum(axis=1), (blocks ** 2).sum(axis=1)  # (S, N)
    combos = np.array(list(itertools.combinations(range(n_blocks), n_blocks // 2)))
    M = np.zeros((len(combos), n_blocks))
    np.put_along_axis(M, combos, 1.0, axis=1)
    Mo = 1.0 - M
    half = float(L * (n_blocks // 2))
    is_perf = _metric_from_moments(metric, half, M @ bs, M @ bq)
    oos_perf = _metric_from_moments(metric, half, Mo @ bs, Mo @ bq)
    best = is_perf.argmax(axis=1)
    rows = np.arange(len(combos))
    oos_best = oos_perf[rows, best]
    less = (oos_perf < oos_best[:, None]).sum(axis=1)
    equal = (oos_perf == oos_best[:, None]).sum(axis=1)
    rank = less + (equal + 1) / 2.0           # 1..N, ties averaged
    w = rank / (N + 1.0)
    logits = np.log(w / (1.0 - w))
    is_best = is_perf[rows, best]
    slope = float(np.polyfit(is_best, oos_best, 1)[0]) if np.std(is_best) > 0 else NAN
    return dict(pbo=float((logits <= 0).mean()), logits=logits, degradation_slope=slope,
                prob_loss=float((oos_best < 0).mean()), n_combinations=len(combos), n_trials=N)


# --------------------------------------------------------------------------- bootstrap
def _bootstrap_indices(n: int, n_boot: int, block_len: float, rng: np.random.Generator,
                       method: str = "stationary") -> np.ndarray:
    block_len = max(1.0, float(block_len))
    if method == "stationary":
        idx = np.empty((n_boot, n), dtype=np.int64)
        idx[:, 0] = rng.integers(0, n, n_boot)
        new = rng.random((n_boot, n)) < (1.0 / block_len)
        starts = rng.integers(0, n, (n_boot, n))
        for t in range(1, n):
            idx[:, t] = np.where(new[:, t], starts[:, t], (idx[:, t - 1] + 1) % n)
        return idx
    if method == "circular":
        b = int(round(block_len))
        n_blk = -(-n // b)
        st = rng.integers(0, n, (n_boot, n_blk))
        full = (st[:, :, None] + np.arange(b)[None, None, :]) % n
        return full.reshape(n_boot, -1)[:, :n]
    raise ValueError("method must be 'stationary' or 'circular'")


def block_bootstrap_ci(returns, block_len: Optional[int] = None, n: int = 2000,
                       stat: Callable[[np.ndarray], float] = np.mean, alpha: float = 0.05,
                       seed: int = 0, method: str = "stationary") -> Tuple[float, float]:
    """Percentile CI for stat(returns) via stationary (default) or circular block bootstrap."""
    r = _clean(returns)
    if r.size < 3:
        return NAN, NAN
    if block_len is None:
        block_len = max(1, int(round(r.size ** (1 / 3))))
    rng = np.random.default_rng(seed)
    samples = r[_bootstrap_indices(r.size, n, block_len, rng, method)]
    if stat is np.mean:
        vals = samples.mean(axis=1)
    else:
        vals = np.array([stat(s) for s in samples], dtype=float)
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return NAN, NAN
    return float(np.quantile(vals, alpha / 2)), float(np.quantile(vals, 1 - alpha / 2))


def effective_sample_size(returns) -> float:
    """n / (1 + 2*sum rho_k) summing positive autocorrelations until the first non-positive one."""
    r = _clean(returns)
    n = r.size
    if n < 3:
        return float(n) if n else NAN
    x = r - r.mean()
    d = float((x ** 2).sum())
    if d <= 0:
        return NAN
    s = 0.0
    for k in range(1, max(2, n // 4)):
        rho = float((x[k:] * x[:-k]).sum() / d)
        if rho <= 0:
            break
        s += rho * (1 - k / n)
    return float(min(n, max(1.0, n / (1 + 2 * s))))


# --------------------------------------------------------------------------- multiple testing
def bonferroni(pvalues, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """(adjusted p-values, reject flags)."""
    p = np.asarray(pvalues, dtype=float)
    adj = np.minimum(p * p.size, 1.0)
    return adj, adj <= alpha


def holm(pvalues, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    p = np.asarray(pvalues, dtype=float)
    m = p.size
    order = np.argsort(p)
    adj_sorted = np.maximum.accumulate((m - np.arange(m)) * p[order])
    adj = np.empty(m)
    adj[order] = np.minimum(adj_sorted, 1.0)
    return adj, adj <= alpha


def benjamini_hochberg(pvalues, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    p = np.asarray(pvalues, dtype=float)
    m = p.size
    order = np.argsort(p)
    scaled = p[order] * m / (np.arange(m) + 1)
    adj_sorted = np.minimum.accumulate(scaled[::-1])[::-1]
    adj = np.empty(m)
    adj[order] = np.minimum(adj_sorted, 1.0)
    return adj, adj <= alpha


# --------------------------------------------------------------------------- reality check
def white_reality_check(returns_matrix, benchmark=None, n_boot: int = 1000,
                        block_len: Optional[int] = None, seed: int = 0) -> float:
    """White (2000) Reality Check p-value. H0: no strategy beats the benchmark (default 0).

    returns_matrix: T x K per-period returns; benchmark: length-T series or None.
    Stationary bootstrap of recentred means; statistic = max_k sqrt(T)*mean_k.
    """
    X = np.asarray(returns_matrix, dtype=float)
    if X.ndim == 1:
        X = X[:, None]
    if benchmark is not None:
        b = np.asarray(benchmark, dtype=float).ravel()
        if b.size != X.shape[0]:
            raise ValueError("benchmark length must equal number of rows")
        X = X - b[:, None]
    X = X[np.isfinite(X).all(axis=1)]
    T = X.shape[0]
    if T < 3 or X.shape[1] < 1:
        return NAN
    if block_len is None:
        block_len = max(1, int(round(T ** (1 / 3))))
    mean = X.mean(axis=0)
    obs = math.sqrt(T) * mean.max()
    idx = _bootstrap_indices(T, n_boot, block_len, np.random.default_rng(seed), "stationary")
    boot_means = np.stack([X[idx[i]].mean(axis=0) for i in range(n_boot)])
    stat = math.sqrt(T) * (boot_means - mean).max(axis=1)
    return float((1 + (stat >= obs).sum()) / (n_boot + 1))
