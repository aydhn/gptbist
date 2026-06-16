"""Runtime configuration for the BIST Signal Bot.

Configuration is loaded from (in increasing order of precedence):

1. ``.env.example`` — the committed template with safe, research-only defaults
   (the single source of truth for the ~800 available keys).
2. ``.env`` — the operator's local overrides (git-ignored).
3. ``os.environ`` — process environment wins over everything.

Values are coerced to native Python types based on their literal form and key
name, so engines that expect an ``int`` window, a ``bool`` flag, a ``float``
ratio or a ``Path`` directory receive the right type instead of a raw string.

This module is intentionally dependency-free (no ``pydantic-settings`` / no
``python-dotenv``) so configuration loading can never fail to import. The public
surface is fully backwards compatible: ``Settings()``, ``get_settings()`` and the
module-level ``settings`` singleton all behave as before — except they now return
**real values from ``.env`` instead of the string ``"mock_value"``**.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from bist_signal_bot.config.defaults import DEFAULTS

# repo root: bist_signal_bot/config/settings.py -> config -> bist_signal_bot -> <root>
_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _ROOT / ".env"
_ENV_EXAMPLE = _ROOT / ".env.example"

# Name-based hints for typing values that are missing or ambiguous.
_FLAG_PREFIXES = ("ENABLE_", "USE_", "IS_", "HAS_", "ALLOW_", "REQUIRE_")
_FLAG_SUFFIXES = ("_ENABLED", "_DISABLED", "_DRY_RUN")
_INT_SUFFIXES = (
    "_SECONDS", "_MINUTES", "_HOURS", "_DAYS", "_COUNT", "_TOP_N", "_N",
    "_ROWS", "_BYTES", "_RETRIES", "_LIMIT", "_SIZE", "_WINDOW", "_PERIOD",
    "_SAMPLES", "_LAG", "_LAGS", "_DEPTH", "_WORKERS", "_BATCH",
    "_BACKUP_COUNT", "_MAX_BYTES",
)
_FLOAT_SUFFIXES = (
    "_PCT", "_RATIO", "_RATE", "_THRESHOLD", "_ALPHA", "_BETA", "_FACTOR",
    "_MULTIPLIER", "_ANNUALIZATION", "_ABS", "_FRACTION", "_WEIGHT",
    "_TOLERANCE", "_QUANTILE",
)

# Explicit defaults for keys that have a meaningful non-empty fallback when they
# are absent from both .env and .env.example. (Most real keys live in .env.example
# and are read from there; these are a safety net only.)
_EXPLICIT_DEFAULTS: dict[str, Any] = {
    "APP_ENV": "development",
    "RUN_MODE": "research",
    "DRY_RUN": True,
    "DEFAULT_TIMEZONE": "Europe/Istanbul",
    "LOG_LEVEL": "INFO",
    "LOG_MAX_BYTES": 1_000_000,
    "LOG_BACKUP_COUNT": 5,
    "DATA_DIR": Path("data"),
    "CACHE_DIR": Path("data/cache"),
    "REPORTS_DIR": Path("data/reports"),
}


def _unquote(s: str) -> str:
    if len(s) >= 2 and s[0] in ("'", '"') and s[-1] == s[0]:
        return s[1:-1]
    return s


def _parse_env_file(path: Path) -> dict[str, str]:
    """Minimal, robust ``KEY=VALUE`` parser (comments, blank lines, ``export``)."""
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key:
            data[key] = val.strip()
    return data


def _coerce(key: str, raw: str) -> Any:
    """Coerce a raw string value to a native type using value form + key name."""
    if raw is None:
        return None
    s = _unquote(raw.strip())
    if s == "":
        return ""
    low = s.lower()
    up = key.upper()
    is_flag = up.startswith(_FLAG_PREFIXES) or up.endswith(_FLAG_SUFFIXES)

    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("none", "null"):
        return None
    if low in ("1", "0") and is_flag:
        return low == "1"
    if re.fullmatch(r"[+-]?\d+", s):
        try:
            return int(s)
        except ValueError:
            pass
    if re.fullmatch(r"[+-]?(?:\d+\.\d*|\.\d+|\d+(?:\.\d*)?[eE][+-]?\d+)", s):
        try:
            return float(s)
        except ValueError:
            pass
    if up.endswith(("_DIR", "_PATH")):  # NB: "_DIR_NAME" stays a plain string
        return Path(s)
    return s


def _default_for(name: str) -> Any:
    """Name-based safe default for a key absent from all sources."""
    if name in _EXPLICIT_DEFAULTS:
        return _EXPLICIT_DEFAULTS[name]
    up = name.upper()
    if up.endswith("_VERSION"):
        return "1.0.0"
    if up.endswith("_DIR_NAME"):
        return name.lower()
    # Unknown feature flags default to enabled — preserves prior behaviour and is
    # harmless under the research-only / no-real-order invariant.
    if up.startswith(_FLAG_PREFIXES) or up.endswith(_FLAG_SUFFIXES):
        return True
    if up.endswith(_INT_SUFFIXES):
        return 0
    if up.endswith(_FLOAT_SUFFIXES):
        return 0.0
    if up.endswith(("_DIR", "_PATH")):
        return None
    return None


_RAW_CACHE: dict[str, str] | None = None


def _load_raw() -> dict[str, str]:
    """Merge .env.example < .env < os.environ once, then cache."""
    global _RAW_CACHE
    if _RAW_CACHE is None:
        merged: dict[str, str] = {}
        merged.update(_parse_env_file(_ENV_EXAMPLE))
        merged.update(_parse_env_file(_ENV_FILE))
        for k, v in os.environ.items():
            if k.isupper():  # ignore PATH-style mixed-case OS noise
                merged[k] = v
        _RAW_CACHE = merged
    return _RAW_CACHE


def reload_settings() -> "Settings":
    """Drop the cache and rebuild the singleton (useful in tests / after edits)."""
    global _RAW_CACHE, _settings
    _RAW_CACHE = None
    _settings = Settings()
    return _settings


class Settings:
    """Attribute-style access to coerced configuration values.

    Any uppercase attribute is resolved lazily: looked up in the merged raw map,
    coerced to a native type, and cached. Unknown keys fall back to a safe,
    name-based default (never the old ``"mock_value"`` sentinel).
    """

    def __init__(self, **overrides: Any) -> None:
        raw = dict(_load_raw())
        for k, v in overrides.items():
            raw[k] = v if isinstance(v, str) else str(v)
        object.__setattr__(self, "_raw", raw)
        object.__setattr__(self, "_coerced", {})

    def __getattr__(self, name: str) -> Any:
        # __getattr__ is only invoked when normal lookup fails.
        if name.startswith("_"):
            raise AttributeError(name)
        raw = object.__getattribute__(self, "_raw")
        cache = object.__getattribute__(self, "_coerced")
        if name in cache:
            return cache[name]
        if name in raw:
            value = _coerce(name, raw[name])
        elif name in DEFAULTS:
            value = DEFAULTS[name]
        else:
            value = _default_for(name)
        cache[name] = value
        return value

    def get(self, name: str, default: Any = None) -> Any:
        raw = object.__getattribute__(self, "_raw")
        if name in raw:
            return getattr(self, name)
        return default

    def as_dict(self) -> dict[str, Any]:
        """Coerce and return every known key (diagnostics / healthcheck)."""
        raw = object.__getattribute__(self, "_raw")
        keys = set(raw) | set(DEFAULTS)
        return {k: getattr(self, k) for k in sorted(keys)}


_settings = Settings()


def get_settings() -> Settings:
    return _settings


settings = _settings
