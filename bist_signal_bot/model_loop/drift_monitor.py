"""Numpy-only drift tools for the model loop (PSI, two-sample KS, ADWIN).

Research/paper only. No real order is ever sent by anything in this module.

ADWIN variant: a *simple sliding-window* ADWIN (not the bucket/exponential
histogram compression of ADWIN2). The window keeps at most ``max_width``
recent elements; after each insert every admissible cut point is tested with
the variance-aware Hoeffding/Bernstein bound of Bifet & Gavalda (2007):

    eps_cut = sqrt(2/m * var * ln(2/d')) + 2/(3m) * ln(2/d'),
    m = 1 / (1/n0 + 1/n1),  d' = delta / ln(n)

and the older part of the window is dropped when |mean0 - mean1| > eps_cut.
Inputs are scaled by ``value_range`` so the bound holds for values in [0, 1].
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable

import numpy as np

NO_ORDER_MSG = "No real order sent."

SEVERITY_ORDER = {"none": 0, "warn": 1, "alert": 2}


def _clean(x: Iterable[float]) -> np.ndarray:
    a = np.asarray(x if hasattr(x, "__len__") else list(x), dtype=float).ravel()
    return a[np.isfinite(a)]


def psi(ref: Iterable[float], cur: Iterable[float], bins: int = 10) -> float:
    """Population Stability Index with reference-quantile bins."""
    r, c = _clean(ref), _clean(cur)
    if r.size == 0 or c.size == 0:
        return float("nan")
    edges = np.unique(np.quantile(r, np.linspace(0.0, 1.0, bins + 1)))
    if edges.size < 2:  # constant reference
        return 0.0 if np.all(c == r[0]) else float("inf")
    edges[0], edges[-1] = -np.inf, np.inf
    rp = np.histogram(r, bins=edges)[0] / r.size
    cp = np.histogram(c, bins=edges)[0] / c.size
    eps = 1e-6
    rp, cp = np.clip(rp, eps, None), np.clip(cp, eps, None)
    return float(np.sum((cp - rp) * np.log(cp / rp)))


def ks_statistic_pvalue(ref: Iterable[float], cur: Iterable[float]) -> tuple[float, float]:
    """Two-sample Kolmogorov-Smirnov statistic and asymptotic p-value."""
    r, c = np.sort(_clean(ref)), np.sort(_clean(cur))
    n1, n2 = r.size, c.size
    if n1 == 0 or n2 == 0:
        return float("nan"), float("nan")
    allv = np.concatenate([r, c])
    cdf1 = np.searchsorted(r, allv, side="right") / n1
    cdf2 = np.searchsorted(c, allv, side="right") / n2
    d = float(np.max(np.abs(cdf1 - cdf2)))
    ne = n1 * n2 / (n1 + n2)
    lam = (math.sqrt(ne) + 0.12 + 0.11 / math.sqrt(ne)) * d
    if lam < 1e-9:
        return d, 1.0
    s, sign = 0.0, 1.0
    for k in range(1, 101):
        term = sign * math.exp(-2.0 * k * k * lam * lam)
        s += term
        sign = -sign
        if abs(term) < 1e-12:
            break
    return d, float(min(1.0, max(0.0, 2.0 * s)))


class Adwin:
    """Simple sliding-window ADWIN (see module docstring)."""

    def __init__(self, delta: float = 0.002, max_width: int = 1000,
                 min_sub_window: int = 10, value_range: float = 1.0):
        self.delta = float(delta)
        self.max_width = int(max_width)
        self.min_sub_window = int(min_sub_window)
        self.value_range = float(value_range) or 1.0
        self._w: list[float] = []
        self.last_change_direction: int = 0  # -1: mean dropped, +1: mean rose

    @property
    def width(self) -> int:
        return len(self._w)

    @property
    def mean(self) -> float:
        return float(np.mean(self._w)) * self.value_range if self._w else 0.0

    def add_element(self, x: float) -> bool:
        self._w.append(float(x) / self.value_range)
        if len(self._w) > self.max_width:
            self._w.pop(0)
        return self._detect_and_shrink()

    def _detect_and_shrink(self) -> bool:
        changed = False
        while True:
            n = len(self._w)
            m = self.min_sub_window
            if n < 2 * m:
                return changed
            a = np.asarray(self._w)
            cs = np.concatenate([[0.0], np.cumsum(a)])
            cs2 = np.concatenate([[0.0], np.cumsum(a * a)])
            k = np.arange(m, n - m + 1)  # size of older part n0
            n0, n1 = k.astype(float), (n - k).astype(float)
            mean0 = cs[k] / n0
            mean1 = (cs[n] - cs[k]) / n1
            var = max(cs2[n] / n - (cs[n] / n) ** 2, 0.0)
            dd = math.log(2.0 * math.log(max(n, 3)) / self.delta)
            mh = 1.0 / (1.0 / n0 + 1.0 / n1)
            eps = np.sqrt(2.0 * var * dd / mh) + 2.0 * dd / (3.0 * mh)
            hit = np.abs(mean0 - mean1) > eps
            if not hit.any():
                return changed
            idx = int(np.nonzero(hit)[0][0])  # earliest cut
            cut = int(k[idx])
            self.last_change_direction = -1 if mean1[idx] < mean0[idx] else 1
            self._w = self._w[cut:]
            changed = True

    def reset(self) -> None:
        self._w = []
        self.last_change_direction = 0


@dataclass
class FeatureDriftFinding:
    feature: str
    psi: float
    ks_stat: float
    ks_pvalue: float
    severity: str  # none | warn | alert


@dataclass
class DriftDecision:
    retrain: bool
    reasons: list[str] = field(default_factory=list)
    severity: str = "none"
    findings: list[FeatureDriftFinding] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)
    no_real_order_sent: bool = True
    message: str = NO_ORDER_MSG


def _get(settings: Any, key: str, default: Any) -> Any:
    try:
        v = getattr(settings, key, default)
    except Exception:
        return default
    return default if v is None else v


class DriftMonitor:
    def __init__(self, settings: Any = None):
        self.psi_warn = float(_get(settings, "MODEL_LOOP_PSI_WARN", 0.1))
        self.psi_alert = float(_get(settings, "MODEL_LOOP_PSI_ALERT", 0.25))
        self.ks_alpha = float(_get(settings, "MODEL_LOOP_KS_ALPHA", 0.01))
        self.adwin_delta = float(_get(settings, "MODEL_LOOP_ADWIN_DELTA", 0.002))
        self.alert_frac = float(_get(settings, "MODEL_LOOP_FEATURE_ALERT_FRAC", 0.2))
        self.min_samples = 30

    def check_features(self, ref_df, cur_df) -> DriftDecision:
        findings: list[FeatureDriftFinding] = []
        cols = [c for c in ref_df.columns if c in cur_df.columns]
        for col in cols:
            try:
                r, c = _clean(ref_df[col].to_numpy(dtype=float)), _clean(cur_df[col].to_numpy(dtype=float))
            except (TypeError, ValueError):
                continue  # non-numeric
            if r.size < self.min_samples or c.size < self.min_samples:
                continue
            p = psi(r, c)
            d, pv = ks_statistic_pvalue(r, c)
            sev = "none"
            if p >= self.psi_alert:
                sev = "alert"
            elif p >= self.psi_warn or pv < self.ks_alpha:
                sev = "warn"
            findings.append(FeatureDriftFinding(str(col), p, d, pv, sev))
        n = len(findings)
        n_alert = sum(f.severity == "alert" for f in findings)
        n_warn = sum(f.severity == "warn" for f in findings)
        severity = "alert" if n_alert else ("warn" if n_warn else "none")
        reasons: list[str] = []
        retrain = False
        if n and n_alert / n >= self.alert_frac:
            retrain = True
            reasons.append(f"feature_drift: {n_alert}/{n} features PSI>={self.psi_alert}")
        elif n_alert:
            reasons.append(f"feature_drift_minor: {n_alert}/{n} features at alert (below retrain fraction)")
        return DriftDecision(retrain, reasons, severity, findings,
                             {"n_features": n, "n_alert": n_alert, "n_warn": n_warn})

    def check_performance(self, stream: Iterable[float], value_range: float = 1.0) -> DriftDecision:
        """stream: per-trade net returns or hit flags (0/1). Retrain only on a mean DROP."""
        ad = Adwin(delta=self.adwin_delta, value_range=value_range)
        drops = rises = 0
        n = 0
        for x in stream:
            n += 1
            if ad.add_element(float(x)):
                if ad.last_change_direction < 0:
                    drops += 1
                else:
                    rises += 1
        reasons: list[str] = []
        severity = "none"
        retrain = False
        if drops:
            retrain, severity = True, "alert"
            reasons.append(f"performance_degradation: ADWIN detected {drops} mean drop(s)")
        elif rises:
            severity = "warn"
            reasons.append("performance_shift_up: ADWIN detected improvement (no retrain)")
        return DriftDecision(retrain, reasons, severity, [],
                             {"n": n, "drops": drops, "rises": rises, "adwin_mean": ad.mean})

    @staticmethod
    def combine(*decisions: DriftDecision) -> DriftDecision:
        ds = [d for d in decisions if d is not None]
        sev = max((d.severity for d in ds), key=lambda s: SEVERITY_ORDER.get(s, 0), default="none")
        reasons = [r for d in ds for r in d.reasons]
        findings = [f for d in ds for f in d.findings]
        return DriftDecision(any(d.retrain for d in ds), reasons, sev, findings,
                             {"parts": [d.details for d in ds]})
