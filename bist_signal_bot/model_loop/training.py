"""Thin intraday training path: leak-free CPCV OOS evaluation -> final fit -> CandidateGate -> registry.

Research/paper only. A model is NEVER promoted automatically: the best status this module
assigns is CANDIDATE (gate verdict CANDIDATE); everything else is WATCH with an explicit warning.
No real order is ever sent.
"""
from __future__ import annotations

import hashlib
import json
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import numpy as np
import pandas as pd

from bist_signal_bot.core.logging_setup import get_logger
from bist_signal_bot.edge_validation import stats as st
from bist_signal_bot.edge_validation.costs import IntradayCostModel
from bist_signal_bot.edge_validation.cv import CombinatorialPurgedCV, assert_no_leakage
from bist_signal_bot.edge_validation.gate import CandidateGate, GateConfig, _day, daily_series
from bist_signal_bot.model_loop.features import FEATURE_COLUMNS, build_features, build_panel, to_end_ts
from bist_signal_bot.model_loop.interface import NO_ORDER, TrainedModelInfo

logger = get_logger(__name__)

KINDS = ("hgb", "logreg")
MIN_REGISTRY_WARNING = "gate: {v} — no proven edge"


def _setting(settings, key, default):
    try:
        v = getattr(settings, key)
        return default if v is None else v
    except AttributeError:
        return default


# ----------------------------------------------------------------------------- models
def _make_base(kind: str, seed: int, class_weight: Optional[str]):
    if kind == "hgb":
        from sklearn.ensemble import HistGradientBoostingClassifier
        return HistGradientBoostingClassifier(
            max_iter=120, learning_rate=0.05, max_depth=3, min_samples_leaf=100, l2_regularization=1.0,
            early_stopping=False, class_weight=class_weight, random_state=seed)
    if kind == "logreg":
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        return make_pipeline(StandardScaler(), LogisticRegression(
            C=0.1, max_iter=500, class_weight=class_weight, random_state=seed))
    raise ValueError(f"unknown model kind {kind!r}; choose from {KINDS}")


def _calibrator(base):
    from sklearn.calibration import CalibratedClassifierCV
    try:
        from sklearn.frozen import FrozenEstimator
        return CalibratedClassifierCV(FrozenEstimator(base), method="sigmoid")
    except ImportError:  # pragma: no cover - sklearn < 1.6
        return CalibratedClassifierCV(base, method="sigmoid", cv="prefit")


def fit_calibrated(*a, **k):
    # single OpenMP thread: HGB is dramatically slower under thread oversubscription here
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        return _fit_calibrated(*a, **k)


def _fit_calibrated(kind: str, X: pd.DataFrame, y: np.ndarray, t0: pd.Series, t1: pd.Series,
                   seed: int, class_weight: Optional[str] = None, cal_frac: float = 0.2):
    """Fit base on the earlier (1-cal_frac) of the time-ordered data, sigmoid-calibrate on the rest.

    Base-train events whose label window reaches into the calibration block are purged.
    """
    order = np.argsort(pd.DatetimeIndex(t0).asi8, kind="stable")
    X, y, t0, t1 = X.iloc[order], np.asarray(y)[order], pd.Series(t0).iloc[order], pd.Series(t1).iloc[order]
    n = len(X)
    cut = int(n * (1 - cal_frac))
    cal_start = t0.iloc[cut]
    keep = np.flatnonzero((np.arange(n) < cut) & (t1 < cal_start).to_numpy())
    cal_idx = np.arange(cut, n)
    base = _make_base(kind, seed, class_weight)
    if len(np.unique(y[keep])) < 2:
        raise ValueError("training block has a single class")
    base.fit(X.iloc[keep], y[keep])
    if len(cal_idx) < 50 or len(np.unique(y[cal_idx])) < 2:
        return base
    cal = _calibrator(base)
    cal.fit(X.iloc[cal_idx], y[cal_idx])
    return cal


def _proba(model, X: pd.DataFrame) -> np.ndarray:
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        return np.asarray(model.predict_proba(X)[:, 1], dtype=float)


# ----------------------------------------------------------------------------- metrics
def calibration_error(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    """Expected calibration error with equal-width bins."""
    p, y = np.asarray(p, float), np.asarray(y, float)
    b = np.minimum((p * bins).astype(int), bins - 1)
    ece = 0.0
    for k in range(bins):
        m = b == k
        if m.any():
            ece += m.mean() * abs(p[m].mean() - y[m].mean())
    return float(ece)


def prob_metrics(p: np.ndarray, y: np.ndarray) -> Dict[str, float]:
    from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    y = np.asarray(y, int)
    auc = float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else float("nan")
    return {"auc": auc, "brier": float(brier_score_loss(y, p)),
            "log_loss": float(log_loss(y, p, labels=[0, 1])), "calibration_error": calibration_error(p, y),
            "base_rate": float(y.mean())}


# ----------------------------------------------------------------------------- events
def select_events(panel: pd.DataFrame, p: np.ndarray, thr: float, notional: float) -> pd.DataFrame:
    """Long-only events where p > thr, non-overlapping per symbol (greedy by t0)."""
    cols = ["t0", "t1", "symbol", "gross_ret", "price", "order_value", "bar_value_try"]
    sel = panel.loc[np.asarray(p) > thr, ["t0", "t1", "symbol", "ret", "price", "bar_value_try"]]
    if len(sel) == 0:
        return pd.DataFrame(columns=cols)
    sel = sel.sort_values(["symbol", "t0"], kind="stable")
    keep, last_sym, last_end = [], None, None
    for pos, (sym, a, b) in enumerate(zip(sel["symbol"], sel["t0"], sel["t1"])):
        if sym != last_sym or a >= last_end:
            keep.append(pos)
            last_sym, last_end = sym, b
    sel = sel.iloc[keep].sort_values("t0", kind="stable").reset_index(drop=True)
    return pd.DataFrame({"t0": sel["t0"], "t1": sel["t1"], "symbol": sel["symbol"],
                         "gross_ret": sel["ret"].to_numpy(float), "price": sel["price"].to_numpy(float),
                         "order_value": float(notional), "bar_value_try": sel["bar_value_try"].to_numpy(float)})


def fingerprint(symbols: Sequence[str], panel: pd.DataFrame, interval: str, horizon: int) -> str:
    meta = {"symbols": sorted(symbols), "interval": interval, "horizon": horizon, "rows": int(len(panel)),
            "t0_min": str(panel["t0"].min()) if len(panel) else "", "t1_max": str(panel["t1"].max()) if len(panel) else ""}
    return hashlib.sha256(json.dumps(meta, sort_keys=True).encode()).hexdigest()


# ----------------------------------------------------------------------------- registry
def make_registry(settings=None):
    from bist_signal_bot.config.settings import get_settings
    from bist_signal_bot.model_registry.registry import LocalModelRegistry
    from bist_signal_bot.model_registry.storage import ModelRegistryStore
    from bist_signal_bot.storage.paths import get_data_dir
    settings = settings or get_settings()
    base = get_data_dir(settings) / str(_setting(settings, "MODEL_REGISTRY_DIR_NAME", "model_registry"))
    return LocalModelRegistry(settings, ModelRegistryStore(settings, base_dir=base))


def models_dir(settings=None) -> Path:
    from bist_signal_bot.storage.paths import get_data_dir
    d = get_data_dir(settings) / "model_loop" / "models"
    d.mkdir(parents=True, exist_ok=True)
    return d


def latest_oos_net_sharpe(model_id: str, registry=None, settings=None) -> Optional[float]:
    registry = registry or make_registry(settings)
    rec = registry.get_model(model_id)
    if rec is None:
        return None
    v = rec.metadata.get("oos_net_sharpe_annual")
    return None if v is None else float(v)


# ----------------------------------------------------------------------------- train
def train_model(archive, symbols: Sequence[str], interval: str, as_of, settings=None,
                horizon_bars: Optional[int] = None, model_kind: Optional[str] = None, registry=None,
                ledger=None, register: bool = True, prob_threshold: Optional[float] = None,
                seed: Optional[int] = None, min_train_events: Optional[int] = None,
                class_weight: Optional[str] = None, cost_model: Optional[IntradayCostModel] = None,
                gate: Optional[CandidateGate] = None, n_groups: int = 6, n_test_groups: int = 2,
                embargo_days: int = 1) -> TrainedModelInfo:
    if settings is None:
        from bist_signal_bot.config.settings import get_settings
        settings = get_settings()
    horizon_bars = int(horizon_bars if horizon_bars is not None else _setting(settings, "MODEL_LOOP_HORIZON_BARS", 4))
    kind = str(model_kind or _setting(settings, "MODEL_LOOP_KIND", "hgb")).lower()
    thr = float(prob_threshold if prob_threshold is not None else _setting(settings, "MODEL_LOOP_PROB_THRESHOLD", 0.55))
    seed = int(seed if seed is not None else _setting(settings, "MODEL_LOOP_SEED", 42))
    min_ev = int(min_train_events if min_train_events is not None else _setting(settings, "MODEL_LOOP_MIN_TRAIN_EVENTS", 2000))
    if kind not in KINDS:
        raise ValueError(f"unknown model kind {kind!r}; choose from {KINDS}")
    as_of_ts = to_end_ts(as_of)
    cost_model = cost_model or IntradayCostModel.from_settings(settings)
    notional = float(_setting(settings, "EDGE_NOTIONAL_TRY", 10000.0))

    panel = build_panel(archive, symbols, interval, None, as_of, horizon_bars)
    if len(panel) < max(min_ev, n_groups * 2):
        raise ValueError(f"insufficient training events: {len(panel)} < {min_ev} (interval={interval})")
    assert panel["t1"].max() <= as_of_ts, "label window crosses as_of (leak)"
    assert (panel["t1"] >= panel["t0"]).all()
    X, y = panel[FEATURE_COLUMNS], panel["y"].to_numpy(int)
    fp = fingerprint(symbols, panel, interval, horizon_bars)

    # ---- combinatorial purged CV: OOS probability for every event on every path
    cv = CombinatorialPurgedCV(n_groups, n_test_groups, embargo=pd.Timedelta(days=embargo_days))
    groups = cv.group_indices(panel["t0"])
    group_of = np.empty(len(panel), dtype=int)
    for g, idx in enumerate(groups):
        group_of[idx] = g
    preds, n_checked = [], 0
    for train, test, combo in cv.split(panel["t0"], panel["t1"]):
        assert_no_leakage(train, test, panel["t0"], panel["t1"], embargo=pd.Timedelta(days=embargo_days))
        n_checked += 1
        model = fit_calibrated(kind, X.iloc[train], y[train], panel["t0"].iloc[train], panel["t1"].iloc[train],
                               seed, class_weight)
        entry = {}
        for g in combo:
            gi = groups[g]  # whole group is in the test set
            entry[g] = (gi, _proba(model, X.iloc[gi]))
        preds.append(entry)
    paths = cv.assemble_paths(preds)
    p_paths = []
    for path in paths:
        p = np.full(len(panel), np.nan)
        for g, (gi, pr) in path.items():
            p[gi] = pr
        p_paths.append(p)
    P = np.vstack(p_paths)
    p_oos = np.nanmean(P, axis=0)
    per_path = [prob_metrics(p, y) for p in p_paths]
    metrics: Dict[str, Any] = {k: float(np.nanmean([m[k] for m in per_path])) for k in per_path[0]}
    metrics["auc_path_std"] = float(np.nanstd([m["auc"] for m in per_path]))
    metrics["auc_path_min"] = float(np.nanmin([m["auc"] for m in per_path]))
    metrics["n_paths"] = len(paths)
    metrics["cpcv_splits_checked"] = n_checked
    metrics["auc_mean_prob"] = prob_metrics(p_oos, y)["auc"]

    # ---- OOS signal events -> honest trials (threshold grid, all recorded) -> gate
    if ledger is None:
        from bist_signal_bot.edge_validation.ledger import TrialLedger
        ledger = TrialLedger(settings=settings)
    if gate is None:
        gate = CandidateGate(GateConfig.from_settings(settings), settings=settings, cost_model=cost_model)
    family = f"ml_{kind}"
    days = _day(pd.DatetimeIndex(panel["t1"])).unique().sort_values()
    events_by_trial: Dict[str, pd.DataFrame] = {}
    best, best_sr, most, most_n = None, -np.inf, None, -1
    for t in sorted({round(thr - 0.05, 4), round(thr, 4), round(thr + 0.05, 4)}):
        tid = f"{family}|{interval}|h{horizon_bars}|thr{t:.3f}|asof{pd.Timestamp(as_of_ts).date()}|{fp[:10]}|s{seed}"
        ev = select_events(panel, p_oos, t, notional)
        events_by_trial[tid] = ev
        if len(ev) > most_n:
            most, most_n = tid, len(ev)
        net = gate._net(ev).dropna(subset=["net_ret"]) if len(ev) else ev
        params = {"thr": t, "horizon_bars": horizon_bars, "kind": kind, "seed": seed}
        universe = ",".join(sorted(symbols))
        if len(net) < gate.config.min_events:
            ledger.record_trial(tid, family, params, interval, universe, None, family, "failed")
            continue
        daily = daily_series(net, "net_ret", days)
        ledger.record_trial(tid, family, params, interval, universe, daily, family, "ok")
        sr = float(st.sharpe(daily.to_numpy()))
        if np.isfinite(sr) and sr > best_sr:
            best, best_sr = tid, sr
    selected = best if best is not None else most
    report = gate.evaluate(family, selected, events_by_trial, ledger, interval, trading_days=days)
    sel_ev = events_by_trial.get(selected)
    sel_thr = thr
    if selected is not None:
        sel_thr = float(selected.split("|thr")[1].split("|")[0])
    if sel_ev is not None and len(sel_ev):
        net = gate._net(sel_ev).dropna(subset=["net_ret"])
        metrics["n_signals"] = int(len(net))
        metrics["hit_rate"] = float((net["gross_ret"] > 0).mean()) if len(net) else None
        metrics["mean_net_ret_bps"] = float(net["net_ret"].mean() * 1e4) if len(net) else None
    else:
        metrics.update(n_signals=0, hit_rate=None, mean_net_ret_bps=None)
    metrics["selected_threshold"] = sel_thr
    metrics["oos_net_sharpe_annual"] = report.net_sharpe_annual
    metrics["dsr"] = report.dsr
    metrics["gate_failed_criteria"] = list(report.failed_criteria)
    metrics["gate_n_trials_ledger"] = report.n_trials_ledger
    verdict = report.verdict

    # ---- final fit on everything up to as_of (calibrated)
    final = fit_calibrated(kind, X, y, panel["t0"], panel["t1"], seed, class_weight)
    trained_through = str(panel["t1"].max())
    day_tag = pd.Timestamp(as_of_ts).strftime("%Y%m%d")
    model_id = f"mloop_{kind}_{interval}_{day_tag}_{fp[:8]}"
    warnings = [] if verdict == "CANDIDATE" else [MIN_REGISTRY_WARNING.format(v=verdict)]

    info = TrainedModelInfo(model_id=model_id, kind=kind, interval=interval, trained_through=trained_through,
                            n_events=int(len(panel)), oos_metrics=metrics, gate_verdict=verdict,
                            artifact_path="", registry_status="", warnings=warnings)
    if not register:
        return info

    registry = registry or make_registry(settings)
    existing = registry.get_model(model_id)
    if existing is not None:
        model_id = f"{model_id}_{uuid.uuid4().hex[:6]}"
        info.model_id = model_id
    import joblib
    path = models_dir(settings) / f"{model_id}.joblib"
    joblib.dump({"model": final, "feature_names": list(FEATURE_COLUMNS), "kind": kind, "interval": interval,
                 "horizon_bars": horizon_bars, "seed": seed, "prob_threshold": sel_thr,
                 "trained_through": trained_through, "fingerprint": fp}, path)
    info.artifact_path = str(path)
    _register(registry, settings, info, report, fp, symbols, panel, thr, seed, horizon_bars, class_weight)
    return info


def _register(registry, settings, info: TrainedModelInfo, report, fp, symbols, panel, thr, seed,
              horizon_bars, class_weight) -> None:
    from bist_signal_bot.model_registry.model_cards import ModelCardBuilder
    from bist_signal_bot.model_registry.models import (
        ModelArtifact, ModelArtifactFormat, ModelGovernanceStatus, ModelKind, ModelRecord, ModelRegistryStatus)

    cand = info.gate_verdict == "CANDIDATE"
    status = ModelRegistryStatus.CANDIDATE if cand else ModelRegistryStatus.WATCH  # never ACTIVE_RESEARCH
    info.registry_status = status.value
    now = datetime.now(timezone.utc)
    window = f"{panel['t0'].min()} .. {panel['t1'].max()}"
    meta = {"interval": info.interval, "kind_short": info.kind, "horizon_bars": horizon_bars,
            "prob_threshold": thr, "seed": seed, "class_weight": class_weight, "training_window": window,
            "trained_through": info.trained_through, "n_events": info.n_events,
            "symbols": sorted(symbols), "fingerprint": fp, "feature_names": list(FEATURE_COLUMNS),
            "oos_metrics": info.oos_metrics, "gate_verdict": info.gate_verdict,
            "gate_failed_criteria": list(report.failed_criteria), "gate_report_path": report.report_path,
            "oos_net_sharpe_annual": info.oos_metrics.get("oos_net_sharpe_annual"),
            "artifact_path": info.artifact_path, "auto_promoted": False, "no_real_order_sent": True}
    rec = ModelRecord(
        model_id=info.model_id, model_name=f"intraday_{info.kind}_{info.interval}", model_kind=ModelKind.CLASSIFIER,
        version=f"{pd.Timestamp(info.trained_through).strftime('%Y%m%d')}-s{seed}", created_at=now,
        status=status, feature_set_version="intraday_v1",
        dataset_refs=[f"bar_archive:{info.interval}:{fp[:16]}"], owner_module="model_loop",
        tags=["intraday", "model_loop", f"gate_{info.gate_verdict.lower()}"] + ([] if cand else ["baseline"]),
        warnings=list(info.warnings), metadata=meta)
    store = registry.store
    # NOTE: ModelArtifactManager() currently fails to construct (PathGuard signature mismatch in
    # model_registry/artifacts.py), so the same ModelArtifact record is built directly.
    try:
        ap = Path(info.artifact_path)
        art = ModelArtifact(
            artifact_id=f"art_{now.strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}", model_id=info.model_id,
            path=str(ap), artifact_format=ModelArtifactFormat.JOBLIB, created_at=now, size_bytes=ap.stat().st_size,
            checksum=hashlib.sha256(ap.read_bytes()).hexdigest(), loadable=True)
        store.append_artifact(art)
        rec.artifact_id = art.artifact_id
    except Exception as exc:  # the joblib file itself exists; registry entry is best-effort
        rec.warnings.append(f"artifact registry entry failed: {exc}")
        info.warnings.append(rec.warnings[-1])
    card = ModelCardBuilder(settings, store).build_card(
        rec, input_features=list(FEATURE_COLUMNS),
        training_data_summary=(f"Intraday {info.interval} bars, {len(symbols)} symbols, window {window}, "
                               f"{info.n_events} events, fingerprint {fp[:16]}, seed {seed}."))
    m = info.oos_metrics
    card.validation_summary = (
        f"CPCV(N=6,k=2,embargo=1d) OOS: AUC={m.get('auc'):.4f}, Brier={m.get('brier'):.4f}, "
        f"logloss={m.get('log_loss'):.4f}, ECE={m.get('calibration_error'):.4f}, hit={m.get('hit_rate')}, "
        f"mean_net_bps={m.get('mean_net_ret_bps')}. CandidateGate verdict: {info.gate_verdict} "
        f"(failed: {', '.join(report.failed_criteria) or 'none'}). Not proof of future performance.")
    card.calibration_summary = "Sigmoid (Platt) calibration on a time-ordered held-out tail of the training window."
    card.governance_status = {"CANDIDATE": ModelGovernanceStatus.WATCH,
                              "REJECTED": ModelGovernanceStatus.FAIL}.get(info.gate_verdict,
                                                                          ModelGovernanceStatus.INSUFFICIENT_DATA)
    card.warnings.extend(info.warnings)
    card.metadata.update({"gate_verdict": info.gate_verdict, "training_window": window, "fingerprint": fp})
    store.append_model_card(card)
    rec.model_card_id = card.card_id
    registry.register_model(rec, confirm=True)


# ----------------------------------------------------------------------------- inference
def load_artifact(model_id: str, registry=None, settings=None) -> dict:
    import joblib
    registry = registry or make_registry(settings)
    rec = registry.get_model(model_id)
    if rec is None:
        raise KeyError(f"model not found: {model_id}")
    return joblib.load(rec.metadata["artifact_path"])


def predict_proba(model_id: str, bars_by_symbol: Dict[str, pd.DataFrame], registry=None,
                  settings=None) -> Dict[str, float]:
    """P(forward return > 0) at each symbol's LATEST bar (features use data <= that bar only)."""
    art = load_artifact(model_id, registry, settings)
    out: Dict[str, float] = {}
    for sym, bars in bars_by_symbol.items():
        if bars is None or len(bars) < 60:
            continue
        row = build_features(bars, art["interval"]).iloc[[-1]][art["feature_names"]]
        if row.isna().any().any():
            continue
        out[sym] = float(_proba(art["model"], row)[0])
    return out


class IntradayModelTrainer:
    """Implements interface.TrainerProtocol around train_model."""

    def __init__(self, archive, symbols, interval, settings=None, registry=None, ledger=None, **kw):
        self.archive, self.symbols, self.interval = archive, list(symbols), interval
        self.settings, self.registry, self.ledger, self.kw = settings, registry, ledger, kw

    def train(self, as_of) -> TrainedModelInfo:
        return train_model(self.archive, self.symbols, self.interval, as_of, self.settings,
                           registry=self.registry, ledger=self.ledger, **self.kw)

    def latest_oos_net_sharpe(self, model_id: str) -> Optional[float]:
        return latest_oos_net_sharpe(model_id, self.registry, self.settings)
