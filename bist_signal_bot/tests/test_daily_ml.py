"""Multi-day ML research path: feature causality, labels, walk-forward leakage, calibration, meta top-K, families,
runner integration (temp ledger only) and the daily model lifecycle (gating, drift challenger, rollback)."""
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
from bist_signal_bot.edge_validation.gate import CandidateGate, GateConfig
from bist_signal_bot.edge_validation.ledger import TrialLedger
from bist_signal_bot.edge_validation.runner_daily import run_family_daily
from bist_signal_bot.edge_validation.xsection import (DailyContext, apply_benchmark, build_portfolio_events,
                                                      check_score_causality)
from bist_signal_bot.model_loop.daily_features import (CS_FEATURES, FEATURE_COLUMNS, MKT_FEATURES,
                                                       build_feature_panel, get_feature_panel)
from bist_signal_bot.model_loop.daily_lifecycle import (DailyDriftMonitor, DailyModelTrainer, daily_drift_inputs,
                                                        due_for_retrain)
from bist_signal_bot.model_loop.daily_training import (Calibrator, WFConfig, build_labels, cpcv_report,
                                                       get_labels, oof_report, walk_forward)
from bist_signal_bot.model_loop.lifecycle import ModelLifecycle
from bist_signal_bot.model_registry.models import ModelRegistryStatus
from bist_signal_bot.model_registry.registry import LocalModelRegistry
from bist_signal_bot.tests.test_model_loop_lifecycle import Audit, FakeStore, Kill, Pre, S, Trainer, rec
from bist_signal_bot.tests.test_xsection_daily import make_panel

SMALL = {"min_train_rows": 500, "min_train_dates": 60}


def _ctx(seed=5, n_sym=30, days=900, momentum=0.0):
    panel = make_panel(seed, n_sym=n_sym, days=days, momentum=momentum)
    bm = pd.DataFrame({s: d["close"] for s, d in panel.items()}).mean(axis=1)
    fx = pd.Series(np.cumprod(1 + np.random.default_rng(seed).normal(0.0005, 0.01, days)), index=bm.index)
    return DailyContext.from_panel(panel, bm, usdtry=fx, min_adv=5e6)


@pytest.fixture(scope="module")
def ctx():
    return _ctx()


def _wf(ctx, fit_final=False, **kw):
    cfg = dict(kind="logit", params={"C": 0.1}, horizon=10, retrain_every=40, **SMALL)
    cfg.update(kw)
    return walk_forward(ctx, WFConfig(**cfg), fit_final=fit_final)


# ------------------------------------------------------------------ features
def test_feature_columns_and_normalisation(ctx):
    fp = get_feature_panel(ctx)
    assert fp.X.shape == (len(ctx.index), len(ctx.symbols), len(FEATURE_COLUMNS))
    assert FEATURE_COLUMNS == CS_FEATURES + MKT_FEATURES and len(set(FEATURE_COLUMNS)) == len(FEATURE_COLUMNS)
    f = FEATURE_COLUMNS.index("ret_60")
    row = fp.X[600, :, f]
    assert np.nanmax(np.abs(row)) <= 3.0 + 1e-6 and abs(np.nanmean(row)) < 0.2  # rank-normal, clipped
    assert np.isfinite(fp.Z).all() and fp.valid.any()
    assert get_feature_panel(ctx) is fp  # cached per context


@pytest.mark.parametrize("cut", [0.45, 0.7, 0.95])
def test_feature_causality_truncation(ctx, cut):
    full = get_feature_panel(ctx).X
    k = int(len(ctx.index) * cut)
    part = build_feature_panel(ctx.truncate(k)).X
    a, b = full[:k], part
    same = (np.isnan(a) & np.isnan(b)) | np.isclose(a, b, atol=1e-5, equal_nan=False)
    assert same.all(), f"look-ahead in features: {(~same).sum()} cells"


# ------------------------------------------------------------------ labels
def test_labels_match_xsection_excess_definition(ctx):
    h = 10
    lp = build_labels(ctx, h)
    assert (lp.t1pos == lp.pos + h).all()
    scores = pd.DataFrame(np.random.default_rng(0).random(ctx.close.shape), index=ctx.index, columns=ctx.symbols)
    ev = apply_benchmark(ctx, build_portfolio_events(ctx, scores, h, 8).events, "ew_universe")
    pos = pd.Series(np.arange(len(ctx.index)), index=ctx.index)
    col = {s: i for i, s in enumerate(ctx.symbols)}
    key = pd.DataFrame({"pos": lp.pos, "j": lp.j, "ex": lp.excess})
    hit = 0
    for _, e in ev[ev['t0'] > ctx.index[450]].head(60).iterrows():
        m = key[(key.pos == pos[e["t0"]]) & (key.j == col[e["symbol"]])]
        if len(m):
            hit += 1
            assert m["ex"].iloc[0] == pytest.approx(e["raw_ret"] - e["bench_ret"], abs=1e-12)
    assert hit > 10


def test_label_tercile_rate_and_horizon_end(ctx):
    lp = get_labels(ctx, 5)
    rate = pd.Series(lp.y_top).groupby(lp.pos).mean()
    assert 0.25 < rate.mean() < 0.40
    assert lp.pos.max() + 5 <= len(ctx.index) - 1
    assert get_labels(ctx, 5) is lp


# ------------------------------------------------------------------ walk-forward leakage
def test_walk_forward_no_label_leakage_purge_by_t1(ctx):
    res = _wf(ctx, embargo=3)
    assert len(res.blocks) >= 5
    lp = get_labels(ctx, 10)
    n = len(ctx.index)
    for b in res.blocks:
        r = b["retrain_pos"]
        assert b["max_train_t1_pos"] < r - 3  # max(train t1) < retrain date - embargo
        assert pd.Timestamp(b["max_train_t1"]) < pd.Timestamp(b["limit_date"]) <= pd.Timestamp(b["retrain_date"])
        # independent recomputation of the train set
        sel = (lp.t1pos < r - 3) & (lp.pos % 5 == 0)
        assert b["n_train"] == int(sel.sum())
        # purging by t0 only (the classic mistake) would have let labels in that end after the cut
        naive = (lp.pos < r - 3) & (lp.pos % 5 == 0)
        assert naive.sum() >= sel.sum()
    assert res.blocks[0]["retrain_pos"] > 10 + 3
    # scores before the first model are NaN, from the first retrain onward some are finite
    first = res.blocks[0]["retrain_pos"]
    assert res.scores.iloc[:first].isna().all().all() and res.scores.iloc[first:].notna().any().any()
    assert res.blocks[0]["n_cal"] == 0 and res.blocks[0]["calibration"] == "identity"
    assert n > first


def test_calibration_uses_only_past_resolved_oof(ctx):
    res = _wf(ctx, embargo=2, cal_min_rows=300)
    oof = res.oof
    for b in res.blocks[1:]:
        r = b["retrain_pos"]
        past = oof[(oof["block"] < b["block"]) & ((oof["pos"] + 10) < r - 2)]
        assert b["n_cal"] == len(past)
    assert any(b["calibration"] == "platt" for b in res.blocks)


def test_deterministic_with_seed(ctx):
    a, b = _wf(ctx, kind="hgb", params={"max_depth": 2}, retrain_every=120, seed=3), \
        _wf(ctx, kind="hgb", params={"max_depth": 2}, retrain_every=120, seed=3)
    pd.testing.assert_frame_equal(a.scores, b.scores)
    pd.testing.assert_frame_equal(a.oof, b.oof)


def test_calibrator_monotone_and_inverted_fallback():
    rng = np.random.default_rng(0)
    p = rng.uniform(0.05, 0.95, 5000)
    y = (rng.uniform(size=5000) < 0.2 + 0.6 * p).astype(int)
    grid = np.linspace(0.01, 0.99, 200)
    for m in ("platt", "isotonic"):
        out = Calibrator(m).fit(p, y).transform(grid)
        assert (np.diff(out) >= -1e-12).all() and out.min() >= 0 and out.max() <= 1
    cal = Calibrator("platt").fit(p, 1 - y)  # inverted relation: must not flip the ranking
    assert cal.identity and (np.diff(cal.transform(grid)) >= 0).all()


def test_oof_report_and_cpcv(ctx):
    res = _wf(ctx)
    rep = oof_report(res)
    assert 0.3 < rep["auc"] < 0.7 and rep["n_oof"] > 1000 and "ic_mean" in rep and "ic_ir" in rep
    cp = cpcv_report(ctx, res.config, n_groups=5, n_test_groups=2)
    assert cp["n_paths"] == 4 and 0.35 < cp["auc"] < 0.65 and cp["n_splits"] == 10


# ------------------------------------------------------------------ meta-labeling
def test_meta_topk_logic(ctx):
    fam = DAILY_FAMILIES["ml_xs_meta"]
    p = {"primary": "xs_momentum_1_6", "K": 8, "retrain_every": 60, "label_h": 10, **SMALL}
    sc = fam.score(ctx, p)
    prim = fam.primary_scores(ctx, p)
    fp = get_feature_panel(ctx)
    per_date = sc.notna().sum(axis=1)
    assert per_date.max() <= 8 and per_date.max() > 0
    for d in sc.index[sc.notna().any(axis=1)][::25]:
        i = ctx.index.get_loc(d)
        ok = fp.valid[i] & np.isfinite(prim.iloc[i].to_numpy(float))
        top = set(np.array(ctx.symbols)[np.argsort(-np.where(ok, prim.iloc[i].to_numpy(float), -np.inf), kind="stable")[:8]])
        assert set(sc.columns[sc.loc[d].notna()]) <= top
    assert not DAILY_FAMILIES["ml_xs_meta"].valid({"primary": "nope", "K": 8})


# ------------------------------------------------------------------ families
@pytest.mark.parametrize("name,params", [
    ("ml_xs_logit", {"C": 0.1, "retrain_every": 40}),
    ("ml_xs_hgb", {"max_depth": 2, "retrain_every": 120}),
    ("ml_xs_meta", {"primary": "xs_quality_proxy", "K": 10, "retrain_every": 120}),
])
def test_family_causality_and_grids(name, params, ctx):
    fam = DAILY_FAMILIES[name]
    p = {**params, "label_h": 10, **SMALL}
    assert fam.valid(p) and fam.needs_horizon
    check_score_causality(fam, ctx, p, cuts=(0.6, 0.9))
    assert fam.score(ctx, p).iloc[:100].isna().all().all()
    import itertools
    grid = [dict(zip(fam.default_grid, v)) for v in itertools.product(*fam.default_grid.values())]
    assert 1 <= len([g for g in grid if fam.valid(g)]) <= 4


def test_runner_passes_horizon_and_uses_temp_ledger(ctx, tmp_path):
    led = TrialLedger(tmp_path / "t.sqlite")
    grid = {"C": [0.1, 1.0], "retrain_every": [60], **{k: [v] for k, v in SMALL.items()}}
    res = run_family_daily("ml_xs_logit", ctx, (5, 10), grid, 8, led, CandidateGate(GateConfig(), save=False),
                           save_report=False, benchmark="ew_universe")
    assert led.n_trials("ml_xs_logit_daily_xs_ew2") == 4  # 2 params x 2 horizons, every combo counted
    assert res.verdict in ("CANDIDATE", "REJECTED", "INSUFFICIENT_DATA")
    assert res.verdict != "CANDIDATE"  # pure noise panel: no edge may be reported
    fam = DAILY_FAMILIES["ml_xs_logit"]
    h5 = fam.wf(ctx, {"C": 0.1, "retrain_every": 60, "label_h": 5, **SMALL})
    h10 = fam.wf(ctx, {"C": 0.1, "retrain_every": 60, "label_h": 10, **SMALL})
    assert h5.config.horizon == 5 and h10.config.horizon == 10


# ------------------------------------------------------------------ lifecycle
def _registry():
    return LocalModelRegistry(None, FakeStore())


def test_failing_gate_model_is_watch_and_never_promotable(ctx, tmp_path):
    reg = _registry()
    tr = DailyModelTrainer(ctx, TrialLedger(tmp_path / "t.sqlite"), "logit", 10, None, reg,
                           {"C": 0.1, "retrain_every": 60}, models_dir=tmp_path / "m", knobs=dict(SMALL),
                           gate=CandidateGate(GateConfig(), save=False))
    info = tr.train(ctx.index[-1])
    assert info.gate_verdict != "CANDIDATE" and info.registry_status == ModelRegistryStatus.WATCH.value
    r = reg.get_model(info.model_id)
    assert r.status == ModelRegistryStatus.WATCH and r.metadata["gate_verdict"] == info.gate_verdict
    assert "daily" in r.tags and r.metadata["auto_promoted"] is False and r.metadata["artifact_path"]
    lc = ModelLifecycle(reg, tr, DailyDriftMonitor(S), Audit(), Pre(), Kill(), S)
    lc._record_challenger(info, datetime.now(timezone.utc))
    res = lc.promote(info.model_id, confirm=True)
    assert res.status == "BLOCKED" and any("CANDIDATE required" in x for x in res.reasons)
    assert lc.champion() is None and reg.get_model(info.model_id).status != ModelRegistryStatus.ACTIVE_RESEARCH


def test_drift_triggers_challenger_and_rollback(ctx, tmp_path):
    reg = _registry()
    tr = DailyModelTrainer(ctx, TrialLedger(tmp_path / "t.sqlite"), "logit", 10, None, reg,
                           {"C": 0.1, "retrain_every": 60}, models_dir=tmp_path / "m", knobs=dict(SMALL),
                           gate=CandidateGate(GateConfig(), save=False))
    lc = ModelLifecycle(reg, tr, DailyDriftMonitor(S), Audit(), Pre(), Kill(), S)
    rng = np.random.default_rng(0)
    feats = pd.DataFrame(rng.normal(size=(2000, 5)), columns=list("abcde"))
    ref = feats.assign(score=rng.normal(0.33, 0.02, 2000))
    same = feats.assign(score=rng.normal(0.33, 0.02, 2000))
    shifted = feats.assign(score=rng.normal(0.45, 0.02, 2000))
    quiet = lc.evaluate("2026-01-10", ref, same)
    assert not quiet.drift.retrain and not quiet.trained
    rep = lc.evaluate("2026-01-20", ref, shifted)  # only the SCORE distribution moved
    assert rep.drift.retrain and any("score_drift" in r for r in rep.drift.reasons)
    assert rep.trained and rep.challenger_id
    ch = reg.get_model(rep.challenger_id)
    assert "challenger" in ch.tags and ch.status != ModelRegistryStatus.ACTIVE_RESEARCH
    assert not rep.promotion_recommended  # failing/non-candidate challenger is only recorded

    # promote + rollback with gate-CANDIDATE stand-ins (stubbed trainer; promotion rules are the real ones)
    reg2 = _registry()
    stub = Trainer("CANDIDATE", 1.0)
    lc2 = ModelLifecycle(reg2, stub, DailyDriftMonitor(S), Audit(), Pre(), Kill(), S)
    lc2.evaluate("2026-02-01", ref, shifted)
    assert lc2.promote("m1", confirm=True).status == "PROMOTED"
    stub.sharpe = 2.0
    lc2.evaluate("2026-03-01", ref, shifted)
    assert lc2.promote("m2", confirm=True).status == "PROMOTED" and lc2.champion().model_id == "m2"
    assert lc2.rollback(confirm=True).status == "PROMOTED"
    assert lc2.champion().model_id == "m1"


def test_daily_drift_inputs_include_score(ctx, tmp_path):
    res = _wf(ctx, fit_final=True)
    art = {"model": res.final_model, "calibrator": res.final_calibrator, "feature_names": res.feature_names}
    ref, cur = daily_drift_inputs(ctx, art, ref_days=200, cur_days=60)
    assert "score" in ref.columns and len(ref) > 100 and len(cur) > 50
    assert set(FEATURE_COLUMNS) <= set(ref.columns)
    dec = DailyDriftMonitor(S).check_features(ref, cur)
    assert len(dec.findings) >= 2 and "score" in {f.feature for f in dec.findings}


def test_due_for_retrain_weekly_schedule(ctx, tmp_path):
    reg = _registry()
    assert due_for_retrain(reg, "2026-01-10")[0]
    r = rec("d1", ModelRegistryStatus.WATCH, tags=("daily",), meta={"loop_as_of": "2026-01-05T00:00:00+00:00"})
    r.owner_module = "model_loop"
    reg.register_model(r, confirm=True)
    assert not due_for_retrain(reg, "2026-01-10")[0]
    assert due_for_retrain(reg, "2026-01-12")[0]


def test_cli_parser_daily_train():
    from bist_signal_bot.cli.model_loop_cli import build_parser
    a = build_parser().parse_args(["daily-train", "--kind", "hgb", "--horizon", "10", "--ledger-path", "x.sqlite"])
    assert a.kind == "hgb" and a.horizon == 10 and a.ledger_path == "x.sqlite"


# ------------------------------------------------------------------ neighbour grid (PBO needs >=2 trial columns)
def _train_nb(ctx, tmp_path, kind="logit", params=None):
    led = TrialLedger(tmp_path / "nb.sqlite")
    tr = DailyModelTrainer(ctx, led, kind, 10, None, None, params or {"C": 0.1, "retrain_every": 60},
                           knobs=dict(SMALL), gate=CandidateGate(GateConfig(), save=False))
    return led, tr, tr.train(ctx.index[-1])


def test_neighbor_grid_shape_and_centre_first():
    from bist_signal_bot.model_loop.daily_lifecycle import neighbor_grid
    for kind, c in (("logit", {"C": 0.1}), ("hgb", {"max_depth": 2}), ("meta", {"K": 30})):
        g = neighbor_grid(kind, c)
        assert g[0] == c and 2 <= len(g) <= 5 and len({str(x) for x in g}) == len(g)
    assert min(x["max_depth"] for x in neighbor_grid("hgb", {"max_depth": 2})) >= 2


@pytest.fixture(scope="module")
def ctx_long():
    return _ctx(seed=5, n_sym=30, days=1600)  # PBO/gate need enough active days


def test_neighbor_grid_pbo_defined_ledger_n_and_tag(ctx_long, tmp_path):
    led, tr, info = _train_nb(ctx_long, tmp_path)
    om = info.oos_metrics
    assert om["n_grid_trials"] == 3 and om["n_trials_ledger"] == 3 and om["grid_tag"] == "neighbor_grid"
    assert om["pbo"] is not None and np.isfinite(om["pbo"])
    assert om["primary_params"]["C"] == 0.1  # smoke only; the real selection test is test_runner_daily_fixed_primary.py
    rows = led._query("SELECT params_json FROM trials")
    assert len(rows) == 3 and all("neighbor_grid" in r[0] for r in rows)


def test_neighbor_grid_noise_never_candidate(ctx_long, tmp_path):
    _, _, info = _train_nb(ctx_long, tmp_path)
    assert info.gate_verdict != "CANDIDATE"
