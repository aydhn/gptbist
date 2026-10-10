"""Daily (multi-day) model lifecycle glue: train -> SAME CandidateGate excess evaluation -> registry -> drift/challenger.

Research/paper only. No real order is ever sent. A model is NEVER a champion automatically: ``daily_train`` registers
CANDIDATE (gate CANDIDATE) or WATCH (anything else); ``ModelLifecycle.promote`` additionally requires
gate_verdict == CANDIDATE, preflight, kill switch and an explicit ``confirm=True``.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.xsection import DailyContext
from bist_signal_bot.model_loop.daily_features import FEATURE_COLUMNS, get_feature_panel
from bist_signal_bot.model_loop.daily_training import cpcv_report, oof_report
from bist_signal_bot.model_loop.drift_monitor import DriftDecision, DriftMonitor
from bist_signal_bot.model_loop.interface import NO_ORDER, TrainedModelInfo

DEFAULT_RETRAIN_DAYS = 7
TAG_DAILY = "daily"
FAMILY_OF = {"logit": "ml_xs_logit", "hgb": "ml_xs_hgb", "meta": "ml_xs_meta"}
DEFAULT_PARAMS = {"logit": {"C": 0.1, "retrain_every": 20}, "hgb": {"max_depth": 2, "retrain_every": 60},
                  "meta": {"primary": "xs_momentum_1_6", "K": 30, "retrain_every": 60}}


def ctx_as_of(ctx: DailyContext, as_of) -> DailyContext:
    """Context with only the sessions <= as_of (a causal view; used so a model can never see later data)."""
    ts = pd.Timestamp(as_of)
    if ts.tzinfo is not None:  # lifecycle passes UTC-aware datetimes; the session index is tz-naive
        ts = ts.tz_convert("UTC").tz_localize(None)
    n = int(np.searchsorted(ctx.index.values, np.datetime64(ts.normalize()), side="right"))
    return ctx if n >= len(ctx.index) else ctx.truncate(n)


def _setting(settings, key, default):
    try:
        v = getattr(settings, key)
        return default if v is None else v
    except AttributeError:
        return default


def due_for_retrain(registry, today, every_days: int = DEFAULT_RETRAIN_DAYS) -> tuple:
    """(due, reason): True when no daily model exists or the newest one was trained >= every_days ago."""
    stamps = []
    for r in registry.list_models():
        if TAG_DAILY in (r.tags or []) and r.owner_module == "model_loop":
            s = (r.metadata or {}).get("loop_as_of") or (r.metadata or {}).get("trained_at")
            if s:
                stamps.append(pd.Timestamp(s).tz_localize(None) if pd.Timestamp(s).tzinfo else pd.Timestamp(s))
    if not stamps:
        return True, "no daily model registered"
    last = max(stamps)
    age = (pd.Timestamp(today).tz_localize(None) if pd.Timestamp(today).tzinfo else pd.Timestamp(today)) - last
    if age >= pd.Timedelta(days=every_days):
        return True, f"last daily training {last.date()} is {age.days}d old (>= {every_days}d)"
    return False, f"last daily training {last.date()} is {age.days}d old (< {every_days}d)"


class DailyModelTrainer:
    """Implements ``interface.TrainerProtocol`` for the daily ML path."""

    def __init__(self, ctx: DailyContext, ledger, kind: str = "logit", horizon: int = 10, settings=None,
                 registry=None, params: Optional[dict] = None, top_n: int = 8, models_dir: Optional[Path] = None,
                 scenarios=("placeholder_commission", "zero_commission"), cpcv: bool = False,
                 report_dir=None, save_report: bool = False, knobs: Optional[dict] = None, gate=None):
        if kind not in FAMILY_OF:
            raise ValueError(f"kind must be in {sorted(FAMILY_OF)}")
        self.ctx, self.ledger, self.kind, self.horizon = ctx, ledger, kind, int(horizon)
        self.settings, self.registry = settings, registry
        self.params = dict(params or DEFAULT_PARAMS[kind])
        self.knobs = dict(knobs or {})  # non-grid knobs (embargo, min_train_rows, ...)
        self.top_n, self.models_dir, self.scenarios, self.cpcv = top_n, models_dir, tuple(scenarios), cpcv
        self.report_dir, self.save_report = report_dir, save_report
        self.gate = gate
        self.last: Dict[str, Any] = {}

    def latest_oos_net_sharpe(self, model_id: str) -> Optional[float]:
        rec = self.registry.get_model(model_id) if self.registry is not None else None
        v = None if rec is None else (rec.metadata or {}).get("oos_net_sharpe_annual")
        return None if v is None else float(v)

    def train(self, as_of) -> TrainedModelInfo:
        from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
        from bist_signal_bot.edge_validation.runner_daily import run_family_daily
        ctx = ctx_as_of(self.ctx, as_of)
        fam = DAILY_FAMILIES[FAMILY_OF[self.kind]]
        p = {**self.params, **self.knobs, "label_h": self.horizon}
        wf = fam.wf(ctx, p, fit_final=True)
        metrics: Dict[str, Any] = {"oof": oof_report(wf)}
        if self.cpcv:
            from bist_signal_bot.edge_validation.families_daily_ml import _cfg
            cfg = wf.config
            prim = fam.primary_scores(ctx, p) if self.kind == "meta" else None
            metrics["cpcv"] = cpcv_report(ctx, cfg, primary=prim, top_k=int(p.get("K", 30)))
        grid = {k: [v] for k, v in {**self.params, **self.knobs}.items()}
        res = run_family_daily(fam, ctx, [self.horizon], grid, self.top_n, self.ledger, gate=self.gate,
                               scenarios=self.scenarios, settings=self.settings, benchmark="ew_universe", save_report=self.save_report,
                               report_dir=self.report_dir)
        verdict = res.verdict
        rep = res.report
        prim_s = rep["scenarios"][rep["candidacy_scenario"]]
        oof = metrics["oof"]
        om = {"net_sharpe": rep.get("net_sharpe_annual"), "oos_net_sharpe_annual": rep.get("net_sharpe_annual"),
              "excess_sharpe_vs_ew": prim_s.get("excess_sharpe_vs_ew"), "dsr": rep.get("dsr"),
              "auc": oof.get("auc"), "brier": oof.get("brier"), "log_loss": oof.get("log_loss"),
              "calibration_error": oof.get("calibration_error"), "ic_mean": oof.get("ic_mean"),
              "ic_ir": oof.get("ic_ir"), "gate_failed_criteria": list(prim_s.get("failed_criteria") or []),
              "n_trials_ledger": rep.get("n_trials_ledger")}
        trained_through = str(ctx.index[-1].date())
        fp8 = hashlib.sha256(f"{self.kind}|{self.horizon}|{len(ctx.symbols)}|{trained_through}|{wf.config.as_json()}"
                             .encode()).hexdigest()[:8]
        model_id = f"mloop_daily_{self.kind}_h{self.horizon}_{trained_through.replace('-', '')}_{fp8}"
        info = TrainedModelInfo(model_id=model_id, kind=f"daily_{self.kind}", interval="1d",
                                trained_through=trained_through, n_events=int(oof.get("n_oof") or 0),
                                oos_metrics=om, gate_verdict=verdict,
                                warnings=[] if verdict == "CANDIDATE" else [f"gate: {verdict} - no proven edge"])
        self.last = {"wf": wf, "metrics": metrics, "report": rep, "result": res}
        if self.registry is not None:
            self._register(info, wf, p, metrics, rep, ctx)
        return info

    def _register(self, info: TrainedModelInfo, wf, p: dict, metrics: dict, rep: dict, ctx: DailyContext) -> None:
        from bist_signal_bot.model_registry.models import ModelKind, ModelRecord, ModelRegistryStatus
        rec0 = self.registry.get_model(info.model_id)
        if rec0 is not None:
            info.model_id = f"{info.model_id}_{uuid.uuid4().hex[:6]}"
        cand = info.gate_verdict == "CANDIDATE"
        status = ModelRegistryStatus.CANDIDATE if cand else ModelRegistryStatus.WATCH  # never ACTIVE_RESEARCH
        info.registry_status = status.value
        art_path = ""
        if self.models_dir is not None and wf.final_model is not None:
            import joblib
            Path(self.models_dir).mkdir(parents=True, exist_ok=True)
            art_path = str(Path(self.models_dir) / f"{info.model_id}.joblib")
            joblib.dump({"model": wf.final_model, "calibrator": wf.final_calibrator,
                         "feature_names": list(wf.feature_names), "kind": self.kind, "params": p,
                         "horizon": self.horizon, "trained_through": info.trained_through,
                         "symbols": list(ctx.symbols)}, art_path)
            info.artifact_path = art_path
        now = datetime.now(timezone.utc)
        meta = {"loop_kind": f"daily_{self.kind}", "interval": "1d", "params": {k: v for k, v in p.items()},
                "horizon": self.horizon, "trained_through": info.trained_through, "trained_at": now.isoformat(),
                "loop_as_of": pd.Timestamp(info.trained_through).tz_localize("UTC").isoformat(),
                "n_events": info.n_events, "gate_verdict": info.gate_verdict, "oos_metrics": dict(info.oos_metrics),
                "oos_net_sharpe_annual": info.oos_metrics.get("oos_net_sharpe_annual"),
                "gate_failed_criteria": info.oos_metrics.get("gate_failed_criteria"),
                "retrain_blocks": len(wf.blocks), "feature_names": list(wf.feature_names),
                "symbols_n": len(ctx.symbols), "benchmark": "ew_universe", "artifact_path": art_path,
                "auto_promoted": False, "no_real_order_sent": True}
        rec = ModelRecord(model_id=info.model_id, model_name=f"daily_{self.kind}_h{self.horizon}",
                          model_kind=ModelKind.CLASSIFIER, version=info.trained_through.replace("-", ""),
                          created_at=now, status=status, feature_set_version="daily_xs_v1",
                          owner_module="model_loop",
                          tags=[TAG_DAILY, "model_loop", f"gate_{info.gate_verdict.lower()}"] + ([] if cand else ["baseline"]),
                          warnings=list(info.warnings), metadata=meta)
        self.registry.register_model(rec, confirm=True)


# ----------------------------------------------------------------------------- drift
def _sample(df: pd.DataFrame, cap: int, seed: int = 0) -> pd.DataFrame:
    return df if len(df) <= cap else df.sample(cap, random_state=seed).sort_index()


def daily_drift_inputs(ctx: DailyContext, artifact: dict, ref_days: int = 250, cur_days: int = 60,
                       cap: int = 20000) -> tuple:
    """(ref_df, cur_df): rank-normalised feature rows + the model's score ('score' column) for the reference window
    (the ``ref_days`` sessions before the current window) and the current window (last ``cur_days`` sessions)."""
    fp = get_feature_panel(ctx)
    n = len(ctx.index)
    mdl, cal = artifact["model"], artifact.get("calibrator")
    names = list(artifact.get("feature_names") or FEATURE_COLUMNS)
    base = [c for c in names if c in FEATURE_COLUMNS]

    def window(a: int, b: int) -> pd.DataFrame:
        ii, jj = np.nonzero(fp.valid[a:b])
        X = fp.Z[a + ii, jj, :]
        df = pd.DataFrame(X[:, [FEATURE_COLUMNS.index(c) for c in base]], columns=base)
        if len(df):
            Xm = X if len(names) == len(FEATURE_COLUMNS) else np.concatenate([X, np.zeros((len(X), 1), np.float32)], axis=1)
            p = mdl.predict_p(Xm)
            df["score"] = cal.transform(p) if cal is not None else p
        return _sample(df, cap)

    cur = window(max(n - cur_days, 0), n)
    ref = window(max(n - cur_days - ref_days, 0), max(n - cur_days, 0))
    return ref, cur


class DailyDriftMonitor(DriftMonitor):
    """PSI/KS on rank-normalised features (as the base monitor) PLUS the score distribution: a score alert
    (PSI >= alert) on its own triggers retrain, because rank-normalised features rarely drift in marginal shape."""

    def check_features(self, ref_df, cur_df) -> DriftDecision:
        feat_cols = [c for c in ref_df.columns if c != "score"]
        base = super().check_features(ref_df[feat_cols], cur_df[[c for c in cur_df.columns if c != "score"]])
        if "score" in ref_df.columns and "score" in cur_df.columns:
            sc = super().check_features(ref_df[["score"]], cur_df[["score"]])
            sc.reasons = [r.replace("feature_drift", "score_drift") for r in sc.reasons]
            return DriftMonitor.combine(base, sc)
        return base


def make_data_provider(ctx: DailyContext, artifact_getter: Callable[[], Optional[dict]], **kw):
    """data_provider(as_of) for ``ModelLifecycle`` -> {ref_df, cur_df}."""
    def provider(as_of):
        art = artifact_getter()
        if art is None:
            return {}
        ref, cur = daily_drift_inputs(ctx_as_of(ctx, as_of), art, **kw)
        return {"ref_df": ref, "cur_df": cur}
    return provider
