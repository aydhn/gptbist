"""Batch-level global-multiplicity behaviour: fail-closed trial_id, SMALL_UNIVERSE tag/warning, deferred/provisional
reports, relabel end-to-end. Temp ledgers only. No real order is ever sent."""
import json

import numpy as np
import pandas as pd

from bist_signal_bot.config.settings import get_settings
from bist_signal_bot.edge_validation.global_multiplicity import global_dsr_robust
from bist_signal_bot.edge_validation.ledger import TrialLedger, parse_universe_size
from bist_signal_bot.edge_validation.run_all_daily import relabel_with_snapshot, run_all_daily
from bist_signal_bot.edge_validation.runner_daily import run_family_daily
from bist_signal_bot.edge_validation.xsection import DailyContext
from bist_signal_bot.tests.test_edge_benchmark_excess import GRID, drift_panel

SUF = "_daily_xs_ew2"


def _s(mu, seed, n=400):
    return pd.Series(np.random.default_rng(seed).normal(mu, 0.01, n),
                     index=pd.date_range("2020-01-01", periods=n, freq="B"))


def _fill(led, fam, k, mu, seed0, univ="daily_panel[150]|h5|top8|nors"):
    for i in range(k):
        led.record_trial(f"{fam}|{i}", fam, {"i": i}, "1d", univ, _s(mu, seed0 + i), strategy_family=fam)


def _ctx():
    return DailyContext.from_panel(drift_panel(12, alpha=0.004), min_adv=5e6)


def test_trial_id_never_substituted_on_any_path(tmp_path):
    led = TrialLedger(tmp_path / "t.sqlite")
    _fill(led, "a" + SUF, 4, 0.002, 0)
    for kw in ({}, {"snapshot_rowid": led.snapshot_rowid()}):  # live AND snapshot path
        o = global_dsr_robust(led, "a" + SUF, SUF, trial_id="does-not-exist", **kw)
        assert o["passes"] is None and o["dsr_global"] is None and o["error"]
    ok = global_dsr_robust(led, "a" + SUF, SUF, trial_id="a" + SUF + "|1")
    assert ok["trial_id"] == "a" + SUF + "|1"


def test_small_universe_tag_and_warning(tmp_path, caplog):
    get_settings().GLOBAL_POOL_MIN_UNIVERSE = 100  # conftest fixture restores it
    real, smoke = TrialLedger(tmp_path / "real.sqlite"), TrialLedger(tmp_path / "trials_smoke.sqlite")
    assert smoke.smoke and not real.smoke
    with caplog.at_level("WARNING"):
        run_family_daily("xs_momentum", _ctx(), (5,), GRID, 8, real, save_report=False)
    assert any("GLOBAL_POOL_MIN_UNIVERSE" in r.getMessage() for r in caplog.records)
    unis = [r[0] for r in real._query("SELECT universe FROM trials")]
    assert unis and all("SMALL_UNIVERSE" in u and parse_universe_size(u) == len(_ctx().symbols) for u in unis)
    caplog.clear()
    with caplog.at_level("WARNING"):
        run_family_daily("xs_momentum", _ctx(), (5,), GRID, 8, smoke, save_report=False)
    assert not [r for r in caplog.records if "GLOBAL_POOL_MIN_UNIVERSE" in r.getMessage()]
    assert all("SMALL_UNIVERSE" not in r[0] for r in smoke._query("SELECT universe FROM trials"))


def test_relabel_fails_closed_for_small_universe_without_autouse_override(tmp_path):
    get_settings().GLOBAL_POOL_MIN_UNIVERSE = 100  # undo the conftest override for this test
    led = TrialLedger(tmp_path / "t.sqlite")
    _fill(led, "big" + SUF, 5, 0.003, 0)
    _fill(led, "tiny" + SUF, 5, 0.003, 40, univ="daily_panel[12]|h5|top8|nors|SMALL_UNIVERSE")
    rows = [{"family": f, "placebo": False, "robust_mode": True, "ledger_family": f + SUF,
             "selected_trial_id": f"{f}{SUF}|0", "verdicts": {"placeholder_commission": "CANDIDATE"},
             "robust": True, "robust_failed": [], "failed_criteria": []} for f in ("big", "tiny")]
    relabel_with_snapshot(rows, led, led.snapshot_rowid())
    by = {r["family"]: r for r in rows}
    assert by["tiny"]["verdicts"]["placeholder_commission"] == "REJECTED" and by["tiny"]["global_dsr"]["error"]
    assert by["tiny"]["global_dsr"]["passes"] is None and "global_dsr" in by["tiny"]["robust_failed"]
    assert by["big"]["global_dsr"]["n_global"] == 10  # small trials still counted in honest N


def test_deferred_report_is_marked_provisional(tmp_path):
    res = run_family_daily("xs_momentum", _ctx(), (5,), GRID, 8, TrialLedger(tmp_path / "t.sqlite"),
                           save_report=False, global_gate="deferred")
    assert res.report["provisional"] is True and res.report["verdict"] == "PENDING_GLOBAL"
    assert {d["verdict"] for d in res.report["scenarios"].values()} == {"PENDING_GLOBAL"}
    assert all(d["robustness"]["criteria"]["global_dsr"].get("deferred") for d in res.report["scenarios"].values())
    live = run_family_daily("xs_momentum", _ctx(), (5,), GRID, 8, TrialLedger(tmp_path / "u.sqlite"),
                            save_report=False)
    assert live.report["provisional"] is False


def test_run_all_daily_relabel_end_to_end_and_select_v2(tmp_path):
    from bist_signal_bot.forward.config import select_v2
    ctx = _ctx()
    # (1) pool accepts the small test universe: final CANDIDATE, family file finalized
    led0, meta0 = TrialLedger(tmp_path / "a.sqlite"), {}
    rows0 = run_all_daily(ctx, ["xs_momentum"], [5], 8, led0, param_grids={"xs_momentum": GRID},
                          report_dir=tmp_path / "ra", meta=meta0)
    r0 = next(r for r in rows0 if not r["placebo"])
    assert r0["verdicts"]["placeholder_commission"] == "CANDIDATE" and meta0["snapshot_rowid"] == led0.snapshot_rowid()
    doc0 = json.loads(open(r0["report_path"], encoding="utf-8").read())
    assert doc0["provisional"] is False and doc0["verdict"] == "CANDIDATE"
    # (2) production-like min universe: relabel drops the CANDIDATE, family file rewritten, progress saw PENDING
    get_settings().GLOBAL_POOL_MIN_UNIVERSE = 100
    led, meta, seen = TrialLedger(tmp_path / "b.sqlite"), {}, []
    rows = run_all_daily(ctx, ["xs_momentum"], [5], 8, led, param_grids={"xs_momentum": GRID},
                         report_dir=tmp_path / "rb", meta=meta, progress=lambda r: seen.append(dict(r["verdicts"])))
    r = next(x for x in rows if not x["placebo"])
    assert all(v == "REJECTED" for v in r["verdicts"].values()) and r["global_dsr"]["passes"] is None
    assert "robust:global_dsr" in r["failed_criteria"] and r["robust"] is False
    doc = json.loads(open(r["report_path"], encoding="utf-8").read())
    assert doc["provisional"] is False and doc["global_snapshot_rowid"] == meta["snapshot_rowid"]
    assert doc["verdict"] == "REJECTED"
    assert seen[0]["placeholder_commission"] == "PENDING_GLOBAL"
    # (3) select_v2 sees no candidate from the finalized batch
    rep = tmp_path / "reports"
    rep.mkdir()
    (rep / "daily_all_20260101T000000.json").write_text(json.dumps({
        "meta": {"robust": True, "ledger_suffix": SUF, "top_n": 8, "snapshot_rowid": meta["snapshot_rowid"],
                 "smoke": False}, "rows": rows}, default=str))
    sel = select_v2(led.path, ["xs_momentum"], [5], reports_dir=rep)
    assert not [p for p in sel if p["tier"] == "candidate"]


def test_edge_report_marks_provisional(capsys):
    from bist_signal_bot.cli import edge_cli
    try:
        edge_cli._print_report({"family": "f", "interval": "1d", "verdict": "PENDING_GLOBAL", "provisional": True})
    except KeyError:
        pass  # the rest of the printer needs a full report; the marker is printed first
    assert "PROVISIONAL" in capsys.readouterr().out
