"""KAP fetcher for Borsa Istanbul VBTS announcements. Heavy (thousands of rate-limited requests): run on demand via
``python -m bist_signal_bot measures sync``. Never used by tests/backtests directly; providers are injectable.

Optional third-party code lives OUTSIDE requirements.txt. Install in a SEPARATE environment, versions pinned:
    pip install pykap==0.2.0 borsapy==0.11.0
(borsapy README: personal / educational use only. pykap was only used to discover the Borsa Istanbul member oid,
which is hard-coded below.) Undocumented KAP endpoint: may change or block at any time.
No real order is ever sent.
"""
from __future__ import annotations

import json
import time
from datetime import date, timedelta
from pathlib import Path
from typing import Callable, Dict, List, Optional

from bist_signal_bot.core.logging_setup import get_logger
from bist_signal_bot.measures.parser import Measure, parse_measure_body
from bist_signal_bot.measures.store import MeasureStore

log = get_logger(__name__)

BIST_OID = "4028e4a14bcf2a06014be4d7e6e256b6"  # Borsa Istanbul A.S. (found with pykap==0.2.0)
LIST_URL = "https://www.kap.org.tr/tr/api/disclosure/members/byCriteria"
MIN_INTERVAL = 2.5
HISTORY_START = date(2018, 1, 1)
INSTALL_HINT = ("borsapy is not installed. Install it in a SEPARATE environment (not the repo .venv): "
                "pip install borsapy==0.11.0 (and pykap==0.2.0 if needed). borsapy: personal/educational use only.")

ListingProvider = Callable[[date, date], List[dict]]
BodyProvider = Callable[[str], str]


class FetcherDependencyError(RuntimeError):
    pass


def default_listing_provider(frm: date, to: date) -> List[dict]:
    import requests  # runtime dependency of the repo
    payload = {"fromDate": frm.isoformat(), "toDate": to.isoformat(), "disclosureClass": "", "subjectList": [],
               "mkkMemberOidList": [BIST_OID], "inactiveMkkMemberOidList": [], "bdkMemberOidList": [],
               "fromSrc": False, "disclosureIndexList": []}
    r = requests.post(LIST_URL, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def default_body_provider() -> BodyProvider:
    try:
        from borsapy._providers.kap import KAPProvider  # optional, guarded
    except ImportError as exc:
        raise FetcherDependencyError(INSTALL_HINT) from exc
    prov = KAPProvider()
    return lambda disclosure_id: prov.get_disclosure_content(disclosure_id) or ""


def _windows(since: date, until: date):
    cur = since
    while cur <= until:
        half_end = date(cur.year, 6, 30) if cur.month <= 6 else date(cur.year, 12, 31)
        yield cur, min(half_end, until)
        cur = half_end + timedelta(days=1)


def is_stock_vbts(summary: str) -> bool:
    return "Volatilite" in (summary or "")


class MeasureFetcher:
    def __init__(self, store: Optional[MeasureStore] = None, listing_provider: Optional[ListingProvider] = None,
                 body_provider: Optional[BodyProvider] = None, interval: float = MIN_INTERVAL,
                 sleep: Callable[[float], None] = time.sleep, today: Optional[date] = None):
        self.store = store or MeasureStore()
        self.raw_dir = self.store.dir / "raw"
        self._listing = listing_provider or default_listing_provider
        self._body = body_provider
        self.interval = max(float(interval), MIN_INTERVAL)  # hard floor: be polite to KAP
        self._sleep = sleep
        self.today = today or date.today()

    def _get_body_provider(self) -> BodyProvider:
        if self._body is None:
            self._body = default_body_provider()
        return self._body

    def list_announcements(self, since: date = HISTORY_START) -> List[dict]:
        rows: Dict[str, dict] = {}
        for a, b in _windows(since, self.today):
            cache = self.raw_dir / f"listing_{a.isoformat()}_{b.isoformat()}.json"
            if b < self.today and cache.exists():
                items = json.loads(cache.read_text(encoding="utf-8"))
            else:
                items = self._listing(a, b)
                self._sleep(self.interval)
                if b < self.today:
                    self.raw_dir.mkdir(parents=True, exist_ok=True)
                    cache.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
            for x in items:
                if is_stock_vbts(x.get("summary", "")):
                    rows[str(x["disclosureIndex"])] = x
        return [rows[k] for k in sorted(rows, key=int)]

    def sync(self, since: date = HISTORY_START, max_bodies: Optional[int] = None) -> dict:
        """Restartable: cached raw bodies are re-parsed without network; only missing ids hit KAP."""
        ann = self.list_announcements(since)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        fetched = cached = failed = 0
        found: List[Measure] = []
        for x in ann:
            aid = str(x["disclosureIndex"])
            p = self.raw_dir / f"{aid}.html"
            if p.exists():
                body, cached = p.read_text(encoding="utf-8"), cached + 1
            else:
                if max_bodies is not None and fetched >= max_bodies:
                    continue
                try:
                    body = self._get_body_provider()(aid)
                except FetcherDependencyError:
                    raise
                except Exception as exc:  # network / endpoint trouble: skip, retry next run
                    failed += 1
                    log.warning("measures.fetch: id=%s failed: %s", aid, exc)
                    self._sleep(self.interval)
                    continue
                fetched += 1
                p.write_text(body or "", encoding="utf-8")
                self._sleep(self.interval)
            found.extend(parse_measure_body(body, x.get("publishDate"), aid))
        new_rows = self.store.upsert(found)
        remaining = sum(1 for x in ann if not (self.raw_dir / f"{x['disclosureIndex']}.html").exists())
        return {"announcements": len(ann), "fetched": fetched, "cached": cached, "failed": failed,
                "remaining_bodies": remaining, "new_rows": new_rows, "parsed_measures": len(found)}
