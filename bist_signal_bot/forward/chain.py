"""Append-only, hash-chained JSONL ledger (tamper evident). Simulation only; no real order is ever sent."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Iterator, Optional

GENESIS = "0" * 64


class ChainError(RuntimeError):
    pass


def _clean(o):
    if isinstance(o, float):
        return None if (math.isnan(o) or math.isinf(o)) else o
    if isinstance(o, dict):
        return {str(k): _clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_clean(v) for v in o]
    if hasattr(o, "item") and not isinstance(o, (str, bytes)):  # numpy scalar
        try:
            return _clean(o.item())
        except Exception:  # noqa: BLE001
            return str(o)
    return o


def record_hash(rec: dict) -> str:
    body = {k: v for k, v in rec.items() if k != "hash"}
    blob = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class HashChain:
    """One JSON object per line: seq, type, prev_hash, hash (sha256 of the canonical record without ``hash``)."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    # ---- reading ----
    def records(self) -> list:
        out = []
        if not self.path.exists():
            return out
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        break
        return out

    def iter_type(self, typ: str) -> Iterator[dict]:
        return (r for r in self.records() if r.get("type") == typ)

    def verify(self) -> dict:
        """{ok, n, error, line}. Detects edited, deleted, reordered, inserted or truncated-mid-line records."""
        if not self.path.exists():
            return {"ok": True, "n": 0, "error": None, "line": None, "head": GENESIS, "exists": False}
        prev, n = GENESIS, 0
        raw = self.path.read_bytes()
        if raw and not raw.endswith(b"\n"):
            return {"ok": False, "n": 0, "error": "partial_last_line", "line": raw.count(b"\n") + 1, "head": prev,
                    "exists": True}
        for ln, line in enumerate(raw.decode("utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                return {"ok": False, "n": n, "error": "invalid_json", "line": ln, "head": prev, "exists": True}
            if rec.get("seq") != n:
                return {"ok": False, "n": n, "error": "seq_mismatch", "line": ln, "head": prev, "exists": True}
            if rec.get("prev_hash") != prev:
                return {"ok": False, "n": n, "error": "prev_hash_mismatch", "line": ln, "head": prev, "exists": True}
            if rec.get("hash") != record_hash(rec):
                return {"ok": False, "n": n, "error": "hash_mismatch", "line": ln, "head": prev, "exists": True}
            prev, n = rec["hash"], n + 1
        return {"ok": True, "n": n, "error": None, "line": None, "head": prev, "exists": True}

    # ---- writing ----
    def append(self, typ: str, payload: dict) -> dict:
        v = self.verify()
        if not v["ok"]:
            raise ChainError(f"{self.path.name}: refusing to append to a broken chain ({v['error']} at line {v['line']})")
        rec = {"seq": v["n"], "type": typ, "prev_hash": v["head"]}
        rec.update(_clean(payload))
        rec["hash"] = record_hash(rec)
        line = json.dumps(rec, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str) + "\n"
        with open(self.path, "ab") as f:
            f.write(line.encode("utf-8"))
            f.flush()
            os.fsync(f.fileno())
        return rec

    def head(self) -> Optional[str]:
        v = self.verify()
        return v["head"] if v["n"] else None
