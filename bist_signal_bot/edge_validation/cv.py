"""Leakage-safe cross-validation for overlapping event labels.

Events carry a start ``t0`` and an end ``t1`` (t1 >= t0). Purging is done by
TIME across all rows (so cross-symbol panels are purged jointly, regardless of
symbol). All splitters return positional index arrays into the given t0/t1.
"""
from __future__ import annotations

import itertools
from math import comb
from typing import Dict, Iterator, List, Optional, Sequence, Tuple, Union

import numpy as np
import pandas as pd

from bist_signal_bot.core.logging_setup import get_logger

logger = get_logger(__name__)

TimeLike = Union[pd.Series, pd.DatetimeIndex, Sequence]
Span = Union[int, float, pd.Timedelta]  # plain numbers = days

_INF = np.iinfo(np.int64).max


def _ns(x: TimeLike) -> np.ndarray:
    """Timestamps -> int64 UTC nanoseconds (tz-safe)."""
    idx = pd.DatetimeIndex(pd.to_datetime(pd.Series(list(x))))
    return idx.as_unit("ns").asi8  # pandas>=2 may carry non-ns resolution


def _td_ns(x: Optional[Span]) -> int:
    if x is None:
        return 0
    if isinstance(x, pd.Timedelta):
        return int(x.value)
    return int(pd.Timedelta(days=x).value)


def _prep(t0: TimeLike, t1: TimeLike) -> Tuple[np.ndarray, np.ndarray]:
    a, b = _ns(t0), _ns(t1)
    if len(a) != len(b):
        raise ValueError("t0 and t1 must have the same length")
    if np.any(b < a):
        raise ValueError("t1 must be >= t0")
    return a, b


def _train_mask(a, b, spans: List[Tuple[int, int]], emb_ends: List[int]) -> np.ndarray:
    """Train = not purged and not embargoed w.r.t. every test span.

    spans: [(test_start, test_end)], emb_ends: end of embargo window per span
    (train rows with test_end < t0 <= emb_end are dropped).
    """
    mask = np.ones(len(a), dtype=bool)
    for (s, e), emb in zip(spans, emb_ends):
        mask &= ~((a <= e) & (b >= s))  # overlap (purge)
        mask &= ~((a > e) & (a <= emb))  # embargo
    return mask


def _embargo_end(a_sorted: np.ndarray, last_pos: int, test_end: int,
                 embargo_pct: float, embargo_bars: int, embargo_td: int) -> int:
    n = len(a_sorted)
    nb = max(int(embargo_bars), int(np.ceil(embargo_pct * n)) if embargo_pct else 0)
    end = test_end + embargo_td
    if nb > 0:
        pos = last_pos + nb
        end = max(end, int(a_sorted[pos]) if pos < n else _INF)
    return end


class _EmbargoMixin:
    def _set_embargo(self, embargo_pct, embargo_bars, embargo):
        if embargo_pct < 0 or embargo_bars < 0:
            raise ValueError("embargo must be >= 0")
        self.embargo_pct = float(embargo_pct)
        self.embargo_bars = int(embargo_bars)
        self.embargo = embargo  # extra time-based embargo (days or Timedelta)


class PurgedKFold(_EmbargoMixin):
    """K contiguous (by t0) test folds; purge overlapping, embargo after test.

    embargo_pct: fraction of events; embargo_bars: number of events (sorted by
    t0) after the test fold; embargo: calendar time (days or Timedelta). The
    largest applies.
    """

    def __init__(self, n_splits: int = 5, embargo_pct: float = 0.0,
                 embargo_bars: int = 0, embargo: Optional[Span] = None):
        if n_splits < 2:
            raise ValueError("n_splits must be >= 2")
        self.n_splits = n_splits
        self._set_embargo(embargo_pct, embargo_bars, embargo)

    def get_n_splits(self) -> int:
        return self.n_splits

    def split(self, t0: TimeLike, t1: TimeLike) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
        a, b = _prep(t0, t1)
        n = len(a)
        if n < self.n_splits:
            raise ValueError("fewer events than n_splits")
        order = np.argsort(a, kind="stable")
        a_s = a[order]
        for fold in np.array_split(np.arange(n), self.n_splits):
            test_idx = order[fold]
            s, e = int(a[test_idx].min()), int(b[test_idx].max())
            emb = _embargo_end(a_s, int(fold[-1]), e, self.embargo_pct,
                               self.embargo_bars, _td_ns(self.embargo))
            mask = _train_mask(a, b, [(s, e)], [emb])
            mask[test_idx] = False
            yield np.flatnonzero(mask), np.sort(test_idx)


class CombinatorialPurgedCV(_EmbargoMixin):
    """CPCV (AFML ch.12): N contiguous groups, all C(N,k) test combinations."""

    def __init__(self, n_groups: int = 6, n_test_groups: int = 2,
                 embargo_pct: float = 0.0, embargo_bars: int = 0,
                 embargo: Optional[Span] = None):
        if not 1 <= n_test_groups < n_groups:
            raise ValueError("need 1 <= n_test_groups < n_groups")
        self.n_groups = n_groups
        self.n_test_groups = n_test_groups
        self._set_embargo(embargo_pct, embargo_bars, embargo)

    @property
    def combinations(self) -> List[Tuple[int, ...]]:
        return list(itertools.combinations(range(self.n_groups), self.n_test_groups))

    @property
    def n_splits(self) -> int:
        return comb(self.n_groups, self.n_test_groups)

    @property
    def n_paths(self) -> int:
        return self.n_splits * self.n_test_groups // self.n_groups

    def get_n_splits(self) -> int:
        return self.n_splits

    def group_indices(self, t0: TimeLike) -> List[np.ndarray]:
        """Positional indices of each of the N contiguous (by t0) groups."""
        a = _ns(t0)
        if len(a) < self.n_groups:
            raise ValueError("fewer events than n_groups")
        order = np.argsort(a, kind="stable")
        return [order[g] for g in np.array_split(np.arange(len(a)), self.n_groups)]

    def split(self, t0: TimeLike, t1: TimeLike
              ) -> Iterator[Tuple[np.ndarray, np.ndarray, Tuple[int, ...]]]:
        a, b = _prep(t0, t1)
        if len(a) < self.n_groups:
            raise ValueError("fewer events than n_groups")
        order = np.argsort(a, kind="stable")
        a_s = a[order]
        pos_groups = np.array_split(np.arange(len(a)), self.n_groups)
        groups = [order[g] for g in pos_groups]
        td = _td_ns(self.embargo)
        for combo in self.combinations:
            spans, embs = [], []
            for g in combo:
                s, e = int(a[groups[g]].min()), int(b[groups[g]].max())
                spans.append((s, e))
                embs.append(_embargo_end(a_s, int(pos_groups[g][-1]), e,
                                         self.embargo_pct, self.embargo_bars, td))
            test_idx = np.concatenate([groups[g] for g in combo])
            mask = _train_mask(a, b, spans, embs)
            mask[test_idx] = False
            yield np.flatnonzero(mask), np.sort(test_idx), combo

    def path_map(self) -> List[List[Tuple[int, int]]]:
        """For each path, list of (split_index, group) for groups 0..N-1."""
        seen: Dict[int, List[int]] = {g: [] for g in range(self.n_groups)}
        for si, combo in enumerate(self.combinations):
            for g in combo:
                seen[g].append(si)
        return [[(seen[g][p], g) for g in range(self.n_groups)] for p in range(self.n_paths)]

    def assemble_paths(self, predictions_by_split: Sequence[Dict[int, object]]
                       ) -> List[Dict[int, object]]:
        """Rebuild backtest paths.

        predictions_by_split[s] is a mapping {group: predictions} for the test
        groups of split s (split order = ``split()`` order). Returns n_paths
        dicts {group: predictions}; each group appears exactly once per path.
        """
        if len(predictions_by_split) != self.n_splits:
            raise ValueError("predictions_by_split must have one entry per split")
        return [{g: predictions_by_split[si][g] for si, g in pm} for pm in self.path_map()]


def purged_walk_forward(
    t0: TimeLike, t1: TimeLike, train_span: Span, test_span: Span,
    step: Optional[Span] = None, embargo: Optional[Span] = None,
    expanding: bool = False,
) -> Iterator[Tuple[np.ndarray, np.ndarray]]:
    """Walk-forward windows in calendar time (numbers = days).

    Test window = events with t0 in [ts, ts+test_span); train = events with
    t0 >= train start (rolling: ts-train_span; expanding: first t0) whose label
    END is strictly before ts - embargo. Hence no train label ends after test
    start. First ts = first t0 + train_span; ts advances by ``step`` (default
    test_span). Windows with empty train or test are skipped.
    """
    a, b = _prep(t0, t1)
    if len(a) == 0:
        return
    tr, te = _td_ns(train_span), _td_ns(test_span)
    st = _td_ns(step) if step is not None else te
    emb = _td_ns(embargo)
    if tr <= 0 or te <= 0 or st <= 0:
        raise ValueError("spans and step must be positive")
    first, last = int(a.min()), int(a.max())
    ts = first + tr
    while ts <= last:
        test_mask = (a >= ts) & (a < ts + te)
        train_mask = (b < ts - emb) & ((a >= first) if expanding else (a >= ts - tr))
        tr_idx, te_idx = np.flatnonzero(train_mask), np.flatnonzero(test_mask)
        if len(tr_idx) and len(te_idx):
            yield tr_idx, te_idx
        ts += st


def assert_no_leakage(
    train_idx: Sequence[int], test_idx: Sequence[int], t0: TimeLike, t1: TimeLike,
    embargo: Optional[Span] = None,
) -> None:
    """Raise AssertionError if any train interval overlaps a test interval, or
    (when ``embargo`` given) a train event starts within ``embargo`` after the
    end of a test interval. Time-based across all symbols."""
    a, b = _prep(t0, t1)
    tr, te = np.asarray(train_idx, int), np.asarray(test_idx, int)
    if len(tr) == 0 or len(te) == 0:
        return
    if np.intersect1d(tr, te).size:
        raise AssertionError("train and test share sample indices")
    # merge overlapping test intervals into disjoint sorted [s, e]
    o = np.argsort(a[te], kind="stable")
    ss, ee = a[te][o], b[te][o]
    ms, me = [int(ss[0])], [int(ee[0])]
    for s, e in zip(ss[1:], ee[1:]):
        if s <= me[-1]:
            me[-1] = max(me[-1], int(e))
        else:
            ms.append(int(s))
            me.append(int(e))
    ms, me = np.array(ms), np.array(me)
    ta, tb = a[tr], b[tr]
    k = np.searchsorted(ms, tb, side="right") - 1  # last interval starting <= train end
    bad = (k >= 0) & (me[np.clip(k, 0, None)] >= ta)
    if bad.any():
        raise AssertionError(f"{int(bad.sum())} train events overlap test intervals (leakage)")
    emb = _td_ns(embargo)
    if emb > 0:
        k = np.searchsorted(me, ta, side="left") - 1  # last interval ending < train start
        bad = (k >= 0) & (ta <= me[np.clip(k, 0, None)] + emb)
        if bad.any():
            raise AssertionError(f"{int(bad.sum())} train events inside embargo (leakage)")
