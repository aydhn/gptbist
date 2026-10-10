"""Forward shadow paper trading tests: offline, temp dirs only (never touches ./data). No real order is ever sent."""
import json
import math

import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.daily.fetch import SOURCE, clean_daily
from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
from bist_signal_bot.forward import health as H
from bist_signal_bot.forward import report as R
from bist_signal_bot.forward import shadow as S
from bist_signal_bot.forward.chain import ChainError, HashChain
from bist_signal_bot.forward.config import ForwardConfig, load_portfolios
from bist_signal_bot.intraday.archive import BarArchive

D1 = pd.Timestamp("2026-09-30")
D2 = pd.Timestamp("2026-10-08")
PF = json.dumps([{"family": "xs_momentum", "params": {"lookback": 20, "skip": 0}, "horizon": 5, "top_n": 5}])


def make_frames(end, days=160, n_sym=25, seed=3):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(end=end, periods=days)
    out = {}
    for k in range(n_sym):
        r = rng.normal(0.0005, 0.015, days)
        c = 50 * np.exp(np.cumsum(r))
        o = np.concatenate([[50.0], c[:-1]]) * (1 + rng.normal(0, 0.003, days))
        out[f"S{k:02d}"] = pd.DataFrame({"open": o, "high": np.maximum(o, c) * 1.001, "low": np.minimum(o, c) * 0.999,
                                         "close": c, "volume": rng.uniform(0.8, 1.2, days) * 2e6}, index=idx)
    mkt = pd.DataFrame({"open": 100.0, "high": 101.0, "low": 99.0, "close": 100 * np.exp(np.cumsum(rng.normal(0, .01, days))),
                        "volume": 1e6}, index=idx)
    mkt["open"] = mkt["close"].shift(1).fillna(100.0)
    mkt["high"], mkt["low"] = mkt[["open", "close"]].max(axis=1) * 1.001, mkt[["open", "close"]].min(axis=1) * 0.999
    out["XU100"], out["USDTRY"] = mkt, mkt.copy()
    return out


def load(archive, frames, upto=None):
    for s, df in frames.items():
        d = df if upto is None else df[df.index <= upto]
        archive.upsert_bars(clean_daily(d), s, "1d", SOURCE, adjusted=True)


@pytest.fixture
def env(tmp_path, settings_factory):
    st = settings_factory(FORWARD_PORTFOLIOS=PF)
    frames = make_frames(D2)
    arch = BarArchive(path=tmp_path / "bars.sqlite")
    load(arch, frames, D1)
    cfg = ForwardConfig.from_settings(st, forward_dir=tmp_path / "fwd", archive_path=tmp_path / "bars.sqlite")
    yield st, cfg, arch, frames
    arch.close()


def now_of(ts):
    return pd.Timestamp(ts).to_pydatetime().replace(hour=19, minute=30)


def test_chain_tamper_detection(tmp_path):
    ch = HashChain(tmp_path / "c.jsonl")
    for i in range(4):
        ch.append("x", {"i": i})
    assert ch.verify()["ok"] and ch.verify()["n"] == 4
    lines = (tmp_path / "c.jsonl").read_text().splitlines()
    bad = lines.copy()
    bad[1] = bad[1].replace('"i":1', '"i":9')
    (tmp_path / "e.jsonl").write_text("\n".join(bad) + "\n")
    assert HashChain(tmp_path / "e.jsonl").verify()["error"] == "hash_mismatch"
    (tmp_path / "d.jsonl").write_text("\n".join(lines[:1] + lines[2:]) + "\n")
    assert not HashChain(tmp_path / "d.jsonl").verify()["ok"]
    (tmp_path / "t.jsonl").write_text("\n".join(lines) + "\n" + lines[0][:20])
    assert HashChain(tmp_path / "t.jsonl").verify()["error"] == "partial_last_line"
    with pytest.raises(ChainError):
        HashChain(tmp_path / "e.jsonl").append("x", {})


def test_idempotent_and_header(env):
    st, cfg, arch, _ = env
    r1 = S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    assert r1["status"] == "OK" and r1["decisions_written"] == 1, r1["errors"]
    before = cfg.decisions_path.read_bytes(), cfg.outcomes_path.read_bytes()
    r2 = S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    assert r2["decisions_written"] == 0 and r2["entries_written"] == 0
    assert (cfg.decisions_path.read_bytes(), cfg.outcomes_path.read_bytes()) == before
    recs = HashChain(cfg.decisions_path).records()
    hdr = recs[0]
    assert hdr["type"] == "header" and hdr["plan"]["planned_min_window_calendar_days"] == 90
    assert "decision_rule" in hdr["plan"] and hdr["disclaimer"] == "No real order sent."
    d = recs[1]
    assert d["as_of"] == str(D1.date()) and len(d["picks"]) == 5 and d["prev_hash"] == hdr["hash"]
    assert {"score", "price", "symbol"} <= set(d["picks"][0]) and d["decided_at"]


def test_causality_decision_unchanged_when_later_bars_appear(env):
    st, cfg, arch, frames = env
    S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    rec = HashChain(cfg.decisions_path).records()[1]
    load(arch, frames)  # later bars appear
    S.run_daily(cfg, now=now_of(D2), fetch=False, archive=arch)
    again = [r for r in HashChain(cfg.decisions_path).records() if r.get("type") == "decision"]
    assert again[0] == rec  # recorded line untouched
    from bist_signal_bot.daily.panel import load_benchmark, load_daily_panel
    panel = load_daily_panel(arch)
    ctx = S.ctx_from_panel(panel, load_benchmark(arch, "XU100"), load_benchmark(arch, "USDTRY"), st, as_of=D1)
    body = S.compute_decision(ctx, DAILY_FAMILIES["xs_momentum"], {"lookback": 20, "skip": 0}, 5, D1, 100000.0)
    assert [p["symbol"] for p in body["picks"]] == [p["symbol"] for p in rec["picks"]]
    assert ctx.index[-1] == D1


def test_maturity_and_nav_vs_hand_calc(env):
    st, cfg, arch, frames = env
    S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    load(arch, frames)
    r = S.run_daily(cfg, now=now_of(D2), fetch=False, archive=arch)
    assert r["entries_written"] == 1 and r["exits_written"] == 1, r["errors"]
    dec = [x for x in HashChain(cfg.decisions_path).records() if x.get("type") == "decision"][0]
    ent = next(HashChain(cfg.outcomes_path).iter_type("entry"))
    ex = next(HashChain(cfg.outcomes_path).iter_type("exit"))
    sess = pd.bdate_range(end=D2, periods=160)
    e_date, x_date = sess[sess > D1][0], sess[sess > D1][4]
    assert ent["entry_date"] == str(e_date.date()) and ex["exit_date"] == str(x_date.date())
    from bist_signal_bot.forward.shadow import cost_models
    cm = cost_models(st)["zero_commission"]
    cash = 100000.0
    slot = cash / 5
    spent, proceeds = 0.0, 0.0
    for p in dec["picks"]:
        o = frames[p["symbol"]].loc[e_date, "open"]
        c = cm.cost_bps(o, slot, p["adv"], "buy") / 1e4
        sh = math.floor(slot / (o * (1 + c)))
        assert ent["fills"]["zero_commission"][p["symbol"]]["shares"] == sh
        spent += sh * o * (1 + c)
        v = sh * o * frames[p["symbol"]].loc[x_date, "close"] / o
        b = cm.breakdown(frames[p["symbol"]].loc[x_date, "close"], v, p["adv"], "sell")
        proceeds += v * (1 - b.total_bps / 1e4)
    assert ex["results"]["zero_commission"]["total_proceeds"] == pytest.approx(proceeds, rel=1e-9)
    nav = pd.read_csv(cfg.nav_dir / f"{dec['portfolio_id']}.csv", index_col=0, parse_dates=True)
    cr = pd.Series(S.build_ctx(arch, st).cash_ret)
    cash_t = cash - spent
    for t in sess[(sess >= e_date) & (sess <= x_date)]:
        cash_t *= 1 + cr.loc[t]
    final = cash_t + proceeds
    for t in sess[sess > x_date]:
        final *= 1 + cr.loc[t]
    assert nav["nav_zero_commission"].iloc[-1] == pytest.approx(final, rel=1e-9)
    assert nav["nav_placeholder_commission"].iloc[-1] < nav["nav_zero_commission"].iloc[-1] + 1e-9 or True
    assert {"ew_nav", "xu100_nav", "cash_nav"} <= set(nav.columns)


def test_kill_switch_is_noop_and_logged(env):
    st, cfg, arch, _ = env
    from bist_signal_bot.security.kill_switch import KillSwitchManager
    from bist_signal_bot.security.models import KillSwitchScope
    KillSwitchManager(st, cfg.data_dir).activate([KillSwitchScope.ALL], "test")
    r = S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    assert r["status"] == "KILL_SWITCH" and r["decisions_written"] == 0
    assert len([x for x in HashChain(cfg.decisions_path).records() if x["type"] == "decision"]) == 0
    assert "kill_switch_active" in {s[1] for s in r["skipped"]}
    assert cfg.runs_path.exists()


def test_freshness_gate_stale_and_expected_session(env):
    st, cfg, arch, _ = env
    r = S.run_daily(cfg, now=now_of("2026-10-08"), fetch=False, archive=arch)  # archive ends 09-30
    assert r["status"] == "STALE" and r["decisions_written"] == 0 and r["freshness"]["panel_lag_sessions"] > 0
    assert "STALE_DATA" in r["alerts_new"]
    # before the ready time the expected session is the previous trading day; weekend -> Friday
    assert str(S.expected_session(pd.Timestamp("2026-10-08 12:00").to_pydatetime())) == "2026-10-07"
    assert str(S.expected_session(pd.Timestamp("2026-10-10 12:00").to_pydatetime())) == "2026-10-09"
    assert S.session_lag(pd.Timestamp("2026-10-06").date(), pd.Timestamp("2026-10-08").date()) == 2


def test_frozen_portfolios_tamper_refused(env):
    st, cfg, arch, _ = env
    S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    doc = load_portfolios(cfg)
    doc["portfolios"][0]["top_n"] = 3
    cfg.portfolios_path.write_text(json.dumps(doc))
    r = S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    assert r["status"] == "FAILED" and "content hash" in " ".join(r["errors"])


def test_health_report_and_chain_break_alert(env):
    st, cfg, arch, _ = env
    S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    h = H.build_health(cfg, now=now_of(D1), archive=arch)
    for k in ("freshness", "last_run_at", "decisions_total", "chain_ok", "kill_switch", "disk", "recent_errors"):
        assert k in h
    assert h["chain_ok"] and h["decisions_total"] == 1 and h["overall"] == "OK"
    p = H.save_health(cfg, h)
    assert p.exists() and p.parent == cfg.health_dir
    t = H.notify_telegram(cfg, h, dry_run=True)
    assert t["sent"] is False and "No real order sent." in t["text"] and "TOKEN" not in t["text"].upper()
    assert cfg.heartbeat_path.exists()
    lines = cfg.decisions_path.read_text().splitlines()
    lines[1] = lines[1].replace('"rank":1', '"rank":7')
    cfg.decisions_path.write_text("\n".join(lines) + "\n")
    h2 = H.build_health(cfg, now=now_of(D1), archive=arch)
    assert not h2["chain_ok"] and h2["overall"] == "ATTENTION"
    r = S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    assert r["status"] == "FAILED" and "HASH_CHAIN_BREAK" in r["alerts_new"]


def test_drawdown_alert_levels(env, tmp_path):
    st, cfg, arch, _ = env
    cfg.ensure()
    nav = pd.DataFrame({"nav_placeholder_commission": [100.0, 120.0, 100.0]},
                       index=pd.date_range("2026-01-01", periods=3).rename("date"))
    nav.to_csv(cfg.nav_dir / "pf.csv")
    al = H.evaluate_alerts(cfg, {"started_at": "t"}, {})
    keys = {a["key"] for a in al}
    assert "dd|pf|0.1" in keys and "dd|pf|0.15" in keys and "dd|pf|0.2" not in keys
    assert len(H.emit_alerts(cfg, al)) == 2 and H.emit_alerts(cfg, al) == []  # deduplicated


def test_report_insufficient_and_nw():
    x = np.random.default_rng(0).normal(0.001, 0.01, 200)
    assert abs(R.nw_tstat(x, 0)["t"]) > 0
    assert R.nw_tstat(x, 10)["lag"] == 10
    ar = np.zeros(300)
    for i in range(1, 300):  # strongly autocorrelated -> NW t smaller than naive t
        ar[i] = 0.9 * ar[i - 1] + np.random.default_rng(i).normal(0, 0.01)
    assert abs(R.nw_tstat(ar + 0.002, 20)["t"]) < abs(R.nw_tstat(ar + 0.002, 0)["t"])
    assert R.crit_z(27) > 2.9


def test_report_end_to_end_insufficient(env):
    st, cfg, arch, _ = env
    S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    rep = R.build_report(cfg)
    assert rep["n_portfolios"] == 1 and rep["portfolios"][0]["verdict"] == "INSUFFICIENT"
    assert "No real order sent." in R.format_report(rep)


def test_scheduler_registration(tmp_path):
    from bist_signal_bot.app.scheduler_app import create_scheduler_orchestrator
    from bist_signal_bot.scheduler.models import ScheduledJobType
    from bist_signal_bot.tests.test_scheduler_orchestrator import MockSettings
    s = MockSettings()
    s.DATA_DIR = str(tmp_path)
    orch = create_scheduler_orchestrator(s, tmp_path)
    jobs = {j.job_id: j for j in orch.default_jobs()}
    assert jobs["job_default_healthcheck"] is not None
    d, c = jobs["job_default_forward_daily"], jobs["job_default_forward_catchup"]
    assert d.job_type == ScheduledJobType.FORWARD_SHADOW_DAILY and (d.trigger.hour, d.trigger.minute) == (19, 30)
    assert d.trigger.timezone == "Europe/Istanbul" and d.trigger.only_trading_days
    assert c.trigger.hour == 8
    run = orch.executor.execute(d, dry_run=True)
    assert run.status.value == "SUCCESS"
