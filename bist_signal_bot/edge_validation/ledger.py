"""Append-only SQLite ledger of EVERY evaluated strategy/parameter trial (incl. failures).

N for DSR/PBO must count all attempts. Rows can't be updated or deleted (triggers).
record_trial is idempotent on trial_id.
"""
from __future__ import annotations

import io
import json
import sqlite3
import time
import zlib
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from bist_signal_bot.core.logging_setup import get_logger

logger = get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS trials(
 trial_id TEXT PRIMARY KEY, strategy TEXT NOT NULL, strategy_family TEXT NOT NULL,
 params_json TEXT, interval TEXT, universe TEXT, created_at INTEGER NOT NULL,
 n_obs INTEGER, sharpe REAL, status TEXT DEFAULT 'ok',
 ts_blob BLOB, returns_blob BLOB);
CREATE INDEX IF NOT EXISTS ix_trials_family ON trials(strategy_family);
CREATE TRIGGER IF NOT EXISTS trials_no_delete BEFORE DELETE ON trials
BEGIN SELECT RAISE(ABORT, 'trial ledger is append-only'); END;
CREATE TRIGGER IF NOT EXISTS trials_no_update BEFORE UPDATE ON trials
BEGIN SELECT RAISE(ABORT, 'trial ledger is append-only'); END;
"""


def _pack(a: np.ndarray) -> bytes:
    buf = io.BytesIO()
    np.save(buf, a, allow_pickle=False)
    return zlib.compress(buf.getvalue(), 6)


def _unpack(b: Optional[bytes]) -> np.ndarray:
    if not b:
        return np.array([])
    return np.load(io.BytesIO(zlib.decompress(b)), allow_pickle=False)


def default_ledger_path(settings=None) -> Path:
    from bist_signal_bot.storage.paths import get_edge_validation_dir
    return get_edge_validation_dir(settings) / "trials.sqlite"


class TrialLedger:
    def __init__(self, path: Optional[Path] = None, settings=None):
        self.path = Path(path) if path is not None else default_ledger_path(settings)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        c = self._conn()
        try:
            c.executescript(_SCHEMA)
            c.commit()
        finally:
            c.close()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(str(self.path), timeout=30)

    def _query(self, q: str, args=()):
        c = self._conn()
        try:
            return c.execute(q, args).fetchall()
        finally:
            c.close()

    def record_trial(self, trial_id: str, strategy: str, params: Optional[dict] = None,
                     interval: str = "", universe: str = "", returns: Optional[pd.Series] = None,
                     strategy_family: Optional[str] = None, status: str = "ok") -> bool:
        """Insert a trial; True if new, False if trial_id already existed (nothing changes).

        returns: per-period returns Series indexed by timestamp. Failed trials may pass None
        with status='failed' - they still count toward N.
        """
        n_obs, sr, ts_blob, r_blob = 0, None, None, None
        if returns is not None and len(returns) > 0:
            s = pd.Series(returns).dropna()
            n_obs = int(s.size)
            if n_obs >= 3 and s.std(ddof=1) > 0:
                sr = float(s.mean() / s.std(ddof=1))
            idx = s.index
            if isinstance(idx, pd.DatetimeIndex):
                ts = (idx.tz_convert("UTC") if idx.tz is not None else idx).as_unit("ns").asi8
            else:
                ts = np.asarray(idx, dtype=np.int64)
            ts_blob = _pack(np.asarray(ts, dtype=np.int64))
            r_blob = _pack(s.to_numpy(dtype=float))
        c = self._conn()
        try:
            cur = c.execute(
                "INSERT OR IGNORE INTO trials(trial_id,strategy,strategy_family,params_json,interval,"
                "universe,created_at,n_obs,sharpe,status,ts_blob,returns_blob) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (trial_id, strategy, strategy_family or strategy,
                 json.dumps(params or {}, sort_keys=True, default=str), interval, universe,
                 int(time.time()), n_obs, sr, status, ts_blob, r_blob))
            c.commit()
            return cur.rowcount == 1
        finally:
            c.close()

    def n_trials(self, strategy_family: Optional[str] = None) -> int:
        if strategy_family is None:
            return int(self._query("SELECT COUNT(*) FROM trials")[0][0])
        return int(self._query("SELECT COUNT(*) FROM trials WHERE strategy_family=?",
                               (strategy_family,))[0][0])

    def trial_sharpes(self, strategy_family: Optional[str] = None) -> np.ndarray:
        """Per-period Sharpes of trials where defined."""
        q, a = "SELECT sharpe FROM trials WHERE sharpe IS NOT NULL", ()
        if strategy_family is not None:
            q, a = q + " AND strategy_family=?", (strategy_family,)
        return np.array([r[0] for r in self._query(q, a)], dtype=float)

    def trial_sharpe_variance(self, strategy_family: Optional[str] = None) -> float:
        s = self.trial_sharpes(strategy_family)
        return float(np.var(s, ddof=1)) if s.size >= 2 else float("nan")

    def returns_matrix(self, strategy_family: Optional[str] = None, with_mask: bool = False):
        """Outer-join trial returns on UTC timestamps, NaN->0; columns = trial_id.

        with_mask=True returns (matrix, mask) where mask is True where a value was observed.
        """
        q, a = "SELECT trial_id, ts_blob, returns_blob FROM trials WHERE returns_blob IS NOT NULL", ()
        if strategy_family is not None:
            q, a = q + " AND strategy_family=?", (strategy_family,)
        rows = self._query(q + " ORDER BY created_at, trial_id", a)
        series = {tid: pd.Series(_unpack(rb), index=pd.to_datetime(_unpack(tb), utc=True))
                  for tid, tb, rb in rows}
        if not series:
            return (pd.DataFrame(), pd.DataFrame()) if with_mask else pd.DataFrame()
        raw = pd.concat(series, axis=1).sort_index()
        mask = raw.notna()
        out = raw.fillna(0.0)
        return (out, mask) if with_mask else out
