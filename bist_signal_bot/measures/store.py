"""CSV store for parsed measures: data/measures/measures.csv, idempotent upsert, coverage summary, date lookup."""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Optional, Sequence

import pandas as pd

from bist_signal_bot.measures.parser import Measure

SOURCE = "KAP/Borsa Istanbul A.S. duyurulari"
COLUMNS = ["symbol", "type", "start", "end", "announcement_id", "publish_date", "source", "fetched_at"]
KEY = ["symbol", "type", "start", "end", "announcement_id"]


def measures_dir(settings=None, directory=None) -> Path:
    if directory is not None:
        return Path(directory)
    from bist_signal_bot.storage.paths import get_data_dir
    return get_data_dir(settings) / "measures"


class MeasureStore:
    def __init__(self, directory=None, settings=None):
        self.dir = measures_dir(settings, directory)
        self.path = self.dir / "measures.csv"

    def exists(self) -> bool:
        return self.path.exists()

    def load(self) -> pd.DataFrame:
        if not self.path.exists():
            return pd.DataFrame(columns=COLUMNS)
        df = pd.read_csv(self.path, dtype=str, keep_default_na=False)
        for c in COLUMNS:
            if c not in df.columns:
                df[c] = ""
        return df[COLUMNS]

    def upsert(self, measures: Iterable[Measure], fetched_at: Optional[str] = None) -> int:
        """Idempotent on (symbol,type,start,end,announcement_id). Returns the number of NEW rows."""
        fa = fetched_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
        rows = [{"symbol": m.symbol, "type": m.type, "start": m.start.isoformat(), "end": m.end.isoformat(),
                 "announcement_id": str(m.announcement_id),
                 "publish_date": m.publish_date.isoformat() if m.publish_date else "",
                 "source": SOURCE, "fetched_at": fa} for m in measures]
        if not rows:
            return 0
        old = self.load()
        merged = pd.concat([old, pd.DataFrame(rows, columns=COLUMNS)], ignore_index=True)
        merged = merged.drop_duplicates(KEY, keep="first")
        merged = merged.sort_values(["symbol", "start", "type", "announcement_id"]).reset_index(drop=True)
        self.dir.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".csv.tmp")
        merged.to_csv(tmp, index=False)
        tmp.replace(self.path)
        return len(merged) - len(old)

    def coverage(self) -> dict:
        df = self.load()
        pub = pd.to_datetime(df["publish_date"], errors="coerce").dropna()
        return {"rows": int(len(df)), "symbols": int(df["symbol"].nunique()) if len(df) else 0,
                "announcements": int(df["announcement_id"].nunique()) if len(df) else 0,
                "oldest_publish": pub.min().date().isoformat() if len(pub) else None,
                "newest_publish": pub.max().date().isoformat() if len(pub) else None}

    def coverage_start(self) -> Optional[date]:
        c = self.coverage()["oldest_publish"]
        return date.fromisoformat(c) if c else None

    def _typed(self, kinds: Optional[Sequence[str]]) -> pd.DataFrame:
        df = self.load()
        if kinds:
            df = df[df["type"].isin(list(kinds))]
        df = df.assign(start=pd.to_datetime(df["start"], errors="coerce"), end=pd.to_datetime(df["end"], errors="coerce"))
        return df.dropna(subset=["start", "end"])

    def is_restricted(self, symbol: str, day, kinds: Optional[Sequence[str]] = None) -> bool:
        d = pd.Timestamp(day).normalize()
        df = self._typed(kinds)
        df = df[df["symbol"] == symbol.upper()]
        return bool(((df["start"] <= d) & (df["end"] >= d)).any())

    def restricted_mask(self, symbols: Sequence[str], dates, kinds: Optional[Sequence[str]] = None) -> pd.DataFrame:
        """Boolean DataFrame (dates x symbols), True = a measure of ``kinds`` (default all) is active that day."""
        idx = pd.DatetimeIndex(dates)
        out = pd.DataFrame(False, index=idx, columns=list(symbols))
        df = self._typed(kinds)
        if df.empty:
            return out
        dn = idx.normalize().to_numpy()
        for r in df[df["symbol"].isin(list(symbols))].itertuples():
            out[r.symbol] = out[r.symbol].to_numpy(bool) | ((dn >= r.start.to_datetime64()) & (dn <= r.end.to_datetime64()))
        return out
