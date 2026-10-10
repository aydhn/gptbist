"""Forward integrity verification (fail-closed). Read-only except the small checkpoint file.

Checks: hash chains (decisions / outcomes / intents), frozen portfolios content hash, trial-ledger sqlite
(PRAGMA integrity_check + append-only sanity against ``integrity_checkpoint.json``). Simulation only; no real order
is ever sent."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from bist_signal_bot.forward import NO_ORDER
from bist_signal_bot.forward.chain import HashChain
from bist_signal_bot.forward.config import ForwardConfig, _content_hash

CHECKPOINT_NAME = "integrity_checkpoint.json"


def checkpoint_path(cfg: ForwardConfig) -> Path:
    return cfg.forward_dir / CHECKPOINT_NAME


def _load_checkpoint(cfg: ForwardConfig):
    p = checkpoint_path(cfg)
    if not p.exists():
        return None, None
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except Exception as e:  # noqa: BLE001
        return None, f"checkpoint_unreadable:{type(e).__name__}"


def _check_chain(name: str, path: Path, reasons: list) -> dict:
    try:
        v = HashChain(path).verify()
    except Exception as e:  # noqa: BLE001
        reasons.append(f"chain_{name}_unreadable:{type(e).__name__}:{e}")
        return {"ok": False, "n": None}
    if not v["ok"]:
        reasons.append(f"chain_{name}_broken:{v['error']}@line{v['line']}")
    return {"ok": bool(v["ok"]), "n": v["n"], "exists": v.get("exists")}


def _check_portfolios(cfg: ForwardConfig, reasons: list) -> dict:
    out = {}
    try:
        versions = cfg.portfolios_versions()
    except Exception as e:  # noqa: BLE001
        reasons.append(f"portfolios_unreadable:{e}")
        return {"ok": False}
    for ver, path in sorted(versions.items()):
        try:
            doc = json.loads(Path(path).read_text(encoding="utf-8"))
            ok = doc.get("content_hash") == _content_hash(doc)
        except Exception as e:  # noqa: BLE001
            reasons.append(f"portfolios_v{ver}_unreadable:{type(e).__name__}")
            out[ver] = False
            continue
        if not ok:
            reasons.append(f"portfolios_v{ver}_hash_mismatch")
        out[ver] = ok
    return {"ok": all(out.values()), "versions": out}


def _check_ledger(cfg: ForwardConfig, checkpoint, reasons: list) -> dict:
    path = cfg.resolve_ledger_path()
    info = {"path": str(path)}
    if not Path(path).exists():
        reasons.append("ledger_missing")
        return {**info, "ok": False}
    try:
        con = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)
        try:
            ic = [r[0] for r in con.execute("PRAGMA integrity_check").fetchall()]
            n, lo, hi = con.execute("SELECT COUNT(*), MIN(rowid), MAX(rowid) FROM trials").fetchone()
        finally:
            con.close()
    except Exception as e:  # noqa: BLE001
        reasons.append(f"ledger_unreadable:{type(e).__name__}:{e}")
        return {**info, "ok": False}
    ok = True
    if ic != ["ok"]:
        reasons.append(f"ledger_integrity_check_failed:{';'.join(map(str, ic))[:200]}")
        ok = False
    n, lo, hi = int(n or 0), int(lo or 0), int(hi or 0)
    gaps = (hi - lo + 1 - n) if n else 0
    info.update(rows=n, max_rowid=hi, gaps=gaps)
    cp = (checkpoint or {}).get("ledger")
    if cp:
        if n < int(cp.get("rows", 0)):
            reasons.append(f"ledger_rows_decreased:{n}<{cp['rows']}")
            ok = False
        if hi < int(cp.get("max_rowid", 0)):
            reasons.append(f"ledger_max_rowid_decreased:{hi}<{cp['max_rowid']}")
            ok = False
        if gaps > int(cp.get("gaps", 0)):
            reasons.append(f"ledger_rowid_gaps_increased:{gaps}>{cp.get('gaps', 0)}")
            ok = False
    info["ok"] = ok
    return info


def verify_integrity(cfg: ForwardConfig, update_checkpoint: bool = True) -> dict:
    """{status: PASS|FAIL, reasons, checks}. Any exception or unreadable artefact => FAIL."""
    reasons: list = []
    checks: dict = {}
    try:
        cp, cp_err = _load_checkpoint(cfg)
        if cp_err:
            reasons.append(cp_err)
        checks["chains"] = {
            "decisions": _check_chain("decisions", cfg.decisions_path, reasons),
            "outcomes": _check_chain("outcomes", cfg.outcomes_path, reasons),
            "intents": _check_chain("intents", cfg.forward_dir / "intents.jsonl", reasons),
        }
        checks["portfolios"] = _check_portfolios(cfg, reasons)
        checks["ledger"] = _check_ledger(cfg, cp, reasons)
    except Exception as e:  # noqa: BLE001
        reasons.append(f"integrity_error:{type(e).__name__}:{e}")
    status = "PASS" if not reasons else "FAIL"
    res = {"status": status, "reasons": reasons, "checks": checks, "disclaimer": NO_ORDER,
           "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    if status == "PASS" and update_checkpoint and checks["ledger"].get("rows") is not None:
        try:
            led = {k: checks["ledger"][k] for k in ("rows", "max_rowid", "gaps")}
            p = checkpoint_path(cfg)
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(".tmp")
            tmp.write_text(json.dumps({"ledger": led, "updated_at": res["checked_at"]}, indent=2), encoding="utf-8")
            os.replace(tmp, p)
        except Exception as e:  # noqa: BLE001
            res["checkpoint_error"] = str(e)
    return res


def format_integrity(res: dict) -> str:
    lines = [f"Forward butunluk kontrolu: {res['status']}"]
    lines += [f"  neden: {r}" for r in res["reasons"]]
    lines.append(NO_ORDER)
    return "\n".join(lines)
