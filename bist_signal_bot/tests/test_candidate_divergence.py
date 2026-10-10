"""Candidate divergence (forward live vs backtest replay): offline, temp dirs. No real order is ever sent."""
import json

import pandas as pd

from bist_signal_bot.daily.fetch import SOURCE, clean_daily
from bist_signal_bot.evidence import candidate_divergence as CD
from bist_signal_bot.forward import shadow as S
from bist_signal_bot.forward.config import load_portfolios
from bist_signal_bot.tests.test_forward_shadow import D1, D2, env, load, now_of  # noqa: F401


def _pid(cfg):
    return load_portfolios(cfg)["portfolios"][0]["id"]


def test_no_live_data_is_clean(env):
    st, cfg, arch, _ = env
    from bist_signal_bot.forward.config import freeze_portfolios
    doc = freeze_portfolios(cfg)
    r = CD.candidate_divergence(cfg, doc["portfolios"][0]["id"])
    assert r["status"] == "NO_LIVE_DATA" and r["live_days"] == 0 and r["checks"] == []
    out = CD.run_all(cfg)
    assert out and all(x["status"] == "NO_LIVE_DATA" for x in out)
    md = open(out[0]["md_path"], encoding="utf-8").read()
    assert "Gerçek emir gönderilmedi" in md and "# Aday Sapma Raporu" in md
    assert json.load(open(out[0]["json_path"], encoding="utf-8"))["disclaimer"] == "No real order sent."
    assert (cfg.forward_dir / "divergence").is_dir()


def _live_then_restate(env, shift):
    st, cfg, arch, frames = env
    S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    load(arch, frames)
    S.run_daily(cfg, now=now_of(D2), fetch=False, archive=arch)
    if shift:  # history restated after the live fills: modeled open fill differs from the persisted live fill
        entry = pd.bdate_range(D1, periods=2)[1]
        for s, df in frames.items():
            if s.startswith("S"):
                d = df.copy()
                cols = ["open", "low"]
                d.loc[entry, cols] = d.loc[entry, cols] * (1 - shift)
                arch.upsert_bars(clean_daily(d[d.index <= D2]), s, "1d", SOURCE, adjusted=True)
    return cfg


def test_gap_stats_computed_zero_when_consistent(env):
    cfg = _live_then_restate(env, 0.0)
    r = CD.candidate_divergence(cfg, _pid(cfg), archive=env[2])
    assert r["status"] == "OK" and r["live_days"] >= 3
    assert abs(r["fill"]["fill_gap_bps_mean"]) < 1e-6 and r["fill"]["fills_compared"] > 0
    assert abs(r["mean_daily_gap_bps"]) < 1e-6
    assert r["any_breach"] is False
    ids = {c["id"]: c for c in r["checks"]}
    assert ids["cum_excess_dd"]["breached"] is None  # < 120 live sessions: not evaluable


def test_thresholds_flagged(env):
    cfg = _live_then_restate(env, 0.01)  # modeled open 1% lower -> live fill ~ +100 bps worse
    r = CD.candidate_divergence(cfg, _pid(cfg), archive=env[2])
    assert r["status"] == "OK"
    assert 90 < r["fill"]["fill_gap_bps_mean"] < 110
    ids = {c["id"]: c for c in r["checks"]}
    assert ids["fill_gap"]["breached"] is True and r["any_breach"] is True
    assert ids["unfilled_entries"]["breached"] is False
    assert r["tracking_error_ann"] is not None
    md = CD.format_markdown(r)
    assert "İHLAL" in md and "Gerçek emir gönderilmedi" in md
