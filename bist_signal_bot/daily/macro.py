"""Macro series loader (Turkey monthly CPI). Research only; no real order sent.

Source order (never guesses a CPI):
 1. local CSV ``<DATA_DIR>/macro/cpi_tr.csv`` with columns ``date,index`` (month start or month end dates; the
    user can drop an official TUIK/ENAG series here; it always wins),
 2. optional free open-data download (no API key, CSV endpoint only, no HTML scraping):
    FRED ``https://fred.stlouisfed.org/graph/fredgraph.csv?id=TURCPIALLMINMEI`` (OECD MEI, CPI all items,
    2015=100, monthly). Verified 2026-10: the series exists but ENDS 2025-04 (OECD stopped updating), so recent
    months are NOT covered; callers must truncate to coverage (see ``edge_validation/real_returns.py``).
    Downloads are cached in ``cpi_tr_fred.csv`` next to the user file (never overwriting ``cpi_tr.csv``).
If nothing is usable ``CPIUnavailable`` is raised (fail loudly).
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Callable, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

FRED_CPI_ID = "TURCPIALLMINMEI"
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={id}"
USER_FILE = "cpi_tr.csv"
CACHE_FILE = "cpi_tr_fred.csv"
MIN_OBS = 24


class CPIUnavailable(RuntimeError):
    """No usable CPI series (never replaced by an assumed inflation rate)."""


def macro_dir(settings=None) -> Path:
    from bist_signal_bot.storage.paths import get_data_dir
    return get_data_dir(settings) / "macro"


def _clean(df: pd.DataFrame, date_col: str, val_col: str, source: str) -> pd.Series:
    d = pd.to_datetime(df[date_col], errors="coerce")
    v = pd.to_numeric(df[val_col], errors="coerce")  # FRED uses '.' for missing
    s = pd.Series(v.to_numpy(float), index=d).dropna()
    s = s[s.index.notna()]
    if len(s) < MIN_OBS:
        raise CPIUnavailable(f"{source}: only {len(s)} valid observations (< {MIN_OBS})")
    if (s <= 0).any():
        raise CPIUnavailable(f"{source}: non-positive CPI values")
    s.index = s.index.to_period("M").to_timestamp()  # month start anchor
    s = s[~s.index.duplicated(keep="last")].sort_index()
    s.name = "cpi"
    return s


def read_cpi_csv(path: Path) -> pd.Series:
    """Parse a CSV with columns date,index (case-insensitive; FRED 'observation_date,<ID>' also accepted)."""
    df = pd.read_csv(path)
    cols = {c.lower().strip(): c for c in df.columns}
    if "date" in cols and "index" in cols:
        return _clean(df, cols["date"], cols["index"], str(path))
    if "observation_date" in cols and len(df.columns) >= 2:
        other = [c for c in df.columns if c != cols["observation_date"]][0]
        return _clean(df, cols["observation_date"], other, str(path))
    raise CPIUnavailable(f"{path}: expected columns 'date,index'")


def fetch_fred_cpi(series_id: str = FRED_CPI_ID, timeout: float = 30.0,
                   http_get: Optional[Callable[[str, float], str]] = None) -> pd.Series:
    """Download a FRED CSV series (free, keyless). Raises CPIUnavailable on any failure."""
    url = FRED_URL.format(id=series_id)
    try:
        if http_get is None:
            import requests
            resp = requests.get(url, timeout=timeout, headers={"User-Agent": "bist-signal-bot-research/1.0"})
            resp.raise_for_status()
            text = resp.text
        else:
            text = http_get(url, timeout)
        if not text.lstrip().lower().startswith("observation_date"):
            raise ValueError("response is not a FRED CSV (blocked or HTML)")
        df = pd.read_csv(io.StringIO(text))
        return _clean(df, df.columns[0], df.columns[1], f"FRED:{series_id}")
    except CPIUnavailable:
        raise
    except Exception as exc:
        logger.warning("FRED CPI fetch failed (%s): %s", url, exc)
        raise CPIUnavailable(f"FRED fetch failed: {exc}") from exc


def load_cpi(settings=None, allow_fetch: bool = True, directory: Optional[Path] = None,
             http_get: Optional[Callable[[str, float], str]] = None) -> Tuple[pd.Series, str]:
    """Return (monthly CPI index indexed by month start, source label). Raises CPIUnavailable if none."""
    d = Path(directory) if directory is not None else macro_dir(settings)
    user = d / USER_FILE
    errors = []
    if user.exists():
        try:
            return read_cpi_csv(user), f"local:{user}"
        except Exception as exc:
            errors.append(f"{user}: {exc}")
            logger.error("Unusable local CPI file %s: %s", user, exc)
    cache = d / CACHE_FILE
    if allow_fetch:
        try:
            s = fetch_fred_cpi(http_get=http_get)
            try:
                d.mkdir(parents=True, exist_ok=True)
                s.rename("index").rename_axis("date").to_csv(cache)
            except OSError as exc:  # cache is best effort
                logger.warning("could not cache CPI to %s: %s", cache, exc)
            return s, f"fred:{FRED_CPI_ID}"
        except CPIUnavailable as exc:
            errors.append(str(exc))
    if cache.exists():
        try:
            return read_cpi_csv(cache), f"cache:{cache}"
        except Exception as exc:
            errors.append(f"{cache}: {exc}")
    raise CPIUnavailable("no CPI series available (refusing to assume one). Tried: "
                         + ("; ".join(errors) or "nothing (fetch disabled, no local file)")
                         + f". Drop a CSV with columns date,index at {user}.")
