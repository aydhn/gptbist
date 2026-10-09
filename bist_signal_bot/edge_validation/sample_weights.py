"""Sample weights for overlapping labels (AFML ch. 4). Pure numpy/pandas.

Events span [t0, t1] (inclusive). Concurrency is measured on a time grid: by
default the sorted union of all t0/t1 values, or a user supplied ``grid`` (e.g.
the bar index) for exact per-bar accounting. Deterministic.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _spans(t0, t1, grid=None):
    a_v, b_v = np.asarray(t0), np.asarray(t1)
    if len(a_v) != len(b_v):
        raise ValueError("t0 and t1 must have equal length")
    if len(a_v) and np.any(b_v < a_v):
        raise ValueError("t1 must be >= t0")
    if grid is None:
        g = np.unique(np.concatenate([a_v, b_v])) if len(a_v) else a_v
    else:
        g = np.unique(np.asarray(grid))
    s = np.searchsorted(g, a_v, side="left")
    e = np.searchsorted(g, b_v, side="right")  # exclusive
    return g, s, e


def _concurrency(n_grid: int, s: np.ndarray, e: np.ndarray) -> np.ndarray:
    d = np.zeros(n_grid + 1)
    np.add.at(d, s, 1.0)
    np.add.at(d, e, -1.0)
    return np.cumsum(d)[:n_grid]


def average_uniqueness(t0, t1, grid=None) -> np.ndarray:
    """Average uniqueness per event in (0, 1]: mean of 1/concurrency over its span."""
    g, s, e = _spans(t0, t1, grid)
    if len(s) == 0:
        return np.array([], dtype=float)
    c = _concurrency(len(g), s, e)
    inv = np.where(c > 0, 1.0 / np.maximum(c, 1e-12), 0.0)
    cs = np.concatenate([[0.0], np.cumsum(inv)])
    length = np.maximum(e - s, 1)
    return (cs[e] - cs[s]) / length


def time_decay_weights(uniqueness, last_weight: float = 0.5) -> np.ndarray:
    """Piecewise-linear time decay (AFML 4.11) over events in chronological order.

    AFML semantics: the newest event has weight 1 and the oldest ~``last_weight``
    (1 = no decay; negative values zero out the oldest fraction). Decay runs
    over cumulative uniqueness.
    """
    u = np.asarray(uniqueness, dtype=float)
    if u.size == 0:
        return u.copy()
    cum = np.cumsum(u)
    total = cum[-1]
    c = float(last_weight)
    slope = (1.0 - c) / total if c >= 0 else 1.0 / ((c + 1.0) * total)
    const = 1.0 - slope * total
    w = const + slope * cum
    w[w < 0] = 0.0
    return w


def return_attribution_weights(t0, t1, ret, grid=None, bar_ret=None) -> np.ndarray:
    """Return-attribution weights (AFML 4.10), normalised to sum to len(events).

    w_i = | sum_{t in span_i} r_t / c_t |. If ``bar_ret`` (array aligned with the
    grid) is not given, per-grid-point returns are approximated by spreading each
    event's log(1+ret) evenly over its span and averaging over concurrent events.
    """
    g, s, e = _spans(t0, t1, grid)
    n = len(s)
    if n == 0:
        return np.array([], dtype=float)
    r_ev = np.log1p(np.clip(np.asarray(ret, dtype=float), -0.999999, None))
    if len(r_ev) != n:
        raise ValueError("ret length mismatch")
    c = _concurrency(len(g), s, e)
    csafe = np.maximum(c, 1.0)
    if bar_ret is None:
        share = r_ev / np.maximum(e - s, 1)
        d = np.zeros(len(g) + 1)
        np.add.at(d, s, share)
        np.add.at(d, e, -share)
        r_t = np.cumsum(d)[: len(g)] / csafe
    else:
        r_t = np.asarray(bar_ret, dtype=float)
        if len(r_t) != len(g):
            raise ValueError("bar_ret must align with the grid")
    cs = np.concatenate([[0.0], np.cumsum(np.where(c > 0, r_t / csafe, 0.0))])
    w = np.abs(cs[e] - cs[s])
    tot = w.sum()
    return w * (n / tot) if tot > 0 else np.ones(n)


def sequential_bootstrap(t0, t1, n=None, rng=None, grid=None) -> np.ndarray:
    """Sequential bootstrap (AFML 4.5): returns ``n`` event positions.

    Each draw picks event j with probability proportional to the average
    uniqueness it would have given the events already drawn.
    """
    g, s, e = _spans(t0, t1, grid)
    m = len(s)
    if m == 0:
        return np.array([], dtype=int)
    n = m if n is None else int(n)
    if not isinstance(rng, np.random.Generator):
        rng = np.random.default_rng(0 if rng is None else rng)
    ind = np.zeros((m, len(g)))
    for j in range(m):
        ind[j, s[j]:e[j]] = 1.0
    length = np.maximum(ind.sum(axis=1), 1.0)
    conc = np.zeros(len(g))
    out = np.empty(n, dtype=int)
    for k in range(n):
        c = conc[None, :] + ind
        u = (ind / np.where(c > 0, c, 1.0)).sum(axis=1) / length
        p = u / u.sum()
        j = int(rng.choice(m, p=p))
        out[k] = j
        conc += ind[j]
    return out
