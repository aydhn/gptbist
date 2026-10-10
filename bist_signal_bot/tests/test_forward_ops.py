"""Forward integrity / backup / kill-switch drill tests: tmp dirs only. No real order is ever sent."""
import json
import sqlite3
import zipfile

import pytest

from bist_signal_bot.forward import backup as BK
from bist_signal_bot.forward import integrity as IG
from bist_signal_bot.forward.chain import HashChain
from bist_signal_bot.forward.config import ForwardConfig, _content_hash


def _ledger(path, n=3):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE trials(trial_id TEXT, sharpe REAL)")
    con.executemany("INSERT INTO trials VALUES(?,?)", [(f"t{i}", 0.1) for i in range(n)])
    con.commit()
    con.close()


@pytest.fixture
def cfg(tmp_path, settings_factory):
    st = settings_factory()
    fwd = tmp_path / "fwd"
    fwd.mkdir()
    led = tmp_path / "trials.sqlite"
    _ledger(led)
    c = ForwardConfig.from_settings(st, forward_dir=fwd, ledger_path=led)
    HashChain(c.decisions_path).append("header", {"x": 1})
    HashChain(c.outcomes_path).append("header", {"x": 1})
    doc = {"portfolios": [], "freeze_version": 1}
    doc["content_hash"] = _content_hash(doc)
    (fwd / "portfolios.json").write_text(json.dumps(doc), encoding="utf-8")
    return c


def test_integrity_pass_and_checkpoint(cfg):
    r = IG.verify_integrity(cfg)
    assert r["status"] == "PASS", r["reasons"]
    assert IG.checkpoint_path(cfg).exists()


def test_integrity_detects_chain_tamper(cfg):
    p = cfg.decisions_path
    p.write_text(p.read_text(encoding="utf-8").replace('"x":1', '"x":2'), encoding="utf-8")
    r = IG.verify_integrity(cfg)
    assert r["status"] == "FAIL" and any(x.startswith("chain_decisions_broken") for x in r["reasons"])


def test_integrity_detects_portfolio_tamper(cfg):
    p = cfg.forward_dir / "portfolios.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    d["freeze_version"] = 9
    p.write_text(json.dumps(d), encoding="utf-8")
    assert "portfolios_v1_hash_mismatch" in IG.verify_integrity(cfg)["reasons"]


def test_integrity_ledger_rows_decreased_and_unreadable(cfg, tmp_path):
    assert IG.verify_integrity(cfg)["status"] == "PASS"
    con = sqlite3.connect(cfg.ledger_path)
    con.execute("DELETE FROM trials WHERE rowid=3")
    con.commit()
    con.close()
    r = IG.verify_integrity(cfg)
    assert r["status"] == "FAIL" and any(x.startswith("ledger_rows_decreased") for x in r["reasons"])
    cfg.ledger_path.write_bytes(b"not a sqlite file" * 50)
    r = IG.verify_integrity(cfg)
    assert r["status"] == "FAIL" and any(x.startswith("ledger_unreadable") or "integrity" in x for x in r["reasons"])


def test_integrity_missing_ledger_fails_closed(cfg):
    cfg.ledger_path.unlink()
    assert IG.verify_integrity(cfg)["status"] == "FAIL"


def _root(tmp_path):
    root = tmp_path / "proj"
    (root / "bist_signal_bot" / "config").mkdir(parents=True)
    (root / ".env").write_text("TELEGRAM_BOT_TOKEN=supersecret", encoding="utf-8")
    (root / ".env.example").write_text("A=1", encoding="utf-8")
    (root / "bist_signal_bot" / "config" / "defaults.py").write_text("DEFAULTS={}", encoding="utf-8")
    return root


def test_backup_verify_restore_no_secrets(cfg, tmp_path):
    (cfg.forward_dir / ".env").write_text("SECRET=1", encoding="utf-8")
    (cfg.forward_dir / "api_token.txt").write_text("x", encoding="utf-8")
    res = BK.create_backup(cfg, tmp_path / "bk", root=_root(tmp_path))
    z = res["path"]
    with zipfile.ZipFile(z) as zf:
        names = zf.namelist()
    assert not any(n.endswith(".env") or "token" in n for n in names)
    assert "edge_validation/trials.sqlite" in names and "config/.env.example" in names
    assert BK.verify_backup(z)["status"] == "PASS"
    out = tmp_path / "restored"
    assert BK.restore_backup(z, out)["status"] == "PASS"
    assert (out / "forward" / "portfolios.json").exists()
    assert BK.restore_backup(z, out)["reasons"] == ["target_not_empty"]
    # tamper: rewrite a member -> hash mismatch
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(z) as zin, zipfile.ZipFile(bad, "w") as zout:
        for n in zin.namelist():
            zout.writestr(n, b"tampered" if n == "forward/portfolios.json" else zin.read(n))
    r = BK.verify_backup(bad)
    assert r["status"] == "FAIL" and "hash_mismatch:forward/portfolios.json" in r["reasons"]
    assert BK.verify_backup(tmp_path / "missing.zip")["status"] == "FAIL"


def test_backup_retention_only_own_zips(cfg, tmp_path):
    from datetime import datetime
    dest = tmp_path / "bk"
    dest.mkdir()
    foreign = dest / "forward_backup_20200101_000000.zip"  # matches name but is NOT ours (no manifest)
    foreign.write_bytes(b"x")
    other = dest / "notes.txt"
    other.write_text("keep", encoding="utf-8")
    root = _root(tmp_path)
    for d in range(1, 6):
        BK.create_backup(cfg, dest, keep=3, root=root, now=datetime(2026, 1, d, 10, 0, 0))
    ours = sorted(p.name for p in dest.glob("forward_backup_2026*.zip"))
    assert len(ours) == 3 and ours[0].startswith("forward_backup_20260103")
    assert foreign.exists() and other.exists()


def test_forward_cli_integrity_backup(cfg, tmp_path, capsys):
    from bist_signal_bot.cli import forward_cli
    base = ["--forward-dir", str(cfg.forward_dir), "--ledger-path", str(cfg.ledger_path)]
    assert forward_cli.main(base + ["integrity"]) == 0
    assert forward_cli.main(base + ["backup", "--dest", str(tmp_path / "bk")]) == 0
    z = next((tmp_path / "bk").glob("*.zip"))
    assert forward_cli.main(base + ["restore", str(z), "--verify"]) == 0


def test_kill_switch_drill(tmp_path):
    from bist_signal_bot.security.kill_switch_drill import run_kill_switch_drill
    res = run_kill_switch_drill(workdir=tmp_path)
    assert res["ok"], res["report_tr"]
    assert "BASARILI" in res["report_tr"] and "No real order sent." in res["report_tr"]
