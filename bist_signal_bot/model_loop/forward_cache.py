"""Forward model cache: incremental walk-forward scoring of ONE date (the newest row) from persisted models.

Research/paper only; shadow-only (never champion, never promoted). No real order is ever sent.

``daily_training.walk_forward`` retrains at absolute row positions ``r_k = r_first + k*R`` and scores the rows of block
``k`` with that block's (model, calibrator). The forward job only needs the score row of TODAY, so this module:
  * persists one (model, calibrator) artifact per block under ``<root>/<family>__<key8>/`` (joblib, trusted local
    files) with a state.json carrying the FEATURES_VERSION / feature-schema hash and the full walk-forward config;
  * trains only the blocks that are MISSING (bootstrap = all blocks up to today, daily = none, every R sessions = one),
    always on strictly past data (train labels end before ``r - embargo``; asserted);
  * the calibrator of block k is fitted on the earlier blocks' out-of-fold RAW predictions (recomputed from the
    cached earlier models), exactly like the research walk-forward, so cached scores == full walk-forward scores
    (equivalence test: tests/test_forward_model_cache.py);
  * never recomputes scores of past dates.
A changed feature schema / config / index start yields a different key (a fresh cache dir); an artifact whose stored
schema hash differs from the current one is refused.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from bist_signal_bot.model_loop.daily_features import FEATURE_COLUMNS, FEATURES_VERSION, get_feature_panel
from bist_signal_bot.model_loop.daily_training import (Calibrator, WFConfig, _target, fit_model, get_labels,
                                                       meta_candidates, training_weights)

NO_ORDER = "No real order sent."
SCHEMA = 1


def feature_schema_hash(cols) -> str:
    return hashlib.sha256(json.dumps({"fv": FEATURES_VERSION, "cols": list(cols)}, sort_keys=True)
                          .encode()).hexdigest()[:16]


def _dump(obj, path: Path) -> None:
    import joblib
    tmp = path.with_suffix(path.suffix + ".tmp")
    joblib.dump(obj, tmp)
    os.replace(tmp, path)


class ForwardModelCache:
    def __init__(self, root, ctx, cfg: WFConfig, primary: Optional[pd.DataFrame] = None, top_k: int = 30,
                 family: str = "", extra: Optional[dict] = None, tiers: Optional[List[str]] = None):
        self.ctx, self.cfg, self.family = ctx, cfg, family or cfg.kind
        self.fp = get_feature_panel(ctx)
        self.Z, self.cols, self.cand = self.fp.Z, list(FEATURE_COLUMNS), self.fp.valid
        if primary is not None:
            self.cand, pz = meta_candidates(ctx, primary, self.fp, top_k)
            self.Z = np.concatenate([self.Z, pz[:, :, None].astype(np.float32)], axis=2)
            self.cols = self.cols + ["primary_z"]
        self.schema_hash = feature_schema_hash(self.cols)
        self.payload = {"schema": SCHEMA, "family": self.family, "wf": json.loads(cfg.as_json()),
                        "top_k": int(top_k) if primary is not None else None, "extra": extra or {},
                        "features_version": FEATURES_VERSION, "feature_schema_hash": self.schema_hash,
                        "index_start": str(ctx.index[0].date())}
        self.key = hashlib.sha256(json.dumps(self.payload, sort_keys=True).encode()).hexdigest()[:8]
        self.dir = Path(root) / f"{self.family}__{self.key}"
        self.tiers = sorted(set(tiers or []))
        self._prep = None
        self._oof: Dict[int, tuple] = {}
        self._models: Dict[int, tuple] = {}

    # ---------------- state ----------------
    @property
    def state_path(self) -> Path:
        return self.dir / "state.json"

    def _load_state(self) -> dict:
        if not self.state_path.exists():
            return {"payload": self.payload, "r_first_date": None, "blocks": {}, "shadow_only": True,
                    "champion": False, "tiers": [], "disclaimer": NO_ORDER}
        st = json.loads(self.state_path.read_text(encoding="utf-8"))
        if st.get("payload") != self.payload:
            raise ValueError(f"model cache payload mismatch in {self.dir} (feature schema / config changed)")
        return st

    def _save_state(self, st: dict) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(st, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.state_path)

    # ---------------- label-derived arrays (only needed when something must be trained) ----------------
    def _arrays(self):
        if self._prep is not None:
            return self._prep
        cfg, ctx = self.cfg, self.ctx
        lp = get_labels(ctx, cfg.horizon)
        y_all = _target(lp, cfg.target)
        rowsel = self.cand[lp.pos, lp.j]
        pos_r, j_r, t1_r, y_r = lp.pos[rowsel], lp.j[rowsel], lp.t1pos[rowsel], y_all[rowsel]
        stride_ok = (pos_r % max(1, cfg.date_stride)) == 0
        self._prep = (lp, pos_r, j_r, t1_r, y_r, stride_ok)
        return self._prep

    def _first_retrain(self) -> Optional[int]:
        cfg, n = self.cfg, len(self.ctx.index)
        lp, pos_r, _, t1_r, _, stride_ok = self._arrays()
        emb = int(cfg.embargo)
        cnt = np.bincount(t1_r[stride_ok], minlength=n + 1).cumsum()
        dts = np.bincount(np.unique(pos_r[stride_ok]) + lp.horizon, minlength=n + 1).cumsum()
        for r in range(n):
            k = r - emb - 1
            if k >= 0 and cnt[min(k, n)] >= cfg.min_train_rows and dts[min(k, n)] >= cfg.min_train_dates:
                return r
        return None

    # ---------------- model IO ----------------
    def _block_file(self, k: int) -> Path:
        return self.dir / f"block_{k:03d}.joblib"

    def _load_block(self, k: int, st: dict):
        if k in self._models:
            return self._models[k]
        import joblib
        meta = st["blocks"][str(k)]
        if meta.get("empty"):
            self._models[k] = (None, None)
            return self._models[k]
        art = joblib.load(self._block_file(k))
        if art.get("feature_schema_hash") != self.schema_hash or art.get("features_version") != FEATURES_VERSION:
            raise ValueError(f"cached model block {k} has a different feature schema; refusing to score with it")
        self._models[k] = (art["model"], art["cal"])
        return self._models[k]

    def _block_oof(self, j: int, r_j: int, st: dict):
        """Raw OOF predictions of cached block j on its labelled rows (cand rows with pos in [r_j, r_j+R))."""
        if j in self._oof:
            return self._oof[j]
        model, _ = self._load_block(j, st)
        if model is None:
            self._oof[j] = None
            return None
        _, pos_r, j_r, t1_r, y_r, _ = self._arrays()
        n, R = len(self.ctx.index), int(self.cfg.retrain_every)
        inb = (pos_r >= r_j) & (pos_r < min(r_j + R, n))
        out = None
        if inb.any():
            out = (pos_r[inb], model.predict_p(self.Z[pos_r[inb], j_r[inb], :]), y_r[inb], t1_r[inb])
        self._oof[j] = out
        return out

    def _train_block(self, k: int, r: int, r_first: int, st: dict) -> None:
        cfg, ctx = self.cfg, self.ctx
        n, emb, R = len(ctx.index), int(cfg.embargo), int(cfg.retrain_every)
        _, pos_r, j_r, t1_r, y_r, stride_ok = self._arrays()
        sel = stride_ok & (t1_r < r - emb)
        meta = {"k": k, "retrain_pos": int(r), "retrain_date": str(ctx.index[min(r, n - 1)].date())}
        if sel.sum() == 0:
            meta["empty"] = True
            st["blocks"][str(k)] = meta
            self._models[k] = (None, None)
            self._save_state(st)
            return
        assert t1_r[sel].max() < r - emb, "leakage: training label ends at/after retrain date - embargo"
        X = self.Z[pos_r[sel], j_r[sel], :]
        w = training_weights(pos_r[sel], t1_r[sel], n, cfg.decay_last_weight)
        model = fit_model(cfg.kind, cfg.params, X, y_r[sel], w, pos_r[sel], t1_r[sel], cfg.seed)
        cal = Calibrator(cfg.calibration)
        parts = []
        for j in range(k):
            if st["blocks"][str(j)].get("empty"):
                continue
            o = self._block_oof(j, r_first + j * R, st)
            if o is not None:
                parts.append(o)
        n_cal = 0
        if parts:
            pp = np.concatenate([p[1] for p in parts])
            yy = np.concatenate([p[2] for p in parts])
            tt = np.concatenate([p[3] for p in parts])
            ok = tt < r - emb
            if ok.sum() >= cfg.cal_min_rows:
                cal.fit(pp[ok], yy[ok])
            n_cal = int(ok.sum())
        self.dir.mkdir(parents=True, exist_ok=True)
        _dump({"model": model, "cal": cal, "feature_schema_hash": self.schema_hash,
               "features_version": FEATURES_VERSION, "block": k, "retrain_date": meta["retrain_date"],
               "payload": self.payload}, self._block_file(k))
        meta.update(n_train=int(sel.sum()), max_train_t1=str(ctx.index[int(t1_r[sel].max())].date()),
                    limit_date=str(ctx.index[max(r - emb, 0)].date()), n_cal=n_cal,
                    calibration=("identity" if (cal.identity or not cal.fitted) else cfg.calibration),
                    best_iter=model.best_iter, file=self._block_file(k).name)
        st["blocks"][str(k)] = meta
        self._models[k] = (model, cal)
        self._save_state(st)

    # ---------------- public ----------------
    def score_last(self) -> Tuple[np.ndarray, dict]:
        """(score row aligned to ctx.symbols, info) for the newest row of the context."""
        ctx, cfg = self.ctx, self.cfg
        n, R = len(ctx.index), int(cfg.retrain_every)
        L = n - 1
        st = self._load_state()
        trained: List[int] = []
        r_first = None
        if st.get("r_first_date"):
            r_first = int(ctx.index.get_loc(pd.Timestamp(st["r_first_date"])))
        else:
            r_first = self._first_retrain()
            if r_first is not None:
                st["r_first_date"] = str(ctx.index[r_first].date())
        info = {"cache_key": self.key, "model_dir": self.dir.name, "feature_schema_hash": self.schema_hash,
                "features_version": FEATURES_VERSION, "trained_now": trained, "shadow_only": True,
                "champion": False, "disclaimer": NO_ORDER}
        scores = np.full(len(ctx.symbols), np.nan)
        if r_first is None or L < r_first:
            info.update(block=None, note="no model yet (insufficient resolved training rows)")
            return scores, info
        kcur = (L - r_first) // R
        for k in range(kcur + 1):
            r = r_first + k * R
            meta = st["blocks"].get(str(k))
            if meta is not None:
                if meta["retrain_date"] != str(ctx.index[min(r, n - 1)].date()):
                    raise ValueError(f"model cache block {k} date mismatch (index changed); refusing")
                if meta.get("empty") or self._block_file(k).exists():
                    continue
                raise FileNotFoundError(f"model cache artifact missing: {self._block_file(k)}")
            self._train_block(k, r, r_first, st)
            trained.append(k)
        if sorted(set(st.get("tiers", [])) | set(self.tiers)) != st.get("tiers") or trained or not self.state_path.exists():
            st["tiers"] = sorted(set(st.get("tiers", [])) | set(self.tiers))
            st["shadow_only"], st["champion"] = True, False
            self._save_state(st)
        model, cal = self._load_block(kcur, st)
        meta = st["blocks"][str(kcur)]
        info.update(block=kcur, retrain_date=meta["retrain_date"], n_train=meta.get("n_train"),
                    calibration=meta.get("calibration"), n_blocks=kcur + 1)
        if model is None:
            return scores, info
        valid = self.cand[L]
        if valid.any():
            jj = np.flatnonzero(valid)
            scores[jj] = cal.transform(model.predict_p(self.Z[L, jj, :]))
        return scores, info
