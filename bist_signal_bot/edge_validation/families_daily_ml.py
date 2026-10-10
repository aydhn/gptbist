"""ML daily score families (``ml_xs_logit``, ``ml_xs_hgb``, ``ml_xs_meta``). Research only; no real order is sent.

Each score is a strictly walk-forward model output (see ``model_loop.daily_training``): rows before the first
trained model are NaN, training labels are purged by label end t1 with an embargo, calibration uses only past OOF.
The label horizon is chosen by the RUNNER: families declare ``needs_horizon = True`` and ``run_family_daily`` passes
``params['label_h'] = horizon`` (one walk-forward per (params, horizon), cached per context). Every (params, horizon)
combination is a ledger trial, so grids are kept small:
  * ml_xs_logit : C {0.1, 1.0} x retrain_every {20, 60}        -> 4 combos
  * ml_xs_hgb   : max_depth {2, 3} x retrain_every {60}        -> 2 combos
  * ml_xs_meta  : primary {xs_momentum_1_6, xs_quality_proxy} x K {30} x retrain_every {60} -> 2 combos
    (meta: the rule family picks the top-K candidates; the logistic model learns P(excess>0) among them and the
    portfolio builder takes the final top-N by calibrated probability).
Non-grid knobs (defaults; override via params only for tests): embargo=2, date_stride=5, min_train_rows=3000,
min_train_dates=200, calibration='platt', seed=0.
"""
from __future__ import annotations

import json
from typing import Dict

import pandas as pd

from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES, register_family
from bist_signal_bot.edge_validation.xsection import DailyContext

PRIMARY_DEFAULT_PARAMS: Dict[str, dict] = {
    "xs_momentum_1_6": {"lookback": 126, "skip": 5, "vol_scaled": 0},
    "xs_quality_proxy": {"method": "maxdd", "window": 250},
}
_KNOBS = ("embargo", "date_stride", "min_train_rows", "min_train_dates", "calibration", "seed", "cal_min_rows",
          "target")


def _cfg(kind: str, params: dict, model_params: dict, target: str):
    from bist_signal_bot.model_loop.daily_training import WFConfig
    kw = {k: params[k] for k in _KNOBS if k in params}
    kw.setdefault("target", target)
    return WFConfig(kind=kind, params=model_params, horizon=int(params.get("label_h", 10)),
                    retrain_every=int(params.get("retrain_every", 60)), **kw)


def _cached(ctx: DailyContext, key: str, fn):
    cache = getattr(ctx, "_ml_wf_cache", None)
    if cache is None:
        cache = ctx._ml_wf_cache = {}
    if key not in cache:
        cache[key] = fn()
    return cache[key]


class _MLBase:
    name = ""
    kind = "logit"
    needs_horizon = True
    default_grid: dict = {}

    def valid(self, params: dict) -> bool:
        return int(params.get("retrain_every", 60)) >= 5 and int(params.get("label_h", 10)) >= 1

    def _model_params(self, params: dict) -> dict:
        raise NotImplementedError

    def wf(self, ctx: DailyContext, params: dict, fit_final: bool = False):
        from bist_signal_bot.model_loop.daily_training import walk_forward
        cfg = _cfg(self.kind, params, self._model_params(params), "top")
        key = f"{self.name}|{cfg.as_json()}|{int(fit_final)}"
        return _cached(ctx, key, lambda: walk_forward(ctx, cfg, fit_final=fit_final))

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        if not self.valid(params):
            raise ValueError(f"invalid params for {self.name}: {params}")
        return self.wf(ctx, params).scores


class MLXSLogit(_MLBase):
    """Walk-forward logistic regression on rank-normalised causal features; target = top tercile of excess return
    over the EW eligible universe at horizon h. Score = calibrated P(top tercile). Hypothesis: a regularised linear
    blend of momentum/risk/volume/relative-strength features carries cross-sectional information that single rule
    families lack. Honest prior: weak or none (the rule families found nothing); the gate decides."""
    name = "ml_xs_logit"
    kind = "logit"
    default_grid = {"C": [0.1, 1.0], "retrain_every": [20, 60]}

    def valid(self, params: dict) -> bool:
        return super().valid(params) and float(params.get("C", 1.0)) > 0

    def _model_params(self, params: dict) -> dict:
        return {"C": float(params.get("C", 1.0))}


class MLXSHGB(_MLBase):
    """Walk-forward HistGradientBoosting (shallow trees, lr 0.05, <=150 iterations early-stopped on a
    time-ordered validation tail) with the same target/features/calibration as ``ml_xs_logit``."""
    name = "ml_xs_hgb"
    kind = "hgb"
    default_grid = {"max_depth": [2, 3], "retrain_every": [60]}

    def valid(self, params: dict) -> bool:
        return super().valid(params) and int(params.get("max_depth", 3)) >= 1

    def _model_params(self, params: dict) -> dict:
        return {"max_depth": int(params.get("max_depth", 3))}


class MLXSMeta(_MLBase):
    """Meta-labeling: a rule family (``primary``) picks the top-K names per date; a logistic model (C=0.3, features
    + the primary's normalised score) learns P(excess > 0) among those candidates; non-candidates score NaN so the
    portfolio builder's top-N is the best N of the K by calibrated probability."""
    name = "ml_xs_meta"
    kind = "logit"
    default_grid = {"primary": ["xs_momentum_1_6", "xs_quality_proxy"], "K": [30], "retrain_every": [60]}

    def valid(self, params: dict) -> bool:
        return (super().valid(params) and params.get("primary") in PRIMARY_DEFAULT_PARAMS
                and int(params.get("K", 30)) >= 2)

    def _model_params(self, params: dict) -> dict:
        return {"C": float(params.get("C", 0.3))}

    def primary_scores(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        name = params["primary"]
        pp = PRIMARY_DEFAULT_PARAMS[name]
        return _cached(ctx, f"primary|{name}|{json.dumps(pp, sort_keys=True)}",
                       lambda: DAILY_FAMILIES[name].score(ctx, pp))

    def wf(self, ctx: DailyContext, params: dict, fit_final: bool = False):
        from bist_signal_bot.model_loop.daily_training import walk_forward
        cfg = _cfg(self.kind, params, self._model_params(params), "pos")
        k = int(params.get("K", 30))
        key = f"{self.name}|{params['primary']}|{k}|{cfg.as_json()}|{int(fit_final)}"
        return _cached(ctx, key, lambda: walk_forward(ctx, cfg, primary=self.primary_scores(ctx, params),
                                                      top_k=k, fit_final=fit_final))


FAMILY_CLASSES = {"ml_xs_logit": MLXSLogit, "ml_xs_hgb": MLXSHGB, "ml_xs_meta": MLXSMeta}

for _cls in FAMILY_CLASSES.values():
    register_family(_cls())
