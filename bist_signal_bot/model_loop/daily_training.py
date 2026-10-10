"""Leak-free multi-day ML research path: excess-return labels, walk-forward retraining, calibration, CPCV report.

Research/paper only. No real order is ever sent. Nothing here promotes a model; the CandidateGate decides.

Label (same window as ``xsection.benchmark_event_returns``): decision at the close of row i; entry at the OPEN of
row i+1; exit at the CLOSE of row i+h (deferred to the next unlocked / available close, see ``fills_daily``). ``excess = raw_ret - EW`` where EW is the mean raw return of the
point-in-time eligible universe (``universe_mask[i]``) over names that can be bought at the entry open and have an
exit close. Binary targets:
  * ``top``: excess is in the top tercile of the eligible cross-section at that date (primary; base rate 1/3);
  * ``pos``: excess > 0 (used by the meta-labeling mode);
  * regression variant: ``excess`` winsorised per date (``LabelPanel.excess_w``).
A label is KNOWN only after the close of row i+h (``t1``).

Walk-forward (expanding window): models are retrained every ``retrain_every`` sessions at positions
``r_k = r_first + k*R``. The training set of the model used from ``r_k`` contains ONLY rows whose label end
``t1_pos < r_k - embargo`` (purge by t1, not by t0), so ``max(train t1) < retrain date - embargo`` always holds
(asserted at every retrain and recorded in ``WFResult.blocks``). Probability calibration (Platt by default,
isotonic optional) is fitted only on earlier blocks' out-of-fold predictions whose labels are resolved by then.
Scores for dates ``[r_k, r_{k+1})`` come from model k (features at the close of the date only), earlier rows are NaN.

Sample weights = average uniqueness (AFML 4.4) x piecewise-linear time decay (AFML 4.11) over the TRAINING rows.
Meta-labeling mode: a rule family score selects a wide top-K candidate set per date; the model is trained only on
candidate rows (target ``pos``) and scores only candidates (final top-N is picked by the portfolio builder).
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.cv import CombinatorialPurgedCV
from bist_signal_bot.edge_validation.sample_weights import average_uniqueness, time_decay_weights
from bist_signal_bot.edge_validation.fills_daily import resolve_window
from bist_signal_bot.edge_validation.xsection import DailyContext
from bist_signal_bot.model_loop.daily_features import (FEATURE_COLUMNS, FeaturePanel, get_feature_panel,
                                                       rank_normalize_rows)

NO_ORDER = "No real order sent."
KINDS = ("logit", "hgb")
TARGETS = ("top", "pos")


# ----------------------------------------------------------------------------- labels
@dataclass
class LabelPanel:
    horizon: int
    pos: np.ndarray        # decision row position i
    j: np.ndarray          # symbol column
    t1pos: np.ndarray      # exit row position (label known after its close)
    excess: np.ndarray     # raw - EW
    excess_w: np.ndarray   # per-date winsorised excess (regression target)
    y_top: np.ndarray      # top tercile of excess within the date's eligible set
    y_pos: np.ndarray      # excess > 0
    ew: np.ndarray         # per-row EW return used
    index: pd.DatetimeIndex

    def __len__(self) -> int:
        return len(self.pos)


def build_labels(ctx: DailyContext, horizon: int, fp: Optional[FeaturePanel] = None, top_frac: float = 1 / 3,
                 min_names: int = 10) -> LabelPanel:
    h = int(horizon)
    if h < 1:
        raise ValueError("horizon must be >= 1")
    fp = fp or get_feature_panel(ctx)
    n = len(ctx.index)
    M = ctx.universe_mask.to_numpy(bool)
    P, J, E, EW, W, YT = [], [], [], [], [], []
    for i in range(0, n - h):
        e, x = i + 1, i + h
        # SAME entry/exit semantics as xsection.build_portfolio_events / benchmark_event_returns (fills_daily):
        # unfillable entries (limit-up open, locked bar, zero volume) excluded; locked limit-down / NaN exits deferred.
        w = resolve_window(ctx, i, e, x)
        r = w.raw
        ok = M[i] & w.ok
        if not ok.any():
            continue
        ew = float(r[ok].mean())
        el = np.flatnonzero(ok & fp.valid[i])
        if len(el) < min_names:
            continue
        ex = r[el] - ew
        lo, hi = np.quantile(ex, [0.01, 0.99])
        rk = np.argsort(np.argsort(ex, kind="stable"), kind="stable")
        yt = (rk >= int(math.floor(len(el) * (1.0 - top_frac)))).astype(np.int8)
        P.append(np.full(len(el), i)); J.append(el); E.append(ex); EW.append(np.full(len(el), ew))
        W.append(np.clip(ex, lo, hi)); YT.append(yt)
    if not P:
        z = np.array([], dtype=float)
        zi = np.array([], dtype=int)
        return LabelPanel(h, zi, zi, zi, z, z, zi.astype(np.int8), zi.astype(np.int8), z, ctx.index)
    pos = np.concatenate(P).astype(int)
    ex = np.concatenate(E)
    return LabelPanel(h, pos, np.concatenate(J).astype(int), pos + h, ex, np.concatenate(W), np.concatenate(YT),
                      (ex > 0).astype(np.int8), np.concatenate(EW), ctx.index)


def get_labels(ctx: DailyContext, horizon: int) -> LabelPanel:
    cache = getattr(ctx, "_ml_label_cache", None)
    if cache is None:
        cache = ctx._ml_label_cache = {}
    if int(horizon) not in cache:
        cache[int(horizon)] = build_labels(ctx, horizon)
    return cache[int(horizon)]


def training_weights(pos: np.ndarray, t1pos: np.ndarray, n_grid: int, last_weight: float = 0.5) -> np.ndarray:
    """average uniqueness x time decay (chronological by t0), normalised to mean 1."""
    if len(pos) == 0:
        return np.array([], dtype=float)
    u = average_uniqueness(pos, t1pos, grid=np.arange(n_grid))
    order = np.argsort(pos, kind="stable")
    d = np.empty(len(pos))
    d[order] = time_decay_weights(u[order], last_weight)
    w = u * d
    s = w.mean()
    return w / s if s > 0 else np.ones(len(pos))


# ----------------------------------------------------------------------------- models / calibration
def _threads():
    from threadpoolctl import threadpool_limits
    return threadpool_limits(limits=1)


@dataclass
class FittedModel:
    kind: str
    est: Any
    best_iter: Optional[int] = None

    def predict_p(self, X: np.ndarray) -> np.ndarray:
        with _threads():
            return np.asarray(self.est.predict_proba(X)[:, 1], dtype=float)


def _make_logit(C: float, seed: int):
    from sklearn.linear_model import LogisticRegression
    return LogisticRegression(C=float(C), max_iter=300, random_state=seed)


def _make_hgb(depth: int, max_iter: int, seed: int, lr: float = 0.05, leaf: int = 200):
    from sklearn.ensemble import HistGradientBoostingClassifier
    return HistGradientBoostingClassifier(max_depth=int(depth), learning_rate=lr, max_iter=int(max_iter),
                                          min_samples_leaf=leaf, l2_regularization=1.0, early_stopping=False,
                                          random_state=seed)


def fit_model(kind: str, params: dict, X: np.ndarray, y: np.ndarray, w: np.ndarray, pos: np.ndarray,
              t1pos: np.ndarray, seed: int = 0, hgb_cap: int = 150, tail_frac: float = 0.15) -> FittedModel:
    if len(np.unique(y)) < 2:
        raise ValueError("training block has a single class")
    with _threads():
        if kind == "logit":
            m = _make_logit(params.get("C", 1.0), seed)
            m.fit(X, y, sample_weight=w)
            return FittedModel("logit", m)
        if kind == "hgb":
            depth = int(params.get("max_depth", 3))
            # time-ordered validation tail (by date), head purged by label end so no label overlaps the tail
            dates = np.unique(pos)
            cut = dates[int(len(dates) * (1 - tail_frac))] if len(dates) > 20 else None
            best = hgb_cap
            if cut is not None:
                head = (t1pos < cut)
                tail = pos >= cut
                if head.sum() > 200 and tail.sum() > 100 and len(np.unique(y[head])) == 2 and len(np.unique(y[tail])) == 2:
                    from sklearn.metrics import log_loss
                    m0 = _make_hgb(depth, hgb_cap, seed)
                    m0.fit(X[head], y[head], sample_weight=w[head])
                    losses = [log_loss(y[tail], np.clip(p[:, 1], 1e-6, 1 - 1e-6), labels=[0, 1])
                              for p in m0.staged_predict_proba(X[tail])]
                    best = int(np.argmin(losses)) + 1
            m = _make_hgb(depth, max(best, 10), seed)
            m.fit(X, y, sample_weight=w)
            return FittedModel("hgb", m, best_iter=best)
    raise ValueError(f"unknown kind {kind!r}; choose from {KINDS}")


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


class Calibrator:
    """Monotone non-decreasing probability map fitted on past OOF predictions only.

    ``platt``: sigmoid(a*logit(p)+b), a>0 enforced (a model whose past OOF relation is inverted falls back to the
    identity instead of silently flipping the ranking). ``isotonic``: isotonic regression (may create ties).
    """

    def __init__(self, method: str = "platt"):
        if method not in ("platt", "isotonic", "none"):
            raise ValueError("calibration must be platt|isotonic|none")
        self.method, self.fitted, self.identity, self._m = method, False, method == "none", None

    def fit(self, p: np.ndarray, y: np.ndarray) -> "Calibrator":
        if self.method == "none" or len(p) < 50 or len(np.unique(y)) < 2:
            self.identity = True
            return self
        if self.method == "platt":
            from sklearn.linear_model import LogisticRegression
            lr = LogisticRegression(C=1e4, max_iter=200)
            lr.fit(_logit(p)[:, None], y)
            if lr.coef_[0, 0] <= 0:
                self.identity = True
                return self
            self._m = lr
        else:
            from sklearn.isotonic import IsotonicRegression
            self._m = IsotonicRegression(y_min=0.0, y_max=1.0, increasing=True, out_of_bounds="clip").fit(p, y)
        self.fitted, self.identity = True, False
        return self

    def transform(self, p: np.ndarray) -> np.ndarray:
        p = np.asarray(p, float)
        if self.identity or self._m is None:
            return p
        if self.method == "platt":
            return self._m.predict_proba(_logit(p)[:, None])[:, 1]
        return self._m.predict(p)


# ----------------------------------------------------------------------------- walk-forward
@dataclass
class WFConfig:
    kind: str = "logit"
    params: Dict[str, Any] = field(default_factory=dict)     # model hyperparameters (C / max_depth)
    horizon: int = 10
    retrain_every: int = 60
    embargo: int = 2                 # sessions; train labels must end before r - embargo
    min_train_rows: int = 3000
    min_train_dates: int = 200
    date_stride: int = 5             # train on decision dates with pos % stride == 0 (labels overlap for h > 1)
    target: str = "top"
    calibration: str = "platt"
    seed: int = 0
    cal_min_rows: int = 2000
    decay_last_weight: float = 0.5

    def as_json(self) -> str:
        return json.dumps(self.__dict__, sort_keys=True, default=str)


@dataclass
class WFResult:
    config: WFConfig
    scores: pd.DataFrame
    oof: pd.DataFrame
    blocks: List[dict]
    final_model: Optional[FittedModel] = None
    final_calibrator: Optional[Calibrator] = None
    feature_names: List[str] = field(default_factory=list)


def _target(lp: LabelPanel, name: str) -> np.ndarray:
    if name not in TARGETS:
        raise ValueError(f"target must be in {TARGETS}")
    return (lp.y_top if name == "top" else lp.y_pos).astype(int)


def meta_candidates(ctx: DailyContext, primary: pd.DataFrame, fp: FeaturePanel, k: int) -> tuple:
    """(cand bool (n,m), primary_z (n,m)): top-K by primary score among valid names per date (causal, row-local)."""
    S = primary.reindex(index=ctx.index, columns=ctx.symbols).to_numpy(float)
    ok = fp.valid & np.isfinite(S)
    Sm = np.where(ok, S, -np.inf)
    order = np.argsort(-Sm, axis=1, kind="stable")
    rank = np.empty_like(order)
    np.put_along_axis(rank, order, np.arange(S.shape[1])[None, :].repeat(S.shape[0], 0), axis=1)
    cand = ok & (rank < int(k))
    pz = rank_normalize_rows(np.where(ok, S, np.nan))
    return cand, np.nan_to_num(pz, nan=0.0)


def walk_forward(ctx: DailyContext, cfg: WFConfig, primary: Optional[pd.DataFrame] = None, top_k: int = 30,
                 fit_final: bool = False, fp: Optional[FeaturePanel] = None,
                 lp: Optional[LabelPanel] = None) -> WFResult:
    if cfg.kind not in KINDS:
        raise ValueError(f"kind must be in {KINDS}")
    fp = fp or get_feature_panel(ctx)
    lp = lp or get_labels(ctx, cfg.horizon)
    n, m = len(ctx.index), len(ctx.symbols)
    Z = fp.Z
    cols = list(FEATURE_COLUMNS)
    cand = fp.valid
    if primary is not None:
        cand, pz = meta_candidates(ctx, primary, fp, top_k)
        Z = np.concatenate([Z, pz[:, :, None].astype(np.float32)], axis=2)
        cols = cols + ["primary_z"]
    y_all = _target(lp, cfg.target)
    rowsel = cand[lp.pos, lp.j]
    pos_r, j_r, t1_r, y_r, ex_r = lp.pos[rowsel], lp.j[rowsel], lp.t1pos[rowsel], y_all[rowsel], lp.excess[rowsel]
    stride_ok = (pos_r % max(1, cfg.date_stride)) == 0
    emb, R = int(cfg.embargo), int(cfg.retrain_every)

    # first retrain: enough RESOLVED (t1 < r - emb) rows and dates on the stride grid
    cnt = np.bincount(t1_r[stride_ok], minlength=n + 1).cumsum()
    dts = np.bincount(np.unique(pos_r[stride_ok]) + lp.horizon, minlength=n + 1).cumsum()
    r_first = None
    for r in range(n):
        k = r - emb - 1  # resolved: t1 <= k
        if k >= 0 and cnt[min(k, n)] >= cfg.min_train_rows and dts[min(k, n)] >= cfg.min_train_dates:
            r_first = r
            break
    scores = np.full((n, m), np.nan)
    oof_parts: List[pd.DataFrame] = []
    blocks: List[dict] = []
    oof_store = {"pos": [], "p": [], "y": [], "t1": [], "blk": []}
    if r_first is None:
        return WFResult(cfg, pd.DataFrame(scores, index=ctx.index, columns=ctx.symbols),
                        pd.DataFrame(columns=["pos", "j", "date", "p_raw", "p", "y", "excess"]), blocks, None, None, cols)

    def fit_at(r: int, bi: int):
        sel = stride_ok & (t1_r < r - emb)
        if sel.sum() == 0:
            return None
        assert t1_r[sel].max() < r - emb, "leakage: training label ends at/after retrain date - embargo"
        X = Z[pos_r[sel], j_r[sel], :]
        y = y_r[sel]
        w = training_weights(pos_r[sel], t1_r[sel], n, cfg.decay_last_weight)
        model = fit_model(cfg.kind, cfg.params, X, y, w, pos_r[sel], t1_r[sel], cfg.seed)
        # calibrator: earlier blocks' OOF predictions that are resolved by r - emb
        cal = Calibrator(cfg.calibration)
        if oof_store["pos"]:
            op, pp, yy, tt = (np.concatenate(oof_store[k]) for k in ("pos", "p", "y", "t1"))
            ok = tt < r - emb
            if ok.sum() >= cfg.cal_min_rows:
                cal.fit(pp[ok], yy[ok])
            n_cal = int(ok.sum())
        else:
            n_cal = 0
        blocks.append({"block": bi, "retrain_pos": int(r), "retrain_date": str(ctx.index[min(r, n - 1)].date()),
                       "embargo": emb, "n_train": int(sel.sum()),
                       "max_train_t1_pos": int(t1_r[sel].max()),
                       "max_train_t1": str(ctx.index[int(t1_r[sel].max())].date()),
                       "limit_date": str(ctx.index[max(r - emb, 0)].date()),
                       "n_cal": n_cal, "calibration": ("identity" if (cal.identity or not cal.fitted) else cfg.calibration),
                       "best_iter": model.best_iter})
        return model, cal

    starts = list(range(r_first, n, R))
    for bi, r in enumerate(starts):
        end = min(r + R, n)
        fc = fit_at(r, bi)
        if fc is None:
            continue
        model, cal = fc
        # score every eligible (date, symbol) in the block with features at that date only
        blk_valid = cand[r:end]
        if blk_valid.any():
            ii, jj = np.nonzero(blk_valid)
            pr = model.predict_p(Z[r + ii, jj, :])
            scores[r + ii, jj] = cal.transform(pr)
        # OOF store for labelled rows inside the block
        inb = (pos_r >= r) & (pos_r < end)
        if inb.any():
            Xb = Z[pos_r[inb], j_r[inb], :]
            praw = model.predict_p(Xb)
            pcal = cal.transform(praw)
            oof_store["pos"].append(pos_r[inb]); oof_store["p"].append(praw); oof_store["y"].append(y_r[inb])
            oof_store["t1"].append(t1_r[inb]); oof_store["blk"].append(np.full(int(inb.sum()), bi))
            oof_parts.append(pd.DataFrame({"pos": pos_r[inb], "j": j_r[inb], "p_raw": praw, "p": pcal,
                                           "y": y_r[inb], "excess": ex_r[inb], "block": bi}))
    oof = (pd.concat(oof_parts, ignore_index=True) if oof_parts else
           pd.DataFrame(columns=["pos", "j", "p_raw", "p", "y", "excess", "block"]))
    if len(oof):
        oof.insert(2, "date", ctx.index[oof["pos"].to_numpy(int)])
    fm = fc_cal = None
    if fit_final:
        r_end = n
        out = fit_at(r_end, len(starts))
        if out is not None:
            fm, fc_cal = out
    return WFResult(cfg, pd.DataFrame(scores, index=ctx.index, columns=ctx.symbols), oof, blocks, fm, fc_cal, cols)


# ----------------------------------------------------------------------------- metrics
def rank_ic_by_date(pos: np.ndarray, score: np.ndarray, excess: np.ndarray, min_names: int = 10) -> pd.Series:
    df = pd.DataFrame({"pos": pos, "s": score, "e": excess})
    df["rs"] = df.groupby("pos")["s"].rank()
    df["re"] = df.groupby("pos")["e"].rank()
    out = {}
    for p, g in df.groupby("pos"):
        if len(g) >= min_names and g["rs"].std() > 0 and g["re"].std() > 0:
            out[p] = float(np.corrcoef(g["rs"], g["re"])[0, 1])
    return pd.Series(out, dtype=float)


def ic_summary(ic: pd.Series, horizon: int) -> Dict[str, Optional[float]]:
    if len(ic) < 2:
        return {"ic_mean": None, "ic_std": None, "ic_ir": None, "ic_ir_annual": None, "ic_tstat_overlap_adj": None,
                "n_dates": int(len(ic))}
    mu, sd = float(ic.mean()), float(ic.std())
    ir = mu / sd if sd > 0 else None
    return {"ic_mean": mu, "ic_std": sd, "ic_ir": ir, "ic_ir_annual": None if ir is None else ir * math.sqrt(252.0 / horizon),
            "ic_tstat_overlap_adj": None if ir is None else ir * math.sqrt(len(ic) / max(horizon, 1)),
            "n_dates": int(len(ic))}


def oof_report(res: WFResult) -> Dict[str, Any]:
    """OOS AUC/Brier/ECE (raw and calibrated) + cross-sectional rank IC of the walk-forward out-of-fold scores."""
    from bist_signal_bot.model_loop.training import prob_metrics
    o = res.oof
    if len(o) < 100 or o["y"].nunique() < 2:
        return {"n_oof": int(len(o)), "note": "insufficient OOF rows"}
    y = o["y"].to_numpy(int)
    raw, cal = prob_metrics(o["p_raw"].to_numpy(), y), prob_metrics(o["p"].to_numpy(), y)
    ic = rank_ic_by_date(o["pos"].to_numpy(int), o["p"].to_numpy(), o["excess"].to_numpy())
    out = {"n_oof": int(len(o)), "n_blocks": len(res.blocks), "raw": raw, "calibrated": cal,
           "auc": cal["auc"], "brier": cal["brier"], "log_loss": cal["log_loss"],
           "calibration_error": cal["calibration_error"], "base_rate": raw["base_rate"]}
    out.update(ic_summary(ic, res.config.horizon))
    return out


def cpcv_report(ctx: DailyContext, cfg: WFConfig, primary: Optional[pd.DataFrame] = None, top_k: int = 30,
                n_groups: int = 6, n_test_groups: int = 2) -> Dict[str, Any]:
    """Combinatorial purged CV of the model (no walk-forward ordering) on the label intervals [t0, t1].

    Per path: AUC / Brier / ECE; plus the cross-sectional rank IC of the path-averaged probabilities. Purge uses
    the label end t1; embargo = ``cfg.embargo`` sessions (converted to calendar days)."""
    from bist_signal_bot.model_loop.training import prob_metrics
    fp, lp = get_feature_panel(ctx), get_labels(ctx, cfg.horizon)
    Z, cand = fp.Z, fp.valid
    if primary is not None:
        cand, pz = meta_candidates(ctx, primary, fp, top_k)
        Z = np.concatenate([Z, pz[:, :, None].astype(np.float32)], axis=2)
    y_all = _target(lp, cfg.target)
    sel = cand[lp.pos, lp.j] & ((lp.pos % max(1, cfg.date_stride)) == 0)
    pos, j, t1, y, ex = lp.pos[sel], lp.j[sel], lp.t1pos[sel], y_all[sel], lp.excess[sel]
    if len(pos) < n_groups * 50:
        return {"note": "insufficient rows", "n_rows": int(len(pos))}
    t0d, t1d = pd.Series(ctx.index[pos]), pd.Series(ctx.index[t1])
    cv = CombinatorialPurgedCV(n_groups, n_test_groups, embargo=pd.Timedelta(days=int(math.ceil(cfg.embargo * 7 / 5))))
    groups = cv.group_indices(t0d)
    X = Z[pos, j, :]
    preds = []
    for tr, te, combo in cv.split(t0d, t1d):
        w = training_weights(pos[tr], t1[tr], len(ctx.index), cfg.decay_last_weight)
        mdl = fit_model(cfg.kind, cfg.params, X[tr], y[tr], w, pos[tr], t1[tr], cfg.seed)
        preds.append({g: (groups[g], mdl.predict_p(X[groups[g]])) for g in combo})
    paths = cv.assemble_paths(preds)
    per, pbar = [], np.zeros(len(pos))
    for path in paths:
        p = np.full(len(pos), np.nan)
        for g, (gi, pr) in path.items():
            p[gi] = pr
        per.append(prob_metrics(p, y))
        pbar += p / len(paths)
    ic = rank_ic_by_date(pos, pbar, ex)
    out = {k: float(np.nanmean([d[k] for d in per])) for k in per[0]}
    out.update({"auc_path_std": float(np.nanstd([d["auc"] for d in per])), "n_paths": len(paths),
                "n_splits": cv.n_splits, "n_rows": int(len(pos))})
    out.update(ic_summary(ic, cfg.horizon))
    return out
