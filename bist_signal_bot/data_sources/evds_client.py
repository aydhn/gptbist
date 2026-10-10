"""TCMB EVDS3 client (CPI, TLREF/AOFM cash rate). Research only; no real order sent.

* Base ``https://evds3.tcmb.gov.tr/igmevdsms-dis/``; the API key travels in the ``key`` HTTP header (never in the
  URL). The old evds2 host answers with HTML -> counted as an error. The key is masked in every message/log.
* Rate limit >= 1 s between requests, 3 attempts with exponential backoff, on-disk cache
  ``<DATA_DIR>/macro/evds_cache/`` (each file labelled with source and fetch date).
* Nothing is assumed: missing key / HTML / empty answers raise ``EVDSError``; search helpers return None.
"""
from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

EVDS_BASE = "https://evds3.tcmb.gov.tr/igmevdsms-dis/"
SOURCE_LABEL = "TCMB-EVDS3"
CPI_NEW = "TP.TUKFIY2025.GENEL"   # 2025=100
CPI_OLD = "TP.FG.J0"              # 2003=100, ends 2026-1
TLREF = "TP.BISTTLREF.ORAN"
AOFM = "TP.APIFON4"
CPI_FILE = "cpi_tr.csv"
CASH_FILE = "tlref.csv"
MIN_INTERVAL_S = 1.0
ATTEMPTS = 3
CHUNK_YEARS = 2
TRUNCATION_ROWS = 1000
NO_ORDER = "No real order sent."

HttpGet = Callable[[str, Dict[str, str], float], Tuple[int, str]]
_last_call = [float("-inf")]


class EVDSError(RuntimeError):
    """EVDS request/parse failure (message is always key-masked)."""


def mask(text: Any, key: Optional[str] = None) -> str:
    s = str(text)
    if key:
        s = s.replace(key, "***")
    return re.sub(r"(?i)(key[=:]\s*)[A-Za-z0-9]{6,}", r"\1***", s)


def get_api_key(settings=None) -> str:
    if settings is None:
        from bist_signal_bot.config.settings import get_settings
        settings = get_settings()
    try:
        k = getattr(settings, "EVDS_API_KEY", None)
    except Exception:
        k = None
    k = str(k).strip() if k is not None else ""
    if not k or k.lower().startswith(("your", "changeme", "xxx")) or "placeholder" in k.lower():
        raise EVDSError("EVDS_API_KEY is not set (put it in .env; value is never printed)")
    return k


def macro_dir(settings=None, directory: Optional[Path] = None) -> Path:
    if directory is not None:
        return Path(directory)
    from bist_signal_bot.daily.macro import macro_dir as _md
    return _md(settings)


def _default_http_get(url: str, headers: Dict[str, str], timeout: float) -> Tuple[int, str]:
    import requests
    r = requests.get(url, headers=headers, timeout=timeout)
    return r.status_code, r.text


def _fmt_date(d) -> str:
    if isinstance(d, str) and re.fullmatch(r"\d{2}-\d{2}-\d{4}", d):
        return d
    return pd.Timestamp(d).strftime("%d-%m-%Y")


def _to_ts(d):
    if isinstance(d, str) and re.fullmatch(r"\d{2}-\d{2}-\d{4}", d):
        return pd.to_datetime(d, format="%d-%m-%Y")
    return pd.Timestamp(d)


class EVDSClient:
    def __init__(self, api_key: Optional[str] = None, *, settings=None, directory: Optional[Path] = None,
                 base_url: str = EVDS_BASE, http_get: Optional[HttpGet] = None, min_interval: float = MIN_INTERVAL_S,
                 attempts: int = ATTEMPTS, backoff: float = 2.0, timeout: float = 30.0,
                 cache_ttl_hours: float = 12.0, sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], float] = time.monotonic):
        self._key = api_key
        self._settings = settings
        self.dir = macro_dir(settings, directory)
        self.cache_dir = self.dir / "evds_cache"
        self.base = base_url if base_url.endswith("/") else base_url + "/"
        self.http_get = http_get or _default_http_get
        self.min_interval, self.attempts, self.backoff = float(min_interval), int(attempts), float(backoff)
        self.timeout, self.cache_ttl = float(timeout), float(cache_ttl_hours)
        self._sleep, self._clock = sleep, clock

    @property
    def key(self) -> str:
        if not self._key:
            self._key = get_api_key(self._settings)
        return self._key

    # ---- transport ----
    def _throttle(self) -> None:
        wait = self.min_interval - (self._clock() - _last_call[0])
        if wait > 0:
            self._sleep(wait)
        _last_call[0] = self._clock()

    def _request_json(self, path_query: str) -> Any:
        url = self.base + path_query
        key = self.key
        last = "unknown"
        for i in range(self.attempts):
            self._throttle()
            try:
                status, text = self.http_get(url, {"key": key}, self.timeout)
                if status != 200:
                    last = f"HTTP {status}"
                elif not text.strip() or text.lstrip()[:1] == "<":
                    last = "non-JSON answer (HTML/empty; wrong host or key rejected)"
                else:
                    return json.loads(text)
            except Exception as exc:  # network / JSON errors
                last = mask(f"{type(exc).__name__}: {exc}", key)
            logger.warning("EVDS request failed (attempt %d/%d): %s", i + 1, self.attempts, mask(last, key))
            if i < self.attempts - 1:
                self._sleep(self.backoff ** i)
        raise EVDSError(mask(f"EVDS request failed after {self.attempts} attempts: {last} ({path_query})", key))

    # ---- cache ----
    def _cache_path(self, code: str, start: str, end: str) -> Path:
        safe = re.sub(r"[^A-Za-z0-9]+", "_", code)
        return self.cache_dir / f"{safe}__{start}__{end}.json"

    @staticmethod
    def _read_cache(p: Path) -> Optional[dict]:
        try:
            return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
        except Exception:
            return None

    # ---- API ----
    def fetch_series(self, code: str, start, end, *, use_cache: bool = True,
                     chunk_years: int = CHUNK_YEARS) -> pd.Series:
        """Observations of one EVDS series as a float Series (DatetimeIndex; monthly -> month start).

        EVDS may truncate long answers (~1000 rows), so the range is fetched in ``chunk_years`` pieces, merged and
        de-duplicated. A chunk with >= 1000 rows logs a warning (possible truncation)."""
        t0, t1 = pd.Timestamp(_to_ts(start)), pd.Timestamp(_to_ts(end))
        if t1 < t0:
            raise EVDSError(f"EVDS range end before start for {code}")
        parts: List[pd.Series] = []
        lo = t0
        while lo <= t1:
            hi = min(lo + pd.DateOffset(years=chunk_years) - pd.Timedelta(days=1), t1)
            try:
                part = self._fetch_chunk(code, lo.strftime("%d-%m-%Y"), hi.strftime("%d-%m-%Y"), use_cache=use_cache)
            except EVDSError as exc:
                if "no observations" not in str(exc) and "no numeric" not in str(exc):
                    raise
                part = None  # empty window (e.g. before the series starts)
            if part is not None:
                if len(part) >= TRUNCATION_ROWS:
                    logger.warning("EVDS chunk %s %s..%s has %d rows (>= %d): answer may be truncated",
                                   code, lo.date(), hi.date(), len(part), TRUNCATION_ROWS)
                parts.append(part)
            lo = hi + pd.Timedelta(days=1)
        if not parts:
            raise EVDSError(f"EVDS returned no observations for {code}")
        out = pd.concat(parts).sort_index()
        out = out[~out.index.duplicated(keep="last")]
        out.name = code
        return out

    def _fetch_chunk(self, code: str, start, end, *, use_cache: bool = True) -> pd.Series:
        s_, e_ = _fmt_date(start), _fmt_date(end)
        p = self._cache_path(code, s_, e_)
        cached = self._read_cache(p) if use_cache else None
        if cached:
            age_h = (datetime.now(timezone.utc) - datetime.fromisoformat(cached["fetched_at"])).total_seconds() / 3600
            if age_h <= self.cache_ttl:
                return _parse_items(cached["items"], code)
        try:
            data = self._request_json(f"series={code}&startDate={s_}&endDate={e_}&type=json")
            items = data.get("items") if isinstance(data, dict) else None
            if not items:
                raise EVDSError(f"EVDS returned no observations for {code}")
            out = _parse_items(items, code)
        except EVDSError as exc:
            if cached:
                logger.warning("using STALE EVDS cache for %s (%s)", code, exc)
                return _parse_items(cached["items"], code)
            raise
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps({"source": SOURCE_LABEL, "series": code, "start": s_, "end": e_,
                                     "fetched_at": datetime.now(timezone.utc).isoformat(), "items": items},
                                    ensure_ascii=False), encoding="utf-8")
        except OSError as exc:
            logger.warning("could not cache %s: %s", code, exc)
        return out

    def serie_list(self, group: str) -> List[Dict[str, Any]]:
        """Series metadata of a datagroup code (e.g. ``bie_ptbfon``)."""
        return _as_rows(self._request_json(f"serieList/type=json&code={group}"))

    def categories(self) -> List[Dict[str, Any]]:
        return _as_rows(self._request_json("categories/type=json"))

    def find_series(self, group: str, *keywords: str) -> Optional[str]:
        """First series code in ``group`` whose name contains ALL keywords (case-insensitive), else None."""
        kws = [k.lower() for k in keywords]
        for row in self.serie_list(group):
            name = " ".join(str(v) for k, v in row.items() if "NAME" in str(k).upper()).lower()
            if name and all(k in name for k in kws):
                code = row.get("SERIE_CODE") or row.get("serie_code")
                if code:
                    return str(code)
        return None

    def find_policy_rate_series(self, group: str = "bie_ptbfon") -> Optional[str]:
        """Helper: 'TCMB bir hafta vadeli repo' policy-rate series in a datagroup, or None (never guessed)."""
        for kw in (("bir hafta", "repo"), ("1 hafta", "repo"), ("one week", "repo"), ("politika",)):
            c = self.find_series(group, *kw)
            if c:
                return c
        return None

    # ---- builders ----
    def build_cpi(self, start="01-01-2003", end=None, write: bool = True) -> pd.Series:
        end = end or datetime.now().strftime("%d-%m-%Y")
        new = self.fetch_series(CPI_NEW, "01-01-2025", end)
        old = self.fetch_series(CPI_OLD, start, end)
        s = splice_cpi(old, new)
        if write:
            self.dir.mkdir(parents=True, exist_ok=True)
            s.rename("index").rename_axis("date").to_csv(self.dir / CPI_FILE)
        return s

    def build_cash_rate(self, start="01-01-2010", end=None, write: bool = True) -> pd.Series:
        end = end or datetime.now().strftime("%d-%m-%Y")
        tl = self.fetch_series(TLREF, start, end)
        try:
            ao = self.fetch_series(AOFM, start, end)
        except EVDSError as exc:
            logger.warning("AOFM series unavailable (%s); TLREF only", exc)
            ao = None
        s = combine_cash_rate(tl, ao)
        if write:
            self.dir.mkdir(parents=True, exist_ok=True)
            s.rename("rate_annual").rename_axis("date").to_csv(self.dir / CASH_FILE)
        return s


def _as_rows(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("items") or []
    return []


def _parse_date(v: str) -> pd.Timestamp:
    v = str(v).strip()
    m = re.fullmatch(r"(\d{4})-(\d{1,2})", v)            # monthly "2025-1"
    if m:
        return pd.Timestamp(int(m.group(1)), int(m.group(2)), 1)
    m = re.fullmatch(r"(\d{1,2})-(\d{1,2})-(\d{4})", v)  # "dd-mm-yyyy"
    if m:
        return pd.Timestamp(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    return pd.Timestamp(v)


def _parse_items(items: List[dict], code: str) -> pd.Series:
    col = code.replace(".", "_")
    dates, vals = [], []
    for it in items:
        raw = it.get(col)
        if raw is None:  # tolerate other column spellings
            others = [k for k in it if k not in ("Tarih", "UNIXTIME")]
            raw = it.get(others[0]) if len(others) == 1 else None
        try:
            v = float(raw)
        except (TypeError, ValueError):
            continue
        dates.append(_parse_date(it["Tarih"]))
        vals.append(v)
    if not vals:
        raise EVDSError(f"no numeric observations parsed for {code}")
    s = pd.Series(vals, index=pd.DatetimeIndex(dates), name=code).sort_index()
    return s[~s.index.duplicated(keep="last")]


def splice_cpi(old: pd.Series, new: pd.Series) -> pd.Series:
    """One continuous index on the NEW base (2025=100): old * mean(new/old over the overlap) before the new start.
    Dates are month starts (compatible with daily.macro.read_cpi_csv)."""
    old = old.copy()
    new = new.copy()
    old.index = old.index.to_period("M").to_timestamp()
    new.index = new.index.to_period("M").to_timestamp()
    ov = old.index.intersection(new.index)
    if len(ov) == 0:
        raise EVDSError("old and new CPI series have no overlapping months; cannot splice")
    ratio = float((new.loc[ov] / old.loc[ov]).mean())
    pre = old[old.index < new.index[0]] * ratio
    out = pd.concat([pre, new]).sort_index()
    out = out[~out.index.duplicated(keep="last")]
    if (out <= 0).any():
        raise EVDSError("non-positive CPI after splice")
    out.name = "index"
    return out


def combine_cash_rate(tlref_pct: pd.Series, aofm_pct: Optional[pd.Series] = None) -> pd.Series:
    """Daily annual rate as a FRACTION: TLREF where available, AOFM before TLREF starts (percent -> fraction)."""
    tl = tlref_pct.astype(float) / 100.0
    if aofm_pct is not None and len(aofm_pct):
        ao = aofm_pct.astype(float) / 100.0
        tl = pd.concat([ao[ao.index < tl.index[0]], tl]).sort_index()
    tl = tl[~tl.index.duplicated(keep="last")]
    tl.name = "rate_annual"
    return tl


def load_cash_rate_series(settings=None, directory: Optional[Path] = None) -> Optional[pd.Series]:
    """Time-varying annual cash rate (fraction) from ``macro/tlref.csv``; None if absent/unusable."""
    p = macro_dir(settings, directory) / CASH_FILE
    if not p.exists():
        return None
    try:
        df = pd.read_csv(p)
        s = pd.Series(pd.to_numeric(df["rate_annual"], errors="coerce").to_numpy(float),
                      index=pd.to_datetime(df["date"], errors="coerce")).dropna()
        s = s[s.index.notna()].sort_index()
        s = s[~s.index.duplicated(keep="last")]
        return s if len(s) else None
    except Exception as exc:
        logger.error("unusable cash rate file %s: %s", p, exc)
        return None
