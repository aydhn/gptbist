"""CLI args (run-daily / run-daily-all), USDTRY plumbing in DailyContext, run-all driver, sector speedup equality."""
import json

import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.cli import edge_cli
from bist_signal_bot.edge_validation import families_daily_macro as fm
from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
from bist_signal_bot.edge_validation.ledger import TrialLedger
from bist_signal_bot.edge_validation.run_all_daily import plan_runs, run_all_daily
from bist_signal_bot.edge_validation.xsection import DailyContext, check_score_causality
from bist_signal_bot.tests.test_xsection_daily import make_panel


def _fx(panel, seed=5):
    idx = next(iter(panel.values())).index
    rng = np.random.default_rng(seed)
    bm = pd.Series(1000 * np.exp(np.cumsum(rng.normal(0.0004, 0.01, len(idx)))), index=idx)
    fx = pd.Series(10 * np.exp(np.cumsum(rng.normal(0.0008, 0.006, len(idx)))), index=idx)
    return bm, fx


@pytest.fixture(scope="module")
def ctx():
    p = make_panel(3, n_sym=20, days=500)
    bm, fx = _fx(p)
    return DailyContext.from_panel(p, bm, min_adv=5e6, usdtry=fx)


# ---------------- parser
def test_parser_run_daily_new_args():
    a = edge_cli.build_parser().parse_args(["run-daily", "--family", "xs_momentum", "--ledger-path", "x.sqlite",
                                            "--report-dir", "rd", "--grid-json", '{"lookback":[60,120]}'])
    assert a.ledger_path == "x.sqlite" and a.report_dir == "rd" and json.loads(a.grid_json) == {"lookback": [60, 120]}
    d = edge_cli.build_parser().parse_args(["run-daily", "--family", "f"])
    assert d.ledger_path is None and d.grid_json is None


def test_parser_run_daily_all():
    a = edge_cli.build_parser().parse_args(["run-daily-all", "--horizons", "3,5", "--families", "a,b", "--top-n", "4",
                                            "--regime-scale", "--ledger-path", "l", "--max-symbols", "10"])
    assert (a.horizons, a.families, a.top_n, a.regime_scale, a.ledger_path, a.max_symbols) == (
        "3,5", "a,b", 4, True, "l", 10)
    assert edge_cli.build_parser().parse_args(["run-daily-all"]).horizons == "3,5,10,15"


def test_bad_grid_json_rejected(capsys):
    a = edge_cli.build_parser().parse_args(["run-daily", "--family", "xs_momentum", "--grid-json", "[1]"])
    assert edge_cli._run_daily(a, None) == 1


# ---------------- USDTRY plumbing
def test_context_carries_and_truncates_usdtry(ctx):
    assert ctx.usdtry is not None and len(ctx.usdtry) == len(ctx.index)
    t = ctx.truncate(200)
    assert len(t.usdtry) == 200 and t.usdtry.equals(ctx.usdtry.iloc[:200])


def test_fx_family_works_without_manual_attach_and_is_causal(ctx):
    fm.FX_SENSITIVITY.set_usdtry(None)
    f, p = DAILY_FAMILIES["xs_fx_sensitivity"], {"beta_window": 60, "thr": 0.5}
    assert np.isfinite(f.score(ctx, p).to_numpy(float)).any()
    check_score_causality(f, ctx, p)


def test_attach_usdtry_helper_still_works():
    p = make_panel(4, n_sym=10, days=300)
    bm, fx = _fx(p)
    c = DailyContext.from_panel(p, bm)
    assert c.usdtry is None
    fm.attach_usdtry(c, fx)
    assert len(c.usdtry) == len(c.index)
    assert np.isfinite(DAILY_FAMILIES["xs_fx_sensitivity"].score(c, {"beta_window": 60, "thr": 0.5}).to_numpy(float)).any()


def test_from_archive_loads_usdtry(monkeypatch):
    import bist_signal_bot.daily.panel as dp
    p = make_panel(6, n_sym=5, days=200)
    bm, fx = _fx(p)
    idx = bm.index
    monkeypatch.setattr(dp, "load_daily_panel", lambda a, s=None: p)
    monkeypatch.setattr(dp, "load_benchmark",
                        lambda a, name="XU100": pd.DataFrame({"close": bm if name == "XU100" else fx}, index=idx))
    c = DailyContext.from_archive(object(), None)
    assert c.usdtry is not None and c.benchmark is not None and len(c.usdtry) == len(c.index)


# ---------------- run-all driver
def test_plan_runs_placebo_once_and_tom_fixed():
    pl = plan_runs(["xs_momentum", "cal_turn_of_month"], [15, 3, 10, 5])
    mom = [r for r in pl if r["family"] == "xs_momentum"]
    assert [r["horizon"] for r in mom if not r["placebo"]] == [3, 5, 10, 15]
    assert [r["horizon"] for r in mom if r["placebo"]] == [10]
    tom = [r for r in pl if r["family"] == "cal_turn_of_month"]
    assert [(r["horizon"], r["placebo"]) for r in tom] == [(5, False), (5, True)]


def test_run_all_daily_end_to_end_temp_ledger(ctx, tmp_path):
    led = TrialLedger(path=tmp_path / "t.sqlite")
    seen = []
    rows = run_all_daily(ctx, ["xs_momentum_12_1", "no_such_family"], [3, 5], 4, led, report_dir=tmp_path / "rep",
                         param_grids={"xs_momentum_12_1": {"lookback": [60], "skip": [5]}}, progress=seen.append)
    assert len(rows) == len(seen) == 6  # 2 horizons + placebo per family
    ok = [r for r in rows if r["family"] == "xs_momentum_12_1"]
    bad = [r for r in rows if r["family"] == "no_such_family"]
    assert all(r["error"] is None and set(r["verdicts"]) == {"placeholder_commission", "zero_commission"} for r in ok)
    assert all(r["error"] for r in bad)  # recorded, batch continued
    assert led.n_trials("xs_momentum_12_1_daily__placebo") >= 1


def test_cli_run_daily_all_writes_reports(ctx, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(edge_cli, "_build_ctx", lambda a, s, ar: (ctx, None))

    class _A:
        def close(self):
            pass
    monkeypatch.setattr(edge_cli, "BarArchive", lambda settings=None: _A())
    rc = edge_cli.main(["run-daily-all", "--horizons", "3,5", "--families", "cal_pre_holiday", "--ledger-path",
                        str(tmp_path / "l.sqlite"), "--report-dir", str(tmp_path / "r")])
    assert rc == 0
    out = capsys.readouterr().out
    assert "cal_pre_holiday" in out and "No real order sent." in out
    assert list((tmp_path / "r").glob("daily_all_*.json")) and list((tmp_path / "r").glob("daily_all_*.md"))
    assert (tmp_path / "l.sqlite").exists()


# ---------------- sector speed-up equals the old implementation
def _old_peer(R, L):
    P = np.full(R.shape, np.nan)
    for i in range(R.shape[0]):
        li, ri = L[i], R[i]
        for c in np.unique(li[np.isfinite(li)]):
            m = (li == c) & np.isfinite(ri)
            if m.any():
                P[i, m] = ri[m].mean()
    return P


def test_sector_peer_mean_equals_loop_and_cache(ctx):
    rng = np.random.default_rng(1)
    R = rng.normal(size=(60, 25))
    R[rng.random(R.shape) < 0.15] = np.nan
    L = rng.integers(1, 5, size=R.shape).astype(float)
    L[rng.random(R.shape) < 0.1] = np.nan
    L[:5] = np.nan
    a, b = fm.XSRelStrengthSector.peer_mean(R, L), _old_peer(R, L)
    assert np.array_equal(np.isnan(a), np.isnan(b)) and np.allclose(a[~np.isnan(a)], b[~np.isnan(b)], atol=1e-12)
    f = DAILY_FAMILIES["xs_rel_strength_sector"]
    c1, c2 = f.clusters(ctx, 4, 120), f.clusters(ctx, 4, 120)
    assert c1.equals(c2) and (4, 120) in ctx.__dict__["_cluster_cache"]
    assert not ctx.truncate(300).__dict__.get("_cluster_cache")
