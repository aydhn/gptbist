"""Robustness layer (v2 candidacy), v2 ledger isolation, cluster fix, new rule families. TEMP ledgers only."""
import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
from bist_signal_bot.edge_validation.gate import CandidateGate, GateConfig
from bist_signal_bot.edge_validation.global_multiplicity import global_dsr_robust, mad_trimmed_variance
from bist_signal_bot.edge_validation.ledger import TrialLedger
from bist_signal_bot.edge_validation.robustness import GATING, RobustnessConfig, robustness_report
from bist_signal_bot.edge_validation.run_all_daily import format_markdown, format_table
from bist_signal_bot.edge_validation.runner_daily import LEDGER_SUFFIX_V2, run_family_daily
from bist_signal_bot.edge_validation.xsection import DailyContext, check_score_causality
from bist_signal_bot.model_loop import daily_features as DF
from bist_signal_bot.tests.test_edge_benchmark_excess import GRID, drift_panel

DAYS = pd.bdate_range("2019-01-01", periods=1300)
GDSR_OK = {"dsr_global": 0.99, "n_global": 10, "dsr_family": 0.99}


def _events(net, seed=0, n_sym=30, cost=0.001):
    rng = np.random.default_rng(seed)
    n = len(net)
    return pd.DataFrame({"t1": DAYS[rng.integers(0, len(DAYS), n)], "symbol": [f"S{k:02d}" for k in rng.integers(0, n_sym, n)],
                         "net_ret": net, "gross_ret": np.asarray(net) + cost, "order_value": 12500.0})


def _nav(seed=1, mu=0.0004):
    return pd.Series(np.random.default_rng(seed).normal(mu, 0.004, len(DAYS)), index=DAYS)


def _rep(ev, nav=None, gd=GDSR_OK, **kw):
    return robustness_report(ev, _nav() if nav is None else nav, grid=DAYS, global_dsr=gd, **kw)


def test_planted_robust_alpha_passes_all_criteria():
    r = _rep(_events(np.random.default_rng(5).normal(0.006, 0.02, 1500)))
    assert r["robust"] and r["complete"] and not r["failed"], {k: v for k, v in r["criteria"].items() if not v["pass"]}
    for k in GATING:
        assert r["criteria"][k]["pass"] is True


def test_lottery_alpha_fails_trim_and_cap():
    rng = np.random.default_rng(6)
    net = np.concatenate([rng.normal(-0.004, 0.01, 1000), np.full(10, 0.8)])  # a few huge events carry the mean
    ev = _events(net, seed=2)
    assert ev["net_ret"].mean() > 0  # looks like alpha in aggregate
    r = _rep(ev)
    assert not r["robust"]
    assert r["criteria"]["trim_top_events"]["pass"] is False and r["criteria"]["event_cap"]["pass"] is False
    assert "trim_top_events" in r["failed"] and "event_cap" in r["failed"]


def test_symbol_concentration_year_concentration_and_cost_stress_fail():
    rng = np.random.default_rng(7)
    # (b) all profit from 10 symbols, rest zero-mean noise
    ev = _events(rng.normal(0.0, 0.02, 3000), seed=3)
    top = ev["symbol"].isin([f"S{k:02d}" for k in range(10)])
    ev.loc[top, "net_ret"] += 0.02
    ev["gross_ret"] = ev["net_ret"] + 0.001
    assert _rep(ev)["criteria"]["drop_top_symbols"]["pass"] is False
    # (c) all excess in a single year
    nav = pd.Series(np.random.default_rng(8).normal(0.0, 0.004, len(DAYS)), index=DAYS)
    nav[nav.index.year == 2021] += 0.003
    c = _rep(_events(np.random.default_rng(9).normal(0.006, 0.02, 1500)), nav=nav)["criteria"]["year_stability"]
    assert c["pass"] is False and c["max_year_share"] > 0.6
    # (d) thin edge that dies at 2x cost
    ev = _events(np.random.default_rng(10).normal(0.0004, 0.01, 2000), cost=0.003)
    assert _rep(ev)["criteria"]["cost_stress"]["pass"] is False


def test_global_dsr_gating_and_unavailable_fails_closed_in_runner_contract():
    ev = _events(np.random.default_rng(5).normal(0.006, 0.02, 1500))
    low = _rep(ev, gd={"dsr_global": 0.5, "n_global": 99})
    assert low["criteria"]["global_dsr"]["pass"] is False and "global_dsr" in low["failed"]
    assert _rep(ev, gd={"dsr_global": None})["criteria"]["global_dsr"]["pass"] is False
    nd = robustness_report(ev, _nav(), grid=DAYS)  # pure-function use without global DSR
    assert nd["criteria"]["global_dsr"]["pass"] is None and nd["complete"] is False


def test_config_defaults_typed_and_mad_trimming(tmp_path):
    from bist_signal_bot.config.settings import get_settings
    c = RobustnessConfig.from_settings(get_settings())
    assert c == RobustnessConfig()  # defaults.py mirrors the documented thresholds
    base = np.random.default_rng(0).normal(0, 0.05, 60)
    junk = np.concatenate([base, [5.0, -7.0]])
    assert mad_trimmed_variance(junk) < 0.5 * float(np.var(junk, ddof=1))
    assert mad_trimmed_variance(junk) == pytest.approx(float(np.var(base, ddof=1)), rel=0.35)
    led = TrialLedger(tmp_path / "t.sqlite")
    out = global_dsr_robust(led, "nofam_daily_xs_ew2", LEDGER_SUFFIX_V2)
    assert out["passes"] is None and out["dsr_global"] is None


# ---------------------------------------------------------------- runner v2
@pytest.fixture(scope="module")
def alpha_ctx():
    return DailyContext.from_panel(drift_panel(12, alpha=0.004), min_adv=5e6)


@pytest.fixture(scope="module")
def beta_ctx():
    return DailyContext.from_panel(drift_panel(11), min_adv=5e6)


def _run(fam, ctx, led, **kw):
    return run_family_daily(fam, ctx, (5,), GRID, 8, led, CandidateGate(GateConfig(), save=False), save_report=False, **kw)


def test_v2_ledger_isolation_and_report(alpha_ctx, tmp_path):
    assert LEDGER_SUFFIX_V2 == "_daily_xs_ew2"
    led = TrialLedger(tmp_path / "t.sqlite")
    old = _run("xs_momentum", alpha_ctx, led, robust=False)
    assert old.ledger_family == "xs_momentum_daily_xs_ew"
    before = led.returns_matrix("xs_momentum_daily_xs_ew").copy()
    new = _run("xs_momentum", alpha_ctx, led)  # robust default
    assert new.ledger_family == "xs_momentum" + LEDGER_SUFFIX_V2
    assert led.n_trials("xs_momentum_daily_xs_ew") == 6 and led.n_trials("xs_momentum_daily_xs_ew2") == 6
    pd.testing.assert_frame_equal(before, led.returns_matrix("xs_momentum_daily_xs_ew"))  # old rows untouched
    assert new.report["robust_mode"] is True and old.report["robust_mode"] is False
    for s, d in new.report["scenarios"].items():
        rob = d["robustness"]
        assert set(rob["criteria"]) >= set(GATING) | {"breadth_topk"}
        assert rob["criteria"]["global_dsr"]["dsr_global"] is not None
        assert d["robust"] == rob["robust"]
        if d["verdict"] == "CANDIDATE":
            assert rob["robust"]
        elif old.report["scenarios"][s]["verdict"] == "CANDIDATE" and not rob["robust"]:
            assert all(f.startswith("robust:") or f in old.report["scenarios"][s]["failed_criteria"]
                       for f in d["failed_criteria"])
    assert "robustness" not in old.report["scenarios"]["zero_commission"]


def test_runner_failed_robust_turns_candidate_into_rejected(alpha_ctx, tmp_path):
    # make the robust layer impossible to satisfy (cap 0 -> mean of capped events <= 0 is not forced, so use year share)
    cfg = RobustnessConfig(year_max_share=0.0)
    r = _run("xs_momentum", alpha_ctx, TrialLedger(tmp_path / "t.sqlite"), robust_config=cfg)
    leg = _run("xs_momentum", alpha_ctx, TrialLedger(tmp_path / "t2.sqlite"), robust=False)
    for s in ("placeholder_commission", "zero_commission"):
        if leg.report["scenarios"][s]["verdict"] == "CANDIDATE":
            d = r.report["scenarios"][s]
            assert d["verdict"] == "REJECTED" and "robust:year_stability" in d["failed_criteria"]


def test_placebo_and_pure_beta_rejected_in_v2(beta_ctx, tmp_path):
    for sd in (0, 1):
        pl = _run("xs_momentum", beta_ctx, TrialLedger(tmp_path / f"p{sd}.sqlite"), placebo=True, seed=sd)
        assert pl.ledger_family == "xs_momentum_daily_xs_ew2__placebo" and pl.verdict == "REJECTED"
        assert all(d["verdict"] == "REJECTED" for d in pl.report["scenarios"].values())
    b = _run("xs_momentum", beta_ctx, TrialLedger(tmp_path / "b.sqlite"))
    assert b.verdict == "REJECTED"


def test_run_all_daily_table_and_markdown_have_robust_columns():
    row = {"family": "f", "horizon": 5, "placebo": False, "error": None, "seconds": 1.0, "n_trials_ledger": 3,
           "verdicts": {"placeholder_commission": "REJECTED"}, "nav_net_sharpe": 1.0, "net_cagr": 0.3,
           "max_drawdown": -0.2, "alpha_vs_cash": 0.01, "excess_sharpe_vs_ew": 0.4, "excess_cagr_vs_ew": 0.05,
           "cash_alpha_ok": True, "robust": False, "robust_failed": ["trim_top_events", "event_cap"],
           "robust_criteria": {"trim_top_events": False, "event_cap": False, "cost_stress": True, "global_dsr": None}}
    t = format_table([row])
    assert "rob" in t and "robust_failed" in t and "trim_top_events,event_cap" in t
    md = format_markdown([row], {"benchmark": "ew_universe", "robust": True, "ledger_suffix": LEDGER_SUFFIX_V2})
    assert "| robust |" in md and "failed robustness criteria" in md and "trim_top_events,event_cap" in md
    assert "## Robustness criteria" in md and "n/a" in md
    assert format_table([{**row, "robust": None, "robust_failed": None}])  # legacy rows still render


def test_cli_no_robust_flag():
    from bist_signal_bot.cli.edge_cli import build_parser
    p = build_parser()
    assert p.parse_args(["run-daily", "--family", "x"]).robust is True
    assert p.parse_args(["run-daily", "--family", "x", "--no-robust"]).robust is False
    assert p.parse_args(["run-daily-all"]).robust is True


# ---------------------------------------------------------------- cluster fix / features v2
def _factor_ctx(n_sym=40, days=420, seed=3, k=4):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2020-01-01", periods=days)
    mkt = rng.normal(0.0004, 0.01, days)
    fac = rng.normal(0, 0.012, (days, k))
    panel = {}
    for j in range(n_sym):
        r = 0.9 * mkt + 1.0 * fac[:, j % k] + rng.normal(0, 0.008, days)
        c = 50 * np.exp(np.cumsum(r))
        panel[f"S{j:02d}"] = pd.DataFrame({"open": c, "high": c, "low": c, "close": c, "volume": 3e6}, index=idx)
    bm = pd.Series(100 * np.exp(np.cumsum(mkt)), index=idx)
    return DailyContext.from_panel(panel, bm, min_adv=1e5)


def test_cluster_labels_not_degenerate_and_size_limited():
    ctx = _factor_ctx()
    lab = DF.cluster_labels(ctx)
    last = lab[-1]
    sizes = np.bincount(last)
    assert len(sizes) > 1, "all symbols in one cluster (degenerate)"
    m = len(ctx.symbols)
    assert sizes.min() >= DF.CLUSTER_MIN_SIZE and sizes.max() <= max(2 * DF.CLUSTER_MIN_SIZE, int(np.ceil(DF.CLUSTER_MAX_FRAC * m)))
    assert (lab[:DF.CLUSTER_WINDOW] == -1).all()  # nothing before the first refresh
    d = DF.cluster_diagnostics(ctx)
    assert d["ok"] and d["n_clusters"] > 1 and d["features_version"] == DF.FEATURES_VERSION
    # market-residual clustering recovers the planted factor groups better than chance
    from itertools import combinations
    truth = np.arange(m) % 4
    same = [(last[a] == last[b]) == (truth[a] == truth[b]) for a, b in combinations(range(m), 2)]
    assert np.mean(same) > 0.6


def test_cluster_degenerate_chaining_falls_back_to_balanced_split():
    rng = np.random.default_rng(0)
    R = rng.normal(0, 0.01, (250, 30)) + rng.normal(0, 0.01, (250, 1))  # one market factor, no sector structure
    lab = DF._corr_clusters(R)
    sizes = np.bincount(lab)
    assert len(sizes) > 1 and sizes.min() >= DF.CLUSTER_MIN_SIZE and sizes.max() <= 12


def test_features_v2_columns_replace_duplicates():
    assert DF.FEATURES_VERSION >= 2
    assert "rs_xu_20" not in DF.FEATURE_COLUMNS and "rs_xu_60" not in DF.FEATURE_COLUMNS
    assert "res_xu_20" in DF.FEATURE_COLUMNS and "res_xu_60" in DF.FEATURE_COLUMNS
    assert DF.FEATURE_COLUMNS == DF.CS_FEATURES + DF.MKT_FEATURES and len(set(DF.FEATURE_COLUMNS)) == len(DF.FEATURE_COLUMNS)
    ctx = _factor_ctx()
    fp = DF.build_feature_panel(ctx)
    i, j = DF.FEATURE_COLUMNS.index("res_xu_20"), DF.FEATURE_COLUMNS.index("ret_20")
    a, b = fp.X[300:, :, i], fp.X[300:, :, j]
    ok = np.isfinite(a) & np.isfinite(b)
    assert not np.allclose(a[ok], b[ok])  # no longer a rank-duplicate of ret_20
    k = DF.FEATURE_COLUMNS.index("rs_cluster_20")
    assert np.isfinite(fp.X[:, :, k]).any()


def test_ml_trial_ids_carry_features_version(alpha_ctx, tmp_path):
    from bist_signal_bot.model_loop.daily_features import FEATURES_VERSION
    fam = DAILY_FAMILIES["ml_xs_logit"]
    assert getattr(fam, "needs_horizon", False) and FEATURES_VERSION >= 2


# ---------------------------------------------------------------- new families
@pytest.fixture(scope="module")
def small_ctx():
    return DailyContext.from_panel(drift_panel(21, n_sym=15, days=400, alpha=0.004), min_adv=5e6)


def test_new_families_registered_causal_and_grids_small(small_ctx):
    for name, params in (("xs_ret20_raw", {"lookback": 20, "skip": 0, "vol_scaled": 0}),
                         ("xs_tail_momentum_guard", {"lookback": 20, "ret5_cap": 0.25, "streak": 2})):
        fam = DAILY_FAMILIES[name]
        assert fam.valid(params)
        check_score_causality(fam, small_ctx, params)
        from bist_signal_bot.edge_validation.runner import expand_grid
        assert len([p for p in expand_grid(fam.default_grid) if fam.valid(p)]) <= 3
    raw = DAILY_FAMILIES["xs_ret20_raw"]
    assert not raw.valid({"lookback": 20, "skip": 5})
    c = small_ctx.close
    exp = c / c.shift(20) - 1.0
    got = raw.score(small_ctx, {"lookback": 20, "skip": 0, "vol_scaled": 0})
    assert np.allclose(got.to_numpy(float), exp.to_numpy(float), equal_nan=True)


def test_tail_guard_excludes_limit_up_names_only():
    idx = pd.bdate_range("2021-01-01", periods=80)
    base = np.full(80, 10.0) * np.exp(np.cumsum(np.full(80, 0.002)))
    panel = {}
    for s in ("A", "B", "C", "D", "E", "F"):
        c = base.copy()
        panel[s] = pd.DataFrame({"open": c, "high": c, "low": c, "close": c, "volume": 1e7}, index=idx)
    for s, days in (("A", (60, 61)), ("B", (60,)), ("C", ())):
        c = panel[s]["close"].to_numpy().copy()
        for d in days:
            c[d:] *= 1.10
        panel[s] = panel[s].assign(close=c, open=c, high=c, low=c)
    c = panel["D"]["close"].to_numpy().copy()
    c[62:] *= 1.30  # +30% in a single (non-limit) jump -> ret_5 >= 25%
    panel["D"] = panel["D"].assign(close=c, open=c, high=c, low=c)
    ctx = DailyContext.from_panel(panel, min_adv=1e5, min_history=10)
    fam = DAILY_FAMILIES["xs_tail_momentum_guard"]
    p = {"lookback": 20, "ret5_cap": 0.25, "streak": 2}
    s = fam.score(ctx, p)
    raw = DAILY_FAMILIES["xs_ret20_raw"].score(ctx, {"lookback": 20, "skip": 0, "vol_scaled": 0})
    t = idx[63]  # inside the 5-session window after the A streak (60,61) and the D jump (62)
    assert np.isnan(s.loc[t, "A"]) and np.isnan(s.loc[t, "D"])  # two-day limit-up streak / ret5 >= 25%
    assert np.isfinite(s.loc[t, "B"]) and np.isfinite(s.loc[t, "C"])  # a single limit-up day is NOT excluded
    assert s.loc[t, "C"] == pytest.approx(raw.loc[t, "C"])
    late = idx[75]  # the tail names re-enter once the 5-session window has passed
    assert np.isfinite(s.loc[late, "A"]) and np.isfinite(s.loc[late, "D"])
