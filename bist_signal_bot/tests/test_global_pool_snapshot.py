"""Global-multiplicity pool: snapshot determinism, universe filter, N_eff, smoke ledger isolation."""
import itertools

import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.global_multiplicity import global_dsr_robust
from bist_signal_bot.edge_validation.ledger import TrialLedger, default_ledger_path, parse_universe_size
from bist_signal_bot.edge_validation.run_all_daily import relabel_with_snapshot

SUF = "_daily_xs_ew2"


def _s(mu, seed, n=400, base=None):
    rng = np.random.default_rng(seed)
    x = rng.normal(mu, 0.01, n)
    if base is not None:
        x = 0.95 * base + 0.05 * x
    return pd.Series(x, index=pd.date_range("2020-01-01", periods=n, freq="B"))


def _fill(led, fam, k, mu, seed0, univ="daily_panel[150]|h5|top8|nors", base=None):
    for i in range(k):
        led.record_trial(f"{fam}|{i}", fam, {"i": i}, "1d", univ, _s(mu, seed0 + i, base=base), strategy_family=fam)


def test_snapshot_rowid_and_filters(tmp_path):
    led = TrialLedger(tmp_path / "t.sqlite")
    assert led.snapshot_rowid() == 0
    _fill(led, "a" + SUF, 3, 0.001, 0)
    snap = led.snapshot_rowid()
    _fill(led, "b" + SUF, 2, 0.0, 50)
    assert led.n_trials() == 5 and led.n_trials(max_rowid=snap) == 3
    assert led.trial_sharpes(max_rowid=snap).size == 3
    assert led.returns_matrix(max_rowid=snap).shape[1] == 3
    assert parse_universe_size("daily_panel[150]|h5") == 150 and parse_universe_size("x") is None


def test_small_universe_excluded_from_pool(tmp_path):
    led = TrialLedger(tmp_path / "t.sqlite")
    _fill(led, "a" + SUF, 4, 0.001, 0)
    _fill(led, "smoke" + SUF, 30, 0.0, 100, univ="daily_panel[12]|h5|top8|nors|SMALL_UNIVERSE")
    full = global_dsr_robust(led, "a" + SUF, SUF)
    filt = global_dsr_robust(led, "a" + SUF, SUF, min_universe=100)
    assert full["n_global"] == 34 and filt["n_global"] == 34  # honest N never shrinks
    assert filt["small_universe_count"] == 30 and full["small_universe_count"] == 0
    assert filt["variance_raw"] != full["variance_raw"]  # but small-universe Sharpes leave the dispersion
    below = global_dsr_robust(led, "smoke" + SUF, SUF, min_universe=100)
    assert below["passes"] is None and below["error"]


def test_n_effective_le_raw_and_gating_uses_raw(tmp_path):
    led = TrialLedger(tmp_path / "t.sqlite")
    base = _s(0.0, 999).to_numpy()
    _fill(led, "a" + SUF, 12, 0.001, 0, base=base)  # highly correlated trials
    _fill(led, "b" + SUF, 3, 0.0, 500)
    o = global_dsr_robust(led, "a" + SUF, SUF)
    assert o["n_global"] == 15 and 1 <= o["n_effective"] <= o["n_global"]
    assert o["n_effective"] < o["n_global"]
    assert o["dsr_global_neff"] is not None
    assert o["passes"] == bool(o["dsr_global"] >= o["dsr_min"])  # gate uses raw N


def test_snapshot_freezes_pool_and_requires_family_inside(tmp_path):
    led = TrialLedger(tmp_path / "t.sqlite")
    _fill(led, "a" + SUF, 4, 0.002, 0)
    snap = led.snapshot_rowid()
    before = global_dsr_robust(led, "a" + SUF, SUF, snapshot_rowid=snap)
    _fill(led, "b" + SUF, 40, 0.0, 200)
    after = global_dsr_robust(led, "a" + SUF, SUF, snapshot_rowid=snap)
    assert before["dsr_global"] == after["dsr_global"] and after["n_global"] == 4
    live = global_dsr_robust(led, "a" + SUF, SUF)
    assert live["n_global"] == 44
    out = global_dsr_robust(led, "b" + SUF, SUF, snapshot_rowid=snap)
    assert out["passes"] is None and out["error"]


def test_relabel_is_order_invariant(tmp_path):
    fams = {"f1": (0.003, 0), "f2": (0.0005, 40), "f3": (0.0, 80)}
    results = []
    for perm in itertools.permutations(fams):
        led = TrialLedger(tmp_path / f"{'_'.join(perm)}.sqlite")
        rows = []
        for f in perm:
            mu, sd = fams[f]
            _fill(led, f + SUF, 5, mu, sd)
            rows.append({"family": f, "placebo": False, "robust_mode": True, "ledger_family": f + SUF,
                         "selected_trial_id": f"{f}{SUF}|0", "verdicts": {"placeholder_commission": "CANDIDATE"},
                         "robust": True, "robust_failed": [], "failed_criteria": []})
        relabel_with_snapshot(rows, led, led.snapshot_rowid())
        results.append({r["family"]: (r["verdicts"]["placeholder_commission"], r["global_dsr"]["dsr_global"])
                        for r in rows})
    assert all(r == results[0] for r in results[1:])
    assert any(v[0] == "REJECTED" for v in results[0].values())  # the check really bites


def test_smoke_ledger_isolated(tmp_path):
    from bist_signal_bot.config.settings import Settings
    s = Settings()
    s.DATA_DIR = tmp_path
    real, smoke = default_ledger_path(s), default_ledger_path(s, smoke=True)
    assert real.name == "trials.sqlite" and smoke.name == "trials_smoke.sqlite" and real != smoke
    led = TrialLedger(settings=s, smoke=True)
    assert led.smoke and led.path == smoke and not TrialLedger(tmp_path / "x.sqlite").smoke
    _fill(led, "a" + SUF, 2, 0.0, 0)
    assert not real.exists() or TrialLedger(real).n_trials() == 0
