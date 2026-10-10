"""Block I infra: --min-adv trial encoding, delayed-entry report, success_i checklist. Temp ledgers only.
No real order is ever sent."""
import numpy as np

from bist_signal_bot.cli import edge_cli
from bist_signal_bot.edge_validation.costs_daily import DailyCostModel
from bist_signal_bot.edge_validation.entry_delay import delayed_entry_report
from bist_signal_bot.edge_validation.ledger import TrialLedger, parse_universe_size
from bist_signal_bot.edge_validation.runner_daily import run_family_daily
from bist_signal_bot.edge_validation.success_i import ITEMS, evaluate_block_i_success
from bist_signal_bot.edge_validation.xsection import DailyContext, apply_benchmark, build_portfolio_events
from bist_signal_bot.tests.test_edge_benchmark_excess import GRID, drift_panel


def _ctx():
    return DailyContext.from_panel(drift_panel(12, alpha=0.004), min_adv=5e6)


def test_cli_min_adv_arg():
    p = edge_cli.build_parser()
    assert p.parse_args(["run-daily", "--family", "f", "--min-adv", "5e7"]).min_adv == 5e7
    assert p.parse_args(["run-daily-all"]).min_adv is None


def test_min_adv_encoded_and_distinct(tmp_path):
    led = TrialLedger(tmp_path / "t.sqlite")
    base = run_family_daily("xs_momentum", _ctx(), (5,), GRID, 8, led, save_report=False)
    liq = run_family_daily("xs_momentum", _ctx(), (5,), GRID, 8, led, save_report=False, min_adv=5e7)
    assert base.ledger_family.endswith("_daily_xs_ew2") and liq.ledger_family.endswith("_daily_xs_ew2")
    assert "adv5e+07" in liq.ledger_family and liq.ledger_family != base.ledger_family
    ids_b = {t["trial_id"] for t in base.trials}
    ids_l = {t["trial_id"] for t in liq.trials}
    assert ids_b and ids_l and not (ids_b & ids_l) and all("adv5e+07" in i for i in ids_l)
    unis = [r[0] for r in led._query("SELECT universe FROM trials WHERE strategy_family = ?", (liq.ledger_family,))]
    assert unis and all("|adv5e+07" in u and parse_universe_size(u) == len(_ctx().symbols) for u in unis)
    assert liq.report["min_adv"] == 5e7 and base.report["min_adv"] is None
    assert led.n_trials(base.ledger_family) == len(ids_b)  # old family untouched by the liquid run
    assert "entry_delay" in liq.report


def test_default_min_adv_none_keeps_ids(tmp_path):
    a = run_family_daily("xs_momentum", _ctx(), (5,), GRID, 8, TrialLedger(tmp_path / "a.sqlite"), save_report=False)
    assert all("adv" not in t["trial_id"] for t in a.trials) and "_adv" not in a.ledger_family


def test_delayed_entry_report():
    ctx = _ctx()
    cm = DailyCostModel.from_settings(None, scenario="placeholder_commission")
    fam = __import__("bist_signal_bot.edge_validation.families_daily",
                     fromlist=["DAILY_FAMILIES"]).DAILY_FAMILIES["xs_momentum"]
    p = {k: v[0] for k, v in GRID.items()}
    sc = fam.score(ctx, p).reindex(index=ctx.index, columns=ctx.symbols)
    ev = apply_benchmark(ctx, build_portfolio_events(ctx, sc, 5, 4).events, "ew_universe")
    r1 = delayed_entry_report(ctx, ev, 1, cm)
    assert r1["n_events"] == len(ev) and r1["n_valid"] > 0 and r1["delay_sessions"] == 1
    assert np.isfinite(r1["net_excess_mean_bps"]) and np.isfinite(r1["base_net_excess_mean_bps"])
    # delaying the entry to the close of a later session cannot create a free lunch on a drift-less-noise panel: the
    # delayed number must differ (different fill) and a delay >= horizon leaves nothing valid
    assert r1["net_excess_mean_bps"] != r1["base_net_excess_mean_bps"]
    r9 = delayed_entry_report(ctx, ev, 9, cm)
    assert r9["n_valid"] == 0 and r9["net_excess_mean_bps"] is None
    assert delayed_entry_report(ctx, ev.iloc[0:0], 1, cm)["n_valid"] == 0


def test_success_i_missing_keys_false():
    for row in (None, {}, {"verdicts": None, "survivorship": 3}):
        out = evaluate_block_i_success(row)
        assert out["overall"] is False and all(out[k] is False for k in ITEMS)
        assert set(out["explanations_tr"]) == set(ITEMS)


def test_success_i_all_pass():
    row = {"verdicts": {"placeholder_commission": "CANDIDATE"}, "global_dsr": {"passes": True}, "min_adv": 5e7,
           "robust_detail": {"trim_top_events": {"mean_after_bps": 12.0},
                             "year_stability": {"pass": True, "total_excess": 0.2}},
           "survivorship": {"retained_fraction_age_weighted": 0.6, "retained_fraction_excl_recent": 0.5},
           "entry_delay": {"net_excess_mean_bps": 3.0}}
    out = evaluate_block_i_success(row)
    assert out["overall"] is True and out["explanations_tr"] == {}
    row["min_adv"] = 5e6
    out = evaluate_block_i_success(row)
    assert out["overall"] is False and list(out["explanations_tr"]) == ["adv_liquid_trimmed_positive"]
