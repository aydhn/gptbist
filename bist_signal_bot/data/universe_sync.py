"""Dynamic full-BIST universe sync from Yahoo's official screener API (yfinance.screen).

Research/paper only. Fail-closed: a failed or implausibly small listing changes nothing.
The listing is NOT verified against the official Borsa Istanbul list.
"""

import json
import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from bist_signal_bot.core.logging_setup import get_logger
from bist_signal_bot.data.models import AssetType, SymbolGroup, SymbolInfo
from bist_signal_bot.data.symbol_universe import DEFAULT_SEED_SYMBOLS_STR
from bist_signal_bot.data.universe_store import UniverseStore

logger = get_logger(__name__)

PAGE_SIZE = 250
STATE_FILE_NAME = "universe_sync_state.json"
NO_ORDER = "No real order sent."


@dataclass
class UniverseSyncResult:
    added: list[str] = field(default_factory=list)
    reactivated: list[str] = field(default_factory=list)
    deactivated: list[str] = field(default_factory=list)
    unchanged: int = 0
    new_ipos: list[str] = field(default_factory=list)
    total: int = 0
    skipped_reason: str | None = None
    dry_run: bool = False

    def summary(self) -> dict[str, Any]:
        return {
            "added": len(self.added),
            "reactivated": len(self.reactivated),
            "deactivated": len(self.deactivated),
            "unchanged": self.unchanged,
            "new_ipos": list(self.new_ipos),
            "total": self.total,
            "skipped_reason": self.skipped_reason,
            "dry_run": self.dry_run,
            "note": NO_ORDER,
        }


def _default_fetch(sleep: Callable[[float], None] = time.sleep, max_retries: int = 4) -> list[dict]:
    """Page through yfinance's screener for exchange == IST."""
    import yfinance as yf

    query = yf.EquityQuery("eq", ["exchange", "IST"])
    quotes: list[dict] = []
    offset = 0
    total = None
    while total is None or offset < total:
        resp = None
        for attempt in range(max_retries):
            try:
                resp = yf.screen(query, size=PAGE_SIZE, offset=offset)
                break
            except Exception as e:  # network / rate limit
                if attempt == max_retries - 1:
                    raise
                logger.warning("screener page offset=%s failed (%s); retrying", offset, e)
                sleep(2.0 * (2 ** attempt))
        page = (resp or {}).get("quotes") or []
        total = int((resp or {}).get("total") or 0)
        quotes.extend(page)
        if not page:
            break
        offset += PAGE_SIZE
        if offset < total:
            sleep(1.0)
    return quotes


_NON_EQUITY_NAME_RE = re.compile(
    r"\b(warrants?|varant|e\.?t\.?f|exchange traded fund|borsa yat[iı]r[iı]m fonu|"
    r"yat[iı]r[iı]m fonu|mutual fund|fund of funds|rights?|r[uü]chan|"
    r"index|endeks|sertifika|certificate|gayrimenkul sertifikas[iı])\b",
    re.IGNORECASE,
)
# Name tokens too ambiguous for real companies ("Index"/"Rights"/"Fund" appear in legit names such as
# "... Yatirim Holding"), so only unambiguous instrument words above are matched, on word boundaries.


def is_non_equity_listing(sym: str, name: str | None, quote: dict | None = None) -> bool:
    """Conservative non-common-stock detector (warrants, ETFs, funds, index-like, rights).

    Seed symbols are never classified as non-equity. Symbols with '^' / '=' / '-' are already
    dropped by the alphanumeric check; here we match on explicit Yahoo type hints and unambiguous names.
    """
    if sym in DEFAULT_SEED_SYMBOLS_STR:
        return False
    q = quote or {}
    for key in ("typeDisp", "quoteSourceName", "instrumentType"):
        v = str(q.get(key, "") or "").lower()
        if any(t in v for t in ("etf", "fund", "warrant", "index", "right")):
            return True
    return bool(name and _NON_EQUITY_NAME_RE.search(name))


def fetch_ist_listing(fetch: Callable[[], list[dict]] | None = None) -> list[dict]:
    """Return normalized listing rows: symbol, name, first_trade_date (ISO or None).

    Keeps quoteType == EQUITY only, then drops warrants/ETFs/funds/index-like/rights
    (see ``is_non_equity_listing``). Seed symbols are never dropped.
    """
    raw = (fetch or _default_fetch)()
    out: dict[str, dict] = {}
    for q in raw or []:
        if str(q.get("quoteType", "")).upper() != "EQUITY":
            continue
        sym = str(q.get("symbol", "")).upper()
        if sym.endswith(".IS"):
            sym = sym[:-3]
        if not sym or not (sym.isascii() and sym.isalnum()):
            continue
        if is_non_equity_listing(sym, q.get("longName") or q.get("shortName"), q):
            continue
        ftd = None
        ms = q.get("firstTradeDateMilliseconds")
        if ms:
            try:
                ftd = datetime.fromtimestamp(float(ms) / 1000.0, tz=UTC).date().isoformat()
            except (ValueError, OverflowError, OSError):
                ftd = None
        out[sym] = {
            "symbol": sym,
            "name": q.get("longName") or q.get("shortName"),
            "first_trade_date": ftd,
            "avg_volume_3m": q.get("averageDailyVolume3Month"),
            "market_cap": q.get("marketCap"),
        }
    return list(out.values())


def _state_path(store: UniverseStore) -> Path:
    return store.get_universe_dir() / STATE_FILE_NAME


def load_sync_state(store: UniverseStore) -> dict:
    p = _state_path(store)
    if not p.exists():
        return {"misses": {}, "sync_deactivated": [], "last_sync": None}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        data.setdefault("misses", {})
        data.setdefault("sync_deactivated", [])
        data.setdefault("last_sync", None)
        return data
    except Exception:
        return {"misses": {}, "sync_deactivated": [], "last_sync": None}


def last_sync_age(settings, store: UniverseStore | None = None) -> timedelta | None:
    store = store or UniverseStore(settings)
    ts = load_sync_state(store).get("last_sync")
    if not ts:
        return None
    try:
        return datetime.now(UTC) - datetime.fromisoformat(ts)
    except ValueError:
        return None


def sync_universe(settings, fetch: Callable[[], list[dict]] | None = None, dry_run: bool = False,
                  now: datetime | None = None) -> UniverseSyncResult:
    res = UniverseSyncResult(dry_run=dry_run)
    store = UniverseStore(settings)
    now = now or datetime.now(UTC)
    min_listing = int(getattr(settings, "INTRADAY_UNIVERSE_MIN_LISTING", 300))
    ipo_days = int(getattr(settings, "INTRADAY_UNIVERSE_IPO_DAYS", 90))
    delist_misses = int(getattr(settings, "INTRADAY_UNIVERSE_DELIST_MISSES", 10))

    try:
        listing = fetch_ist_listing(fetch)
    except Exception as e:
        res.skipped_reason = f"fetch failed: {e}"
        return res
    if len(listing) < min_listing:
        res.skipped_reason = f"listing too small ({len(listing)} < {min_listing}); nothing changed"
        return res

    by_sym = {r["symbol"]: r for r in listing}
    universe = store.load_universe()
    if not universe.list_symbols(active_only=False):
        from bist_signal_bot.data.symbol_universe import DEFAULT_SEED_SYMBOLS
        for info in DEFAULT_SEED_SYMBOLS:
            universe.add_symbol(info.model_copy(deep=True))
    state = load_sync_state(store)
    misses: dict[str, int] = {k: int(v) for k, v in state["misses"].items()}
    sync_deact = set(state["sync_deactivated"])
    seeds = set(DEFAULT_SEED_SYMBOLS_STR)
    cutoff = (now - timedelta(days=ipo_days)).date().isoformat()

    for sym, row in by_sym.items():
        ftd = row["first_trade_date"]
        if ftd and ftd >= cutoff:
            res.new_ipos.append(sym)
        misses.pop(sym, None)
        if not universe.contains(sym):
            note = "yahoo-screener" + (f"; first_trade={ftd}" if ftd else "")
            universe.add_symbol(SymbolInfo(symbol=sym, name=row["name"], asset_type=AssetType.EQUITY,
                                           groups={SymbolGroup.CUSTOM}, is_active=True, notes=note))
            res.added.append(sym)
        else:
            info = universe.require(sym)
            if not info.is_active and sym in sync_deact:
                universe.activate_symbol(sym)
                sync_deact.discard(sym)
                res.reactivated.append(sym)
            else:
                res.unchanged += 1

    for sym in universe.list_symbols(active_only=True):
        if sym in by_sym:
            continue
        misses[sym] = misses.get(sym, 0) + 1
        if sym in seeds:
            continue  # seeds are never dropped by sync
        if misses[sym] >= delist_misses:
            universe.deactivate_symbol(sym)
            sync_deact.add(sym)
            res.deactivated.append(sym)
        else:
            res.unchanged += 1

    res.total = universe.count(active_only=True)
    if dry_run:
        return res

    store.save_universe(universe)
    state = {"misses": misses, "sync_deactivated": sorted(sync_deact), "last_sync": now.isoformat(),
             "new_ipos": res.new_ipos}
    _state_path(store).write_text(json.dumps(state, indent=2), encoding="utf-8")

    try:  # survivorship snapshot
        from bist_signal_bot.intraday.archive import BarArchive
        archive = BarArchive(settings=settings)
        try:
            archive.snapshot_universe(now.date(), universe.list_symbols(active_only=True))
        finally:
            archive.close()
    except Exception as e:
        logger.warning("archive snapshot after universe sync failed: %s", e)

    try:  # audit (best effort)
        from bist_signal_bot.core.audit import AuditEventType, AuditLogger
        AuditLogger(settings).log_universe_update(
            AuditEventType.UNIVERSE_IMPORT,
            f"Universe sync: +{len(res.added)} react={len(res.reactivated)} -{len(res.deactivated)}. {NO_ORDER}",
            "sync", res.added + res.reactivated + res.deactivated,
            file_path=str(store.get_universe_file_path()),
        )
    except Exception as e:
        logger.warning("universe sync audit failed: %s", e)
    return res


def sync_if_stale(settings, fetch=None, max_age: timedelta = timedelta(days=1)) -> UniverseSyncResult | None:
    """Sync only when INTRADAY_UNIVERSE_AUTO_SYNC and last sync older than max_age. Never raises."""
    try:
        if not getattr(settings, "INTRADAY_UNIVERSE_AUTO_SYNC", True):
            return None
        age = last_sync_age(settings)
        if age is not None and age < max_age:
            return None
        return sync_universe(settings, fetch=fetch)
    except Exception as e:
        logger.warning("auto universe sync failed: %s", e)
        return None
