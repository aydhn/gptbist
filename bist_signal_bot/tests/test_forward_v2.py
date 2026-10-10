"""Forward v2: tiered freeze (+versions), placebo, v2 fill semantics in the shadow sim, ML model cache equivalence,
tier-aware report. Offline, temp dirs only. No real order is ever sent."""
import json
import sqlite3

import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
from bist_signal_bot.edge_validation.xsection import LEDGER_SUFFIX_V2, DailyContext
from bist_signal_bot.forward import report as R
from bist_signal_bot.forward import shadow as S
from bist_signal_bot.forward.config import (ForwardConfig, freeze_portfolios, load_portfolios, select_v2)
from bist_signal_bot.forward.placebo import PLACEBO, all_families
from bist_signal_bot.forward.sim import replay
from bist_signal_bot.model_loop.daily_features import FEATURES_VERSION
from bist_signal_bot.model_loop.daily_training import WFConfig, walk_forward
from bist_signal_bot.model_loop.forward_cache import ForwardModelCache
from bist_signal_bot.tests.test_forward_shadow import make_frames
from bist_signal_bot.tests.test_xsection_daily import make_panel


# ------------------------------------------------------------------ ledger / reports fixture
def _ledger(path):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE trials(trial_id TEXT PRIMARY KEY, strategy TEXT NOT NULL, strategy_family TEXT NOT NULL,"
                " params_json TEXT, interval TEXT, universe TEXT, created_at INTEGER NOT NULL, n_obs INTEGER,"
                " sharpe REAL, status TEXT DEFAULT 'ok', ts_blob BLOB, returns_blob BLOB)")

    def add(fam, h, params, sh, fv=True, suffix=LEDGER_SUFFIX_V2):
        tid = f"{fam}{suffix}|1d|u50|h{h}|top8|nors|{json.dumps(params, sort_keys=True)}|s0" + \
              (f"|fv{FEATURES_VERSION}" if fv else "")
        con.execute("INSERT INTO trials VALUES(?,?,?,?,?,?,?,?,?,?,NULL,NULL)",
                    (tid, fam, fam + suffix, json.dumps(params), "1d", f"daily_panel[50]|h{h}|top8|nors", 1, 100, sh,
                     "ok"))

    add("ml_xs_hgb", 5, {"max_depth": 3, "retrain_every": 60}, 0.16)
    add("ml_xs_hgb", 5, {"max_depth": 2, "retrain_every": 60}, 0.20)   # better Sharpe, but report picked depth 3
    add("ml_xs_hgb", 10, {"max_depth": 2, "retrain_every": 60}, 0.11)
    add("xs_momentum", 5, {"lookback": 20, "skip": 0}, 0.05, fv=False)
    add("xs_momentum", 5, {"lookback": 60, "skip": 0}, 0.07, fv=False)
    add("xs_momentum", 10, {"lookback": 60, "skip": 0}, 0.02, fv=False)
    add("xs_reversal", 5, {"lookback": 5}, -0.03, fv=False)
    add("xs_momentum", 5, {"lookback": 999, "skip": 0}, 9.0, fv=False, suffix="_daily_xs_ew")  # OLD statistic: ignored
    con.commit()
    con.close()


def _report(path, name, rows, robust=True, suffix=LEDGER_SUFFIX_V2):
    path.mkdir(parents=True, exist_ok=True)
    (path / name).write_text(json.dumps({"meta": {"robust": robust, "ledger_suffix": suffix, "top_n": 8}, "rows": rows}))


def _row(fam, h, verdict, robust, params, placebo=False):
    return {"family": fam, "horizon": h, "placebo": placebo, "error": None, "robust": robust,
            "verdicts": {"placeholder_commission": verdict, "zero_commission": verdict}, "selected_params": params}


@pytest.fixture
def led(tmp_path):
    lp = tmp_path / "ledger" / "trials.sqlite"
    lp.parent.mkdir()
    _ledger(lp)
    _report(lp.parent / "reports", "daily_all_20260101T000000.json",
            [_row("ml_xs_hgb", 5, "CANDIDATE", True, {"max_depth": 3, "retrain_every": 60}),
             _row("ml_xs_hgb", 10, "REJECTED", False, {"max_depth": 2, "retrain_every": 60}),
             _row("xs_momentum", 5, "CANDIDATE", False, {"lookback": 60, "skip": 0}),  # candidate but NOT robust
             _row("xs_momentum", 5, "CANDIDATE", True, {"lookback": 20, "skip": 0}, placebo=True)])
    # OLD (v1) report claiming everything is a candidate must be ignored; newer v2 file wins
    _report(lp.parent / "reports", "daily_all_20251231T000000.json",
            [_row("xs_reversal", 5, "CANDIDATE", True, {"lookback": 5})], robust=False, suffix="_daily_xs_ew")
    return lp


# ------------------------------------------------------------------ freeze selection / versions
def test_select_v2_tiers_and_placebo(led):
    pf = select_v2(led, list(DAILY_FAMILIES), [5, 10], 8, led.parent / "reports", n_controls=3, placebo_seed=100)
    by = {(p["family"], p["horizon"]): p for p in pf}
    c = by[("ml_xs_hgb", 5)]
    assert c["tier"] == "candidate" and c["params"] == {"max_depth": 3, "retrain_every": 60}  # report params, not best-SR
    assert c["v2_verdict"] == "CANDIDATE" and c["ledger_sharpe"] == pytest.approx(0.16)
    assert sum(p["tier"] == "candidate" for p in pf) == 1
    m = by[("xs_momentum", 5)]  # best v2 trial, NOT the old-statistic 9.0 one; non-robust => control
    assert m["tier"] == "control" and m["role"] == "rule_control" and m["params"]["lookback"] == 60
    plc = [p for p in pf if p["role"] == "placebo"]
    assert sorted((p["horizon"], p["params"]["seed"]) for p in plc) == [(5, 105), (10, 110)]
    assert all(p["tier"] == "control" and p["family"] == "placebo_random" for p in plc)
    assert len({p["id"] for p in pf}) == len(pf)
    assert sum(p["role"] == "rule_control" for p in pf) == 3


def test_tier_override_demotes_candidate_to_watch(led, tmp_path, settings_factory):
    pf = select_v2(led, list(DAILY_FAMILIES), [5, 10], 8, led.parent / "reports", n_controls=2,
                   tier_overrides='{"ml_xs_hgb|5": "watch"}')
    w = [p for p in pf if p["family"] == "ml_xs_hgb" and p["horizon"] == 5][0]
    assert w["tier"] == "watch" and w["role"] == "watch" and w["v2_verdict"] == "CANDIDATE"
    assert not any(p["tier"] == "candidate" for p in pf) and sum(p["role"] == "placebo" for p in pf) == 2
    with pytest.raises(ValueError):
        select_v2(led, list(DAILY_FAMILIES), [5], 8, led.parent / "reports", tier_overrides='{"a|5": "candidate"}')
    # the shipped default demotes ml_xs_hgb h5 (audit: batch-order artefact) -> watch in the real freeze path
    cfg = ForwardConfig.from_settings(settings_factory(), forward_dir=tmp_path / "fwd", ledger_path=led)
    doc = freeze_portfolios(cfg)
    assert doc["n_candidates"] == 0 and doc["n_watch"] == 1
    assert [p["tier"] for p in doc["portfolios"] if p["family"] == "ml_xs_hgb" and p["horizon"] == 5] == ["watch"]


def test_select_without_reports_is_all_control(led, tmp_path):
    pf = select_v2(led, list(DAILY_FAMILIES), [5, 10], 8, tmp_path / "none", n_controls=2)
    assert not any(p["tier"] == "candidate" for p in pf)
    assert any(p["role"] == "placebo" for p in pf)


def test_freeze_v1_then_new_version_never_mutates(led, tmp_path, settings_factory):
    cfg = ForwardConfig.from_settings(settings_factory(FORWARD_TIER_OVERRIDES="{}"), forward_dir=tmp_path / "fwd",
                                      ledger_path=led)
    d1 = freeze_portfolios(cfg)
    f1 = cfg.portfolios_file(1)
    raw1 = f1.read_bytes()
    assert d1["freeze_version"] == 1 and d1["n_candidates"] == 1 and f1.name == "portfolios.json"
    again = freeze_portfolios(cfg)  # no force: untouched
    assert again["content_hash"] == d1["content_hash"] and f1.read_bytes() == raw1
    d2 = freeze_portfolios(cfg, force_new_version=True)
    assert cfg.portfolios_file(2).name == "portfolios.v2.json" and cfg.portfolios_file(2).exists()
    assert d2["freeze_version"] == 2 and d2["previous_content_hash"] == d1["content_hash"]
    assert f1.read_bytes() == raw1 and cfg.portfolios_path == cfg.portfolios_file(2)
    assert load_portfolios(cfg)["content_hash"] == d2["content_hash"]
    d3 = freeze_portfolios(cfg, force_new_version=True)
    assert d3["freeze_version"] == 3 and cfg.portfolios_file(3).exists()
    doc = json.loads(cfg.portfolios_path.read_text())  # tamper -> refused
    doc["portfolios"][0]["top_n"] = 1
    cfg.portfolios_path.write_text(json.dumps(doc))
    with pytest.raises(ValueError, match="hash mismatch"):
        load_portfolios(cfg)


# ------------------------------------------------------------------ placebo
def test_placebo_deterministic_causal_and_symbol_independent():
    fr = make_frames(pd.Timestamp("2026-09-30"), days=120, n_sym=12)
    panel = {k: v for k, v in fr.items() if k.startswith("S")}
    ctx = DailyContext.from_panel(panel, None)
    a = PLACEBO.score(ctx, {"seed": 7})
    assert a.equals(PLACEBO.score(ctx, {"seed": 7})) and not a.equals(PLACEBO.score(ctx, {"seed": 8}))
    assert ((a >= 0) & (a < 1)).all().all()
    cut = DailyContext.from_panel({k: v.iloc[:80] for k, v in panel.items()}, None)
    assert np.allclose(PLACEBO.score(cut, {"seed": 7}).to_numpy(), a.iloc[:80].to_numpy())  # causal
    sub = DailyContext.from_panel({k: panel[k] for k in sorted(panel)[:6]}, None)
    assert np.allclose(PLACEBO.score(sub, {"seed": 7}).to_numpy(), a[sorted(panel)[:6]].to_numpy())
    assert "placebo_random" in all_families() and "placebo_random" not in DAILY_FAMILIES
    assert abs(a.stack().mean() - 0.5) < 0.05


# ------------------------------------------------------------------ v2 fill semantics in the shadow sim
def test_sim_unfillable_entry_to_cash_and_locked_exit_deferral(settings_factory):
    st = settings_factory()
    fr = make_frames(pd.Timestamp("2026-09-30"), days=60, n_sym=6)
    panel = {k: v.copy() for k, v in fr.items() if k.startswith("S")}
    base = DailyContext.from_panel(panel, None, st)
    i, h = 30, 3
    e, x = i + 1, i + h
    t_e, t_x = base.index[e], base.index[x]
    lu = float(base.limit_up.iloc[e, 0])
    panel["S00"].loc[t_e, ["open", "high", "low"]] = lu   # locked limit-up open: entry unfillable
    panel["S00"].loc[t_e, "close"] = lu
    ld = float(base.limit_down.iloc[x, 1])
    panel["S01"].loc[t_x, ["close", "low"]] = ld          # exit close locked limit-down: deferred one session
    panel["S01"].loc[t_x, "high"] = max(float(panel["S01"].loc[t_x, "open"]), ld)
    ctx = DailyContext.from_panel(panel, None, st)
    assert ctx.semantics.entry_policy == "cash" and ctx.semantics.exit_lock_defer
    adv = ctx.adv.iloc[i]
    dec = {"hash": "h1", "portfolio_id": "p", "as_of": str(ctx.index[i].date()), "horizon": h, "top_n": 2,
           "picks": [{"symbol": s, "adv": float(adv[s])} for s in ("S00", "S01")]}
    entries, exits = {}, {}
    nav, new = replay(ctx, [dec], entries, exits, S.cost_models(st), 100000.0)
    ent = entries["h1"]
    for sc in ("zero_commission", "placeholder_commission"):
        assert "S00" not in ent["fills"][sc] and ent["dropped"][sc][0][0] == "S00"
        assert ent["dropped"][sc][0][1].startswith("unfillable_entry")
        assert "S01" in ent["fills"][sc]
    ex = exits["h1"]
    pos = ex["results"]["placeholder_commission"]["positions"]["S01"]
    assert pos["exit_date"] == str(ctx.index[x + 1].date()) and pos["deferred_sessions"] == 1
    assert ex["exit_date"] == str(ctx.index[x + 1].date())
    assert [t for t, _ in new] == ["entry", "exit"]
    # replay again with the persisted records: no new records, identical NAV (idempotent)
    nav2, new2 = replay(ctx, [dec], entries, exits, S.cost_models(st), 100000.0)
    assert new2 == [] and np.allclose(nav.to_numpy(), nav2.to_numpy())
    # the unbought slot stays in cash: invested share is about half of the capital right after entry
    w = nav["nav_zero_commission"].iloc[2]
    assert 0.9 * 100000 < w < 1.1 * 100000


def test_sim_locked_exit_waits_until_unlock(settings_factory):
    """If the next sessions are still locked/unknown, the basket exit is NOT recorded yet (position marked to market)."""
    st = settings_factory()
    fr = make_frames(pd.Timestamp("2026-09-30"), days=60, n_sym=6)
    panel = {k: v.copy() for k, v in fr.items() if k.startswith("S")}
    base = DailyContext.from_panel(panel, None, st)
    i, h = 30, 3
    x = i + h
    ld = float(base.limit_down.iloc[x, 1])
    panel["S01"].loc[base.index[x], ["close", "low"]] = ld
    panel["S01"].loc[base.index[x], "high"] = max(float(panel["S01"].loc[base.index[x], "open"]), ld)
    ctx = DailyContext.from_panel({k: v.iloc[:x + 1] for k, v in panel.items()}, None, st)  # data ends AT the locked day
    adv = ctx.adv.iloc[i]
    dec = {"hash": "h1", "portfolio_id": "p", "as_of": str(ctx.index[i].date()), "horizon": h, "top_n": 1,
           "picks": [{"symbol": "S01", "adv": float(adv["S01"])}]}
    entries, exits = {}, {}
    _, new = replay(ctx, [dec], entries, exits, S.cost_models(st), 100000.0)
    assert [t for t, _ in new] == ["entry"] and "h1" not in exits


# ------------------------------------------------------------------ ML model cache
def _ctx(seed=5, n_sym=30, days=700):
    panel = make_panel(seed, n_sym=n_sym, days=days, momentum=0.0)
    bm = pd.DataFrame({s: d["close"] for s, d in panel.items()}).mean(axis=1)
    return DailyContext.from_panel(panel, bm, min_adv=5e6)


SMALL = dict(min_train_rows=500, min_train_dates=60, cal_min_rows=300)


@pytest.fixture(scope="module")
def mctx():
    return _ctx()


def _same(a, b):
    assert np.array_equal(np.isnan(a), np.isnan(b)) and np.allclose(a[~np.isnan(a)], b[~np.isnan(b)], atol=1e-9)


@pytest.mark.parametrize("kind,params", [("logit", {"C": 0.1}), ("hgb", {"max_depth": 2})])
def test_cache_equals_full_walk_forward_and_retrains_only_when_due(mctx, tmp_path, kind, params):
    cfg = WFConfig(kind=kind, params=params, horizon=5, retrain_every=40, **SMALL)
    n = len(mctx.index)
    R = cfg.retrain_every

    def job(end):
        c = mctx.truncate(end)
        row, info = ForwardModelCache(tmp_path, c, cfg, family="t").score_last()
        _same(row, walk_forward(c, cfg).scores.iloc[-1].to_numpy(float))  # cached == full walk-forward
        assert np.isfinite(row).any() and info["shadow_only"] and info["champion"] is False
        return c, info

    c0, i0 = job(n - 90)                                    # bootstrap: trains every block up to today
    assert len(i0["trained_now"]) == i0["n_blocks"] >= 1
    st = json.loads(next(tmp_path.glob("t__*/state.json")).read_text())
    r_first = int(c0.index.get_loc(pd.Timestamp(st["r_first_date"])))
    B = r_first + (i0["block"] + 1) * R                      # first row of the next block
    _, i1 = job(B - 1 + 1 - 1)                               # last row pos B-2: same block -> nothing retrained
    assert i1["trained_now"] == [] and i1["block"] == i0["block"]
    _, i2 = job(B)                                           # last row pos B-1: still same block
    assert i2["trained_now"] == []
    _, i3 = job(B + 1)                                       # last row pos B: retrain date reached -> exactly one block
    assert i3["trained_now"] == [i0["block"] + 1] and i3["block"] == i0["block"] + 1
    _, i4 = job(B + 3)
    assert i4["trained_now"] == []
    st = json.loads(next(tmp_path.glob("t__*/state.json")).read_text())
    assert st["shadow_only"] is True and st["champion"] is False
    assert st["payload"]["features_version"] == FEATURES_VERSION and st["payload"]["feature_schema_hash"]
    for b in st["blocks"].values():  # leakage guard: training labels end before the retrain date minus embargo
        if not b.get("empty"):
            assert pd.Timestamp(b["max_train_t1"]) < pd.Timestamp(b["retrain_date"])


def test_cache_meta_equivalence_and_refuses_schema_change(mctx, tmp_path):
    fam = DAILY_FAMILIES["ml_xs_meta"]
    p = {"primary": "xs_momentum_1_6", "K": 12, "retrain_every": 40, "label_h": 5, **SMALL}
    c = mctx.truncate(len(mctx.index) - 30)
    row, info = fam.forward_score_row(c, p, tmp_path, tier="control")
    _same(row.to_numpy(float), fam.wf(c, p).scores.iloc[-1].to_numpy(float))
    st_path = next(tmp_path.glob("ml_xs_meta__*/state.json"))
    st = json.loads(st_path.read_text())
    assert st["tiers"] == ["control"] and st["champion"] is False
    # a changed feature schema must never be served from the old cache
    art = sorted(st_path.parent.glob("block_*.joblib"))[-1]
    import joblib
    obj = joblib.load(art)
    obj["feature_schema_hash"] = "deadbeef"
    joblib.dump(obj, art)
    c2 = ForwardModelCache(tmp_path, c, fam._forward_inputs(c, p)[0], fam._forward_inputs(c, p)[1],
                           fam._forward_inputs(c, p)[2], family="ml_xs_meta", extra=fam._forward_inputs(c, p)[3])
    with pytest.raises(ValueError, match="feature schema"):
        c2.score_last()
    st["payload"]["features_version"] = -1
    st_path.write_text(json.dumps(st))
    c3 = ForwardModelCache(tmp_path, c, fam._forward_inputs(c, p)[0], fam._forward_inputs(c, p)[1],
                           fam._forward_inputs(c, p)[2], family="ml_xs_meta", extra=fam._forward_inputs(c, p)[3])
    with pytest.raises(ValueError, match="payload mismatch"):
        c3.score_last()


def test_compute_decision_ml_uses_cache_and_adds_label_h(mctx, tmp_path):
    fam = DAILY_FAMILIES["ml_xs_logit"]
    c = mctx.truncate(len(mctx.index) - 20)
    params = {"C": 0.1, "retrain_every": 40, **SMALL}
    body = S.compute_decision(c, fam, params, 5, c.index[-1], 100000.0, {}, horizon=5, models_dir=tmp_path,
                              tier="candidate")
    assert body["model"]["tier"] == "candidate" and body["model"]["shadow_only"] is True and len(body["picks"]) == 5
    full = fam.score(c, {**params, "label_h": 5}).iloc[-1]
    top = full[c.universe_mask.iloc[-1]].dropna().sort_values(ascending=False).index[:5]
    assert [p["symbol"] for p in body["picks"]] == list(top)


# ------------------------------------------------------------------ report tiers
def test_report_tier_verdict_and_placebo(tmp_path, settings_factory):
    pfs = [{"family": "ml_xs_hgb", "params": {"max_depth": 3}, "horizon": 5, "top_n": 8, "tier": "candidate"},
           {"family": "xs_momentum", "params": {"lookback": 20, "skip": 0}, "horizon": 5, "top_n": 8,
            "tier": "control"},
           {"family": "placebo_random", "params": {"seed": 1}, "horizon": 5, "top_n": 8, "tier": "control",
            "role": "placebo"}]
    st = settings_factory(FORWARD_PORTFOLIOS=json.dumps(pfs))
    cfg = ForwardConfig.from_settings(st, forward_dir=tmp_path / "fwd")
    doc = freeze_portfolios(cfg)
    assert [p["tier"] for p in doc["portfolios"]] == ["candidate", "control", "control"] and doc["n_candidates"] == 1
    idx = pd.bdate_range("2026-01-01", periods=140)
    rng = np.random.default_rng(1)
    cfg.ensure()
    ew = 100000 * np.cumprod(1 + rng.normal(0, 0.005, 140))
    for p, drift in zip(doc["portfolios"], (0.004, 0.0, 0.0)):
        nav = 100000 * np.cumprod(1 + drift + rng.normal(0, 0.002, 140))
        pd.DataFrame({"nav_zero_commission": nav, "nav_placeholder_commission": nav, "ew_nav": ew,
                      "xu100_nav": ew, "cash_nav": 100000 * np.cumprod(np.full(140, 1.0002))},
                     index=idx.rename("date")).to_csv(cfg.nav_dir / f"{p['id']}.csv")
    rep = R.build_report(cfg)
    by = {r["role"] or r["tier"]: r for r in rep["portfolios"]}
    cand, plc = by["candidate"], by["placebo"]
    assert rep["n_candidates"] == 1 and cand["tier"] == "candidate" and cand["v2_verdict"] is None
    assert cand["verdict"] in ("PASS", "FAIL") and "beats_placebo" in cand["criteria"]
    assert cand["vs_placebo"]["cum_excess"] > 0
    assert plc["verdict"] == "CONTROL" and "placebo_edge" in plc
    assert [r for r in rep["portfolios"] if r["tier"] == "control" and r["role"] != "placebo"][0]["verdict"] == "CONTROL"
    assert "closed baskets" in json.dumps(cand["criteria"]) or "baskets>=min_and_hit>=50%" in cand["criteria"]
    assert rep["overall"] in ("FAIL", "INSUFFICIENT", "SUCCESS", "INCONCLUSIVE_PLACEBO_EDGE")
    txt = R.format_report(rep)
    assert "[candidate/" in txt and "OVERALL=" in txt and "No real order sent." in txt
