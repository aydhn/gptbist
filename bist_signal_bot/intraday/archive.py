"""SQLite-backed archive of RAW intraday bars (adjustment is a read-time transform)."""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from bist_signal_bot.core.logging_setup import get_logger
from bist_signal_bot.intraday.models import normalize_interval

logger = get_logger(__name__)

TZ = "Europe/Istanbul"
COLS = ["open", "high", "low", "close", "volume"]

_SCHEMA = """
CREATE TABLE IF NOT EXISTS bars(
 symbol TEXT NOT NULL, interval TEXT NOT NULL, ts_utc INTEGER NOT NULL,
 open REAL, high REAL, low REAL, close REAL, volume REAL,
 source TEXT, fetched_at INTEGER, adjusted INTEGER DEFAULT 0,
 PRIMARY KEY(symbol, interval, ts_utc));
CREATE TABLE IF NOT EXISTS actions(
 symbol TEXT NOT NULL, ex_date TEXT NOT NULL, kind TEXT NOT NULL, value REAL,
 PRIMARY KEY(symbol, ex_date, kind));
CREATE TABLE IF NOT EXISTS universe_snapshots(
 snapshot_date TEXT NOT NULL, symbol TEXT NOT NULL, status TEXT NOT NULL,
 PRIMARY KEY(snapshot_date, symbol));
CREATE TABLE IF NOT EXISTS fetch_log(
 symbol TEXT, interval TEXT, started_at INTEGER, rows INTEGER, ok INTEGER, error TEXT);
"""


@dataclass
class UpsertResult:
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0


class BarArchive:
    def __init__(self, path: Path | str | None = None, settings=None):
        if path is None:
            from bist_signal_bot.storage.paths import get_intraday_archive_path
            path = get_intraday_archive_path(settings)
        self.path = path
        self.settings = settings
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(path))
        try:
            self._conn.execute("PRAGMA journal_mode=WAL")
        except sqlite3.DatabaseError:
            pass
        self._conn.executescript(_SCHEMA)
        self._conn.commit()
        n = getattr(settings, "INTRADAY_UNIVERSE_DELIST_MISSES", None) if settings is not None else None
        try:
            self._delist_misses = int(n) if n else 10
        except (TypeError, ValueError):
            self._delist_misses = 10

    def close(self) -> None:
        self._conn.close()

    # ---- bars ----
    def upsert_bars(self, df: pd.DataFrame, symbol: str, interval: str, source: str,
                    adjusted: bool = False) -> UpsertResult:
        interval = normalize_interval(interval)
        res = UpsertResult()
        if df is None or df.empty:
            return res
        d = df.copy()
        d.columns = [str(c).lower() for c in d.columns]
        if "volume" not in d.columns:
            d["volume"] = 0.0
        d = d[COLS].apply(pd.to_numeric, errors="coerce")
        idx = pd.DatetimeIndex(df.index)
        idx = idx.tz_localize(TZ) if idx.tz is None else idx
        d.index = idx.tz_convert("UTC")
        d = d.dropna()
        oc_max = d[["open", "close"]].max(axis=1)
        oc_min = d[["open", "close"]].min(axis=1)
        d = d[(d["high"] >= d["low"]) & (d["high"] >= oc_max) & (d["low"] <= oc_min)]
        d = d[~d.index.duplicated(keep="last")]
        now = int(time.time())
        cur = self._conn.cursor()
        for ts, r in d.iterrows():
            key = (symbol, interval, int(ts.timestamp()))
            old = cur.execute(
                "SELECT open,high,low,close,volume FROM bars WHERE symbol=? AND interval=? AND ts_utc=?",
                key).fetchone()
            vals = tuple(float(r[c]) for c in COLS)
            if old is not None and all(abs(a - b) <= 1e-12 for a, b in zip(old, vals)):
                res.unchanged += 1
                continue
            cur.execute(
                "INSERT INTO bars(symbol,interval,ts_utc,open,high,low,close,volume,source,fetched_at,adjusted)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(symbol,interval,ts_utc) DO UPDATE SET"
                " open=excluded.open,high=excluded.high,low=excluded.low,close=excluded.close,"
                " volume=excluded.volume,source=excluded.source,fetched_at=excluded.fetched_at,"
                " adjusted=excluded.adjusted",
                key + vals + (source, now, int(adjusted)))
            if old is None:
                res.inserted += 1
            else:
                res.updated += 1
        self._conn.commit()
        return res

    @staticmethod
    def _epoch(x) -> int:
        t = pd.Timestamp(x)
        t = t.tz_localize(TZ) if t.tzinfo is None else t
        return int(t.timestamp())

    def read_bars(self, symbol: str, interval: str, start=None, end=None) -> pd.DataFrame:
        interval = normalize_interval(interval)
        q = "SELECT ts_utc,open,high,low,close,volume FROM bars WHERE symbol=? AND interval=?"
        p: list = [symbol, interval]
        if start is not None:
            q += " AND ts_utc>=?"
            p.append(self._epoch(start))
        if end is not None:
            q += " AND ts_utc<=?"
            p.append(self._epoch(end))
        rows = self._conn.execute(q + " ORDER BY ts_utc", p).fetchall()
        df = pd.DataFrame(rows, columns=["ts"] + COLS)
        idx = pd.to_datetime(df["ts"], unit="s", utc=True).dt.tz_convert(TZ)
        df = df.drop(columns="ts")
        df.index = pd.DatetimeIndex(idx, name="timestamp")
        return df

    def _ts(self, fn: str, symbol: str, interval: str):
        r = self._conn.execute(f"SELECT {fn}(ts_utc) FROM bars WHERE symbol=? AND interval=?",
                               (symbol, normalize_interval(interval))).fetchone()[0]
        return None if r is None else pd.Timestamp(r, unit="s", tz="UTC").tz_convert(TZ)

    def last_ts(self, symbol: str, interval: str):
        return self._ts("MAX", symbol, interval)

    def first_ts(self, symbol: str, interval: str):
        return self._ts("MIN", symbol, interval)

    def count(self, symbol: str | None = None, interval: str | None = None) -> int:
        q, p = "SELECT COUNT(*) FROM bars WHERE 1=1", []
        if symbol:
            q += " AND symbol=?"
            p.append(symbol)
        if interval:
            q += " AND interval=?"
            p.append(normalize_interval(interval))
        return int(self._conn.execute(q, p).fetchone()[0])

    def symbols(self, interval: str) -> list[str]:
        return [r[0] for r in self._conn.execute(
            "SELECT DISTINCT symbol FROM bars WHERE interval=? ORDER BY symbol", (normalize_interval(interval),))]

    # ---- fetch log ----
    def log_fetch(self, symbol: str, interval: str, started_at: float, rows: int, ok: bool,
                  error: str | None = None) -> None:
        self._conn.execute("INSERT INTO fetch_log VALUES(?,?,?,?,?,?)",
                           (symbol, interval, int(started_at), rows, int(ok), error))
        self._conn.commit()

    def fetch_log(self) -> list[tuple]:
        return self._conn.execute("SELECT symbol,interval,started_at,rows,ok,error FROM fetch_log").fetchall()

    # ---- actions ----
    def record_actions(self, symbol: str, actions) -> int:
        """actions: iterable of (ex_date, kind, value). Idempotent."""
        n = 0
        for ex, kind, val in actions:
            if kind not in ("split", "dividend"):
                raise ValueError(f"bad action kind {kind}")
            self._conn.execute(
                "INSERT INTO actions VALUES(?,?,?,?) ON CONFLICT(symbol,ex_date,kind) DO UPDATE SET value=excluded.value",
                (symbol, str(pd.Timestamp(ex).date()), kind, float(val)))
            n += 1
        self._conn.commit()
        return n

    def get_actions(self, symbol: str, kind: str | None = None) -> list[tuple]:
        q, p = "SELECT ex_date,kind,value FROM actions WHERE symbol=?", [symbol]
        if kind:
            q += " AND kind=?"
            p.append(kind)
        return self._conn.execute(q + " ORDER BY ex_date", p).fetchall()

    def adjust_for_splits(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Adjusted copy: bars before each split ex_date get prices/factor, volume*factor."""
        out = df.copy()
        for ex, _k, factor in self.get_actions(symbol, "split"):
            if not factor or factor <= 0:
                continue
            ex_ts = pd.Timestamp(ex)
            if out.index.tz is not None:
                ex_ts = ex_ts.tz_localize(out.index.tz)
            m = out.index < ex_ts
            for c in ("open", "high", "low", "close"):
                if c in out.columns:
                    out.loc[m, c] = out.loc[m, c] / factor
            if "volume" in out.columns:
                out.loc[m, "volume"] = out.loc[m, "volume"] * factor
        return out

    # ---- universe / survivorship ----
    def snapshot_universe(self, snap_date, active_symbols) -> dict:
        d = str(pd.Timestamp(snap_date).date())
        active = set(active_symbols)
        prev = self._conn.execute(
            "SELECT MAX(snapshot_date) FROM universe_snapshots WHERE snapshot_date<?", (d,)).fetchone()[0]
        prev_status = {}
        if prev:
            prev_status = dict(self._conn.execute(
                "SELECT symbol,status FROM universe_snapshots WHERE snapshot_date=?", (prev,)))
        known = set(prev_status)
        for s in active:
            self._conn.execute("INSERT OR REPLACE INTO universe_snapshots VALUES(?,?,?)", (d, s, "active"))
        for s in known - active:
            misses = self._consecutive_misses(s, d) + 1
            st = "delisted" if (misses >= self._delist_misses or prev_status[s] == "delisted") else "missing"
            self._conn.execute("INSERT OR REPLACE INTO universe_snapshots VALUES(?,?,?)", (d, s, st))
        self._conn.commit()
        return {"date": d, "active": len(active), "missing": len(known - active)}

    def _consecutive_misses(self, symbol: str, before: str) -> int:
        rows = self._conn.execute(
            "SELECT status FROM universe_snapshots WHERE symbol=? AND snapshot_date<? ORDER BY snapshot_date DESC",
            (symbol, before)).fetchall()
        n = 0
        for (st,) in rows:
            if st == "active":
                break
            n += 1
        return n

    def survivorship_report(self) -> dict:
        last = self._conn.execute("SELECT MAX(snapshot_date) FROM universe_snapshots").fetchone()[0]
        rep: dict = {"last_snapshot": last, "active": [], "missing": [], "delisted": []}
        if last:
            for s, st in self._conn.execute(
                    "SELECT symbol,status FROM universe_snapshots WHERE snapshot_date=? ORDER BY symbol", (last,)):
                rep[st].append(s)
        rep["snapshots"] = self._conn.execute(
            "SELECT COUNT(DISTINCT snapshot_date) FROM universe_snapshots").fetchone()[0]
        return rep
