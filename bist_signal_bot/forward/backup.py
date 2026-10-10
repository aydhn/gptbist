"""Forward backup: timestamped zip (forward dir + consistent trial-ledger snapshot + non-secret configs) with a sha256
manifest, verify/restore, retention. NEVER includes .env or secrets. Simulation only; no real order is ever sent."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from bist_signal_bot.forward import NO_ORDER
from bist_signal_bot.forward.config import ForwardConfig

TOOL = "bist_forward_backup"
MANIFEST = "MANIFEST.json"
NAME_RE = re.compile(r"^forward_backup_\d{8}_\d{6}(?:_\d+)?\.zip$")
_SECRET_RE = re.compile(r"(secret|token|password|credential|api[_-]?key|private[_-]?key)", re.I)
CONFIG_FILES = (".env.example", "pyproject.toml", "requirements.txt", "bist_signal_bot/config/defaults.py")


def _excluded(name: str) -> bool:
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    if base.startswith(".env") and base != ".env.example":
        return True
    if base == ".run.lock" or base.endswith((".tmp", ".lock", ".part")):
        return True
    return bool(_SECRET_RE.search(base))


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _project_root() -> Path:
    from bist_signal_bot.storage.paths import PROJECT_ROOT
    return Path(PROJECT_ROOT)


def default_dest(cfg: ForwardConfig) -> Path:
    return cfg.data_dir / "backups" / "forward"


def _snapshot_sqlite(src: Path, dst: Path) -> None:
    s = sqlite3.connect(f"file:{src.as_posix()}?mode=ro", uri=True)
    d = sqlite3.connect(str(dst))
    try:
        s.backup(d)  # consistent snapshot
    finally:
        d.close()
        s.close()


def create_backup(cfg: ForwardConfig, dest: Optional[Path] = None, keep: Optional[int] = None,
                  root: Optional[Path] = None, now: Optional[datetime] = None) -> dict:
    dest = Path(dest) if dest else default_dest(cfg)
    dest.mkdir(parents=True, exist_ok=True)
    dest_res = dest.resolve()
    keep = cfg.i("FORWARD_BACKUP_KEEP", 14) if keep is None else int(keep)
    root = Path(root) if root else _project_root()
    now = now or datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    zpath = dest / f"forward_backup_{stamp}.zip"
    i = 1
    while zpath.exists():
        zpath = dest / f"forward_backup_{stamp}_{i}.zip"
        i += 1
    entries: list = []  # (arcname, filepath)
    skipped: list = []
    with tempfile.TemporaryDirectory() as td:
        if cfg.forward_dir.exists():
            for f in sorted(cfg.forward_dir.rglob("*")):
                if not f.is_file() or dest_res in f.resolve().parents:
                    continue
                rel = f.relative_to(cfg.forward_dir).as_posix()
                if _excluded(rel):
                    skipped.append(rel)
                    continue
                entries.append((f"forward/{rel}", f))
        ledger = cfg.resolve_ledger_path()
        if Path(ledger).exists():
            snap = Path(td) / "trials.sqlite"
            _snapshot_sqlite(Path(ledger), snap)
            entries.append(("edge_validation/trials.sqlite", snap))
        else:
            skipped.append("trials.sqlite(missing)")
        for c in CONFIG_FILES:
            p = root / c
            if p.is_file() and not _excluded(c):
                entries.append((f"config/{c}", p))
        files = {arc: _sha(p) for arc, p in entries}
        manifest = {"tool": TOOL, "created_at": now.isoformat(timespec="seconds"), "files": files,
                    "disclaimer": NO_ORDER}
        tmpz = zpath.with_suffix(".zip.part")
        with zipfile.ZipFile(tmpz, "w", zipfile.ZIP_DEFLATED) as z:
            for arc, p in entries:
                z.write(p, arc)
            z.writestr(MANIFEST, json.dumps(manifest, indent=2, sort_keys=True))
        tmpz.replace(zpath)
    pruned = prune_backups(dest, keep)
    return {"path": str(zpath), "n_files": len(files), "skipped": skipped, "pruned": pruned, "disclaimer": NO_ORDER}


def _is_our_backup(p: Path) -> bool:
    if not (p.is_file() and NAME_RE.match(p.name)):
        return False
    try:
        with zipfile.ZipFile(p) as z:
            return json.loads(z.read(MANIFEST)).get("tool") == TOOL
    except Exception:  # noqa: BLE001
        return False


def prune_backups(dest: Path, keep: int) -> list:
    """Delete only OLDER zips created by this tool (name pattern + manifest marker); keep the newest ``keep``."""
    keep = max(int(keep), 1)
    ours = sorted((p for p in Path(dest).iterdir() if _is_our_backup(p)), key=lambda p: p.name)
    removed = []
    for p in ours[:-keep]:
        p.unlink()
        removed.append(p.name)
    return removed


def verify_backup(zip_path: Path) -> dict:
    """Recompute every sha256 against the manifest; extra/missing/mismatching members => FAIL."""
    reasons: list = []
    try:
        with zipfile.ZipFile(zip_path) as z:
            bad = z.testzip()
            if bad:
                reasons.append(f"corrupt_member:{bad}")
            manifest = json.loads(z.read(MANIFEST))
            if manifest.get("tool") != TOOL:
                reasons.append("not_a_forward_backup")
            files = manifest.get("files") or {}
            names = {n for n in z.namelist() if n != MANIFEST}
            for n in sorted(names - set(files)):
                reasons.append(f"unlisted_member:{n}")
            for n, h in sorted(files.items()):
                if n not in names:
                    reasons.append(f"missing_member:{n}")
                elif hashlib.sha256(z.read(n)).hexdigest() != h:
                    reasons.append(f"hash_mismatch:{n}")
            n_files = len(files)
    except Exception as e:  # noqa: BLE001
        return {"status": "FAIL", "reasons": [f"unreadable:{type(e).__name__}:{e}"], "n_files": 0}
    return {"status": "PASS" if not reasons else "FAIL", "reasons": reasons, "n_files": n_files}


def restore_backup(zip_path: Path, target: Path) -> dict:
    """Verify, then extract into an EMPTY/new directory (never overwrites live data)."""
    res = verify_backup(zip_path)
    if res["status"] != "PASS":
        return res
    target = Path(target)
    if target.exists() and any(target.iterdir()):
        return {"status": "FAIL", "reasons": ["target_not_empty"], "n_files": 0}
    target.mkdir(parents=True, exist_ok=True)
    base = target.resolve()
    with zipfile.ZipFile(zip_path) as z:
        for n in z.namelist():
            if n == MANIFEST:
                continue
            out = (base / n).resolve()
            if base not in out.parents:
                return {"status": "FAIL", "reasons": [f"unsafe_path:{n}"], "n_files": 0}
            out.parent.mkdir(parents=True, exist_ok=True)
            with z.open(n) as src, open(out, "wb") as dst:
                shutil.copyfileobj(src, dst)
    return res
