"""FRED (St. Louis Fed) client: rate-limited, retrying, disk-cached. Research only; no orders.

The API key is read from ``get_settings().FRED_API_KEY`` and is NEVER logged, cached or
included in exceptions (masked via :func:`mask_secrets`).

Publication-lag note: FRED observations are dated by the observation day (US calendar) but are
published later (VIXCLS/DGS10/BAMLH0A0HYM2 typically next US business day; DTWEXBGS weekly-ish
with ~1 week lag). Consumers must therefore align to BIST days with ffill + shift(1).
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from bist_signal_bot.config.settings import get_settings
from bist_signal_bot.core.logging_setup import get_logger

logger = get_logger(__name__)

BASE_URL = "https://api.stlouisfed.org/fred"
OBS_URL = f"{BASE_URL}/series/observations"
SERIES_URL = f"{BASE_URL}/series"
DEFAULT_SERIES = ("VIXCLS", "DGS10", "DTWEXBGS", "BAMLH0A0HYM2")
LAG_NOTE = ("FRED values are dated by observation day and published with a lag (>= next US business day; "
            "DTWEXBGS ~1 week). Align with ffill + shift(1) before use.")
NO_ORDER = "No real order sent."

_KEY_RE = re.compile(r"(api_key=)[^&\s'\"]+", re.IGNORECASE)


class FredError(RuntimeError):
    pass


def mask_secrets(text: Any, key: str | None = None) -> str:
    s = _KEY_RE.sub(r"\1***", str(text))
    if key:
        s = s.replace(key, "***")
    return s


class FredClient:
    def __init__(self, settings=None, session=None, cache_dir: Path | None = None,
                 min_interval: float = 0.6, retries: int = 3, backoff: float = 1.5,
                 timeout: float = 20.0, sleeper: Callable[[float], None] = time.sleep,
                 clock: Callable[[], float] = time.monotonic):
        self.settings = settings or get_settings()
        self._key = str(getattr(self.settings, "FRED_API_KEY", "") or "")
        if session is None:
            import requests
            session = requests.Session()
        self.session = session
        base = Path(getattr(self.settings, "DATA_DIR", "data"))
        self.cache_dir = Path(cache_dir) if cache_dir else base / "macro" / "fred_cache"
        self.min_interval, self.retries, self.backoff, self.timeout = min_interval, retries, backoff, timeout
        self._sleep, self._clock = sleeper, clock
        self._last = None

    def __repr__(self) -> str:  # never expose the key
        return f"FredClient(cache_dir={self.cache_dir}, key_set={bool(self._key)})"

    # -- http ---------------------------------------------------------------
    def _get(self, url: str, params: dict) -> dict:
        if not self._key:
            raise FredError("FRED_API_KEY is not configured")
        q = dict(params, api_key=self._key, file_type="json")
        last_err = "unknown"
        for attempt in range(self.retries + 1):
            if self._last is not None:
                wait = self.min_interval - (self._clock() - self._last)
                if wait > 0:
                    self._sleep(wait)
            self._last = self._clock()
            try:
                r = self.session.get(url, params=q, timeout=self.timeout)
                code = getattr(r, "status_code", 200)
                if code == 200:
                    return r.json()
                last_err = f"HTTP {code}"
                if code not in (429, 500, 502, 503, 504):
                    raise FredError(mask_secrets(f"FRED request failed: {last_err} {url}", self._key))
            except FredError:
                raise
            except Exception as e:  # network errors: message may embed the URL with the key
                last_err = type(e).__name__ + ": " + mask_secrets(e, self._key)
            if attempt < self.retries:
                self._sleep(self.backoff ** (attempt + 1))
        raise FredError(mask_secrets(f"FRED request failed after retries: {last_err}", self._key))

    # -- cache --------------------------------------------------------------
    def _cache_path(self, series_id: str) -> Path:
        return self.cache_dir / f"{re.sub(r'[^A-Za-z0-9_]', '_', series_id)}.json"

    def read_cache(self, series_id: str) -> tuple[pd.Series, dict] | None:
        p = self._cache_path(series_id)
        if not p.exists():
            return None
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
            return _to_series(doc["observations"], series_id), doc["meta"]
        except Exception as e:
            logger.warning("FRED cache unreadable for %s: %s", series_id, e)
            return None

    def _write_cache(self, series_id: str, observations: list[dict]) -> dict:
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        meta = {"source": "FRED (api.stlouisfed.org)", "series_id": series_id,
                "fetched_at": datetime.now(timezone.utc).isoformat(), "lag_note": LAG_NOTE}
        doc = {"meta": meta, "observations": [{"date": o["date"], "value": o["value"]} for o in observations]}
        self._cache_path(series_id).write_text(json.dumps(doc), encoding="utf-8")
        return meta

    # -- public -------------------------------------------------------------
    def fetch_series(self, series_id: str, start: str | None = None, end: str | None = None,
                     max_age_hours: float | None = 12.0, force: bool = False) -> pd.Series:
        """Observations as float Series indexed by date; '.' -> NaN. Uses fresh cache if allowed."""
        if not force and max_age_hours:
            c = self.read_cache(series_id)
            if c is not None:
                try:
                    age = datetime.now(timezone.utc) - datetime.fromisoformat(c[1]["fetched_at"])
                    if age.total_seconds() <= max_age_hours * 3600:
                        return _slice(c[0], start, end)
                except Exception:
                    pass
        params = {"series_id": series_id}
        if start:
            params["observation_start"] = start
        if end:
            params["observation_end"] = end
        data = self._get(OBS_URL, params)
        obs = data.get("observations")
        if obs is None:
            raise FredError(mask_secrets(f"FRED response without observations for {series_id}", self._key))
        if not start and not end:
            self._write_cache(series_id, obs)
        return _to_series(obs, series_id)

    def series_info(self, series_id: str) -> dict:
        data = self._get(SERIES_URL, {"series_id": series_id})
        s = (data.get("seriess") or [None])[0]
        if not s:
            raise FredError(f"Unknown FRED series {series_id}")
        return {"id": s.get("id"), "title": s.get("title"), "frequency": s.get("frequency"),
                "observation_end": s.get("observation_end"), "last_updated": s.get("last_updated")}

    def sync(self, series_ids=DEFAULT_SERIES, start: str | None = None) -> dict[str, dict]:
        out = {}
        for sid in series_ids:
            try:
                s = self.fetch_series(sid, start=start, force=True)
                out[sid] = {"rows": int(len(s)),
                            "last": str(s.dropna().index[-1].date()) if s.notna().any() else None}
            except FredError as e:
                out[sid] = {"error": str(e)}
        return out


def _to_series(obs: list[dict], name: str) -> pd.Series:
    idx = pd.to_datetime([o["date"] for o in obs])
    vals = [np.nan if o["value"] in (".", "", None) else float(o["value"]) for o in obs]
    return pd.Series(vals, index=idx, name=name, dtype=float).sort_index()


def _slice(s: pd.Series, start, end) -> pd.Series:
    if start:
        s = s[s.index >= pd.Timestamp(start)]
    if end:
        s = s[s.index <= pd.Timestamp(end)]
    return s


def load_cached_series(settings=None, series_ids=DEFAULT_SERIES) -> dict[str, pd.Series]:
    """Read-only (no network) load of cached series."""
    c = FredClient(settings=settings, session=object())
    out = {}
    for sid in series_ids:
        r = c.read_cache(sid)
        if r is not None:
            out[sid] = r[0]
    return out
