"""Forward receipt / intent journal tests: offline, temp dirs only. No real order is ever sent."""
import json

import pytest

from bist_signal_bot.forward import receipt as RC
from bist_signal_bot.forward import shadow as S
from bist_signal_bot.forward.chain import HashChain
from bist_signal_bot.forward.config import ForwardConfig
from bist_signal_bot.intraday.archive import BarArchive
from bist_signal_bot.tests.test_forward_shadow import D1, D2, PF, load, make_frames, now_of


@pytest.fixture
def env(tmp_path, settings_factory):
    st = settings_factory(FORWARD_PORTFOLIOS=PF, FORWARD_RECEIPT_TIERS="control,watch,candidate")
    frames = make_frames(D2)
    arch = BarArchive(path=tmp_path / "bars.sqlite")
    load(arch, frames, D1)
    cfg = ForwardConfig.from_settings(st, forward_dir=tmp_path / "fwd", archive_path=tmp_path / "bars.sqlite")
    yield cfg, arch, frames
    arch.close()


def pid_of(cfg):
    return json.loads(cfg.portfolios_path.read_text(encoding="utf-8"))["portfolios"][0]["id"]


def test_first_receipt_buys_within_capital_and_text(env):
    cfg, arch, _ = env
    S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    r = RC.build_receipt(cfg, pid_of(cfg))
    assert r["status"] == "OK" and len(r["buy"]) == 5 and r["sell"] == []
    assert sum(b["value"] for b in r["buy"]) <= 100000.0 and r["cash"] >= 0
    assert r["invested"] + r["cash"] == pytest.approx(100000.0)
    txt = RC.render_receipt_tr(r)
    assert "Gerçek emir gönderilmedi. Yalnız paper/simülasyon." in txt and "No real order sent." in txt
    assert "AL (ne alacağım)" in txt and "Nakit" in txt


def test_buy_sell_diff_vs_previous_holdings(env):
    cfg, arch, frames = env
    S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    pid = pid_of(cfg)
    dec = HashChain(cfg.decisions_path)
    d0 = next(dec.iter_type("decision"))
    # synthetic next decision: keep 3 names, swap 2 (appended to the real chain, as run_daily would)
    new = [dict(p) for p in d0["picks"][:3]] + [dict(d0["picks"][3], symbol="S90"), dict(d0["picks"][4], symbol="S91")]
    dec.append("decision", {"portfolio_id": pid, "as_of": "2026-10-07", "horizon": 5, "picks": new, "disclaimer": "x"})
    run = json.loads(cfg.runs_path.read_text().splitlines()[-1])
    run["as_of"] = "2026-10-07"
    cfg.runs_path.write_text(json.dumps(run) + "\n", encoding="utf-8")
    r = RC.build_receipt(cfg, pid, "2026-10-07")
    assert {b["symbol"] for b in r["buy"]} >= {"S90", "S91"}
    assert {s["symbol"] for s in r["sell"]} == {p["symbol"] for p in d0["picks"][3:]}
    assert all(s["reason"] for s in r["sell"]) and sum(b["value"] for b in r["buy"]) <= 100000.0


def test_stale_gives_no_decisions(env):
    cfg, arch, _ = env
    S.run_daily(cfg, now=now_of(D2), fetch=False, archive=arch)  # archive ends D1 -> stale gate
    r = RC.build_receipt(cfg, pid_of(cfg))
    assert r["status"] == "STALE" and r["buy"] == [] and r["sell"] == []
    txt = RC.render_receipt_tr(r)
    assert "KARAR YOK (veri bayat)" in txt and "Gerçek emir gönderilmedi." in txt
    assert RC.write_intents(cfg, r) == []


def test_missing_runs_is_stale(env):
    cfg, arch, _ = env
    S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    cfg.runs_path.unlink()
    assert RC.build_receipt(cfg, pid_of(cfg))["status"] == "STALE"


def test_intents_chain_valid_idempotent_and_files(env):
    cfg, arch, _ = env
    S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    before = cfg.decisions_path.read_bytes()
    res = RC.run_receipts(cfg)
    assert len(res) == 1 and res[0][1].exists() and res[0][1].name == f"2026-09-30_{pid_of(cfg)}.txt"
    ch = HashChain(RC.intents_path(cfg))
    assert ch.verify()["ok"]
    its = list(ch.iter_type("intent"))
    assert len(its) == 5 and all(i["no_real_order_sent"] is True and i["side"] == "BUY" for i in its)
    RC.run_receipts(cfg)  # idempotent
    assert len(list(HashChain(RC.intents_path(cfg)).iter_type("intent"))) == 5
    assert cfg.decisions_path.read_bytes() == before
    assert HashChain(cfg.decisions_path).verify()["ok"] and HashChain(cfg.outcomes_path).verify()["ok"]
    r = S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)  # shadow still runs fine
    assert r["status"] == "OK" and not r["errors"]


def test_default_tier_is_watch_only(env, tmp_path, settings_factory):
    cfg, _, _ = env
    cfg2 = ForwardConfig.from_settings(settings_factory(FORWARD_PORTFOLIOS=PF), forward_dir=cfg.forward_dir,
                                       archive_path=cfg.archive_path)
    assert RC.receipt_tiers(cfg2) == {"watch"}
    assert RC.run_receipts(cfg2) == []  # fixture portfolio is a control
