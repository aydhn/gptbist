"""Gate/runner tests: offline, seeded synthetic bars, tmp archive + ledger."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.cli.edge_cli import build_parser
from bist_signal_bot.edge_validation.costs import IntradayCostModel
from bist_signal_bot.edge_validation.gate import DISCLAIMER, CandidateGate, GateConfig
from bist_signal_bot.edge_validation.ledger import TrialLedger
from bist_signal_bot.edge_validation.runner import run_family
from bist_signal_bot.edge_validation.signals import breakout
from bist_signal_bot.intraday.archive import BarArchive

SYMS = ["AAA", "BBB", "CCC", "DDD", "EEE"]


def make_bars(seed: int, days: int = 240, drift: float = 0.0, window: int = 10, sigma: float = 0.004):
    """Random-walk 1h bars (7/day). If drift>0, the bar after a `window` breakout gets +drift."""
    rng = np.random.default_rng(seed)
    day_idx = pd.bdate_range("2024-01-02", periods=days)
    ts = [d + pd.Timedelta(hours=h) for d in day_idx for h in range(10, 17)]
    n = len(ts)
    noise = rng.normal(0, sigma, n)
    vol = rng.uniform(0.8, 1.2, n) * 100_000
    o = np.empty(n); h = np.empty(n); l = np.empty(n); c = np.empty(n)
    prev = 50.0
    for i in range(n):
        o[i] = prev
        r = noise[i]
        if drift and i > window:
            if c[i - 1] > h[i - 1 - window:i - 1].max():
                r += drift
        c[i] = o[i] * (1 + r)
        h[i] = max(o[i], c[i]) * (1 + abs(rng.normal(0, 0.0005)))
        l[i] = min(o[i], c[i]) * (1 - abs(rng.normal(0, 0.0005)))
        prev = c[i]
    df = pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": vol},
                      index=pd.DatetimeIndex(ts, tz="Europe/Istanbul"))
    return df


def fill_archive(path, seed, drift=0.0, days=240):
    a = BarArchive(path=path)
    for k, s in enumerate(SYMS):
        a.upsert_bars(make_bars(seed * 100 + k, days=days, drift=drift), s, "1h", "test")
    return a


class _ZeroCost(IntradayCostModel):
    def half_spread_bps(self, price):
        return 0.0


def zero_cost():
    return _ZeroCost(commission_bps=0.0, bsmv_rate=0.0, exchange_fee_bps=0.0, impact_coef=0.0)


GRID = {"window": [5, 10, 20]}


def run(tmp_path, settings, seed, drift=0.0, placebo=False, cost=None, tag="a", days=240):
    a = fill_archive(tmp_path / f"bars_{tag}.sqlite", seed, drift, days)
    led = TrialLedger(path=tmp_path / f"led_{tag}.sqlite")
    try:
        return run_family("breakout", SYMS, "1h", GRID, a, led, cost or IntradayCostModel.from_settings(settings),
                          horizon_bars=1, placebo=placebo, seed=seed, settings=settings), led
    finally:
        a.close()


def test_signals_use_only_past_data():
    b = make_bars(1, days=40)
    full = breakout(b, 10)
    cut = breakout(b.iloc[:150], 10)
    assert (full[:150] == cut).all()


@pytest.mark.parametrize("placebo", [False, True])
def test_noise_not_found_across_seeds(tmp_path, settings_factory, placebo):
    s = settings_factory()
    cand = 0
    seeds = range(8)
    for sd in seeds:
        # zero costs: only the statistics (not trading costs) have to reject noise
        r, _ = run(tmp_path, s, sd, placebo=placebo, cost=zero_cost(), tag=f"n{sd}{int(placebo)}")
        assert r.report.verdict in ("REJECTED", "INSUFFICIENT_DATA", "CANDIDATE")
        cand += r.report.verdict == "CANDIDATE"
    assert cand / len(seeds) <= 0.10


def test_planted_edge_accepted(tmp_path, settings_factory):
    s = settings_factory()
    r, _ = run(tmp_path, s, 11, drift=0.004, tag="edge")
    rep = r.report
    assert rep.verdict == "CANDIDATE", (rep.failed_criteria, rep.model_dump())
    assert rep.net_sharpe_annual > 0 and rep.leakage_splits_checked == 15 and rep.n_paths == 5
    assert rep.disclaimer == DISCLAIMER
    assert Path(rep.report_path).exists()
    saved = json.loads(Path(rep.report_path).read_text(encoding="utf-8"))
    assert saved["verdict"] == "CANDIDATE" and "No real order sent." in saved["disclaimer"]
    assert Path(rep.report_path).parent.name == "reports"


def test_cost_sensitivity_flips_to_rejected(tmp_path, settings_factory):
    s = settings_factory()
    ok, _ = run(tmp_path, s, 12, drift=0.004, tag="c1")
    assert ok.report.verdict == "CANDIDATE"
    heavy = IntradayCostModel(commission_bps=60.0)
    bad, _ = run(tmp_path, s, 12, drift=0.004, cost=heavy, tag="c2")
    assert bad.report.verdict == "REJECTED"
    assert bad.report.net_mean_daily < ok.report.net_mean_daily


def test_insufficient_data(tmp_path, settings_factory):
    s = settings_factory()
    r, led = run(tmp_path, s, 3, drift=0.004, tag="few", days=8)
    assert r.report.verdict == "INSUFFICIENT_DATA"
    assert "min_events" in r.report.failed_criteria or "min_active_days" in r.report.failed_criteria
    # failed trials still count toward N
    assert led.n_trials("breakout") == len(GRID["window"])


def test_dsr_lower_with_more_trials(tmp_path, settings_factory):
    s = settings_factory()
    a = fill_archive(tmp_path / "b.sqlite", 21, drift=0.004)
    led = TrialLedger(path=tmp_path / "l.sqlite")
    cm = IntradayCostModel.from_settings(s)
    r1 = run_family("breakout", SYMS, "1h", GRID, a, led, cm, horizon_bars=1, settings=s)
    for i in range(30):  # extra (noise) trials by the same researcher
        led.record_trial(f"junk{i}", "breakout", {"i": i}, "1h", "", pd.Series(
            np.random.default_rng(i).normal(0, 0.01, 100), index=pd.date_range("2023-01-02", periods=100, tz="UTC")),
            strategy_family="breakout")
    r2 = run_family("breakout", SYMS, "1h", GRID, a, led, cm, horizon_bars=1, settings=s)
    a.close()
    assert r2.report.n_trials_ledger > r1.report.n_trials_ledger
    assert r2.report.dsr < r1.report.dsr


def test_gate_config_from_settings(settings_factory):
    c = GateConfig.from_settings(settings_factory())
    assert (c.min_events, c.min_active_days, c.dsr_min, c.pbo_max) == (300, 60, 0.95, 0.25)
    assert c.min_positive_path_fraction == 0.7 and c.embargo_days == 1


def test_gate_without_events_is_insufficient(tmp_path, settings_factory):
    led = TrialLedger(path=tmp_path / "l.sqlite")
    rep = CandidateGate(settings=settings_factory()).evaluate("x", None, {}, led, "1h")
    assert rep.verdict == "INSUFFICIENT_DATA"


def test_cli_parser():
    p = build_parser()
    a = p.parse_args(["run", "--family", "breakout", "--interval", "1h", "--symbols", "THYAO", "ASELS", "--placebo"])
    assert a.family == "breakout" and a.symbols == ["THYAO", "ASELS"] and a.placebo
    assert p.parse_args(["run", "--family", "sma_trend", "--all-archived"]).all_archived
    assert p.parse_args(["report", "--latest"]).edge_command == "report"
    with pytest.raises(SystemExit):
        p.parse_args(["run", "--family", "nope"])
