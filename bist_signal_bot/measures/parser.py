"""Pure parser for KAP 'Borsa Istanbul A.S.' VBTS announcement bodies.

Pattern: "...{SYM}.E paylarinda DD/MM/YYYY tarihli islemlerden (seans basindan) DD/MM/YYYY tarihli islemlere
(seans sonuna) kadar {brut takas | tek fiyat islem yontemi | emir paketi tedbiri}...". Multi-symbol announcements
carry one sentence per symbol. Malformed input -> empty list + a warning (never raises)."""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, Optional

from bist_signal_bot.core.logging_setup import get_logger

log = get_logger(__name__)

GROSS_SETTLEMENT = "GROSS_SETTLEMENT"
SINGLE_PRICE = "SINGLE_PRICE"
ORDER_PACKAGE = "ORDER_PACKAGE"
KINDS = (GROSS_SETTLEMENT, SINGLE_PRICE, ORDER_PACKAGE)


@dataclass(frozen=True)
class Measure:
    symbol: str
    type: str
    start: date
    end: date
    announcement_id: str
    publish_date: Optional[date]


_SYM = re.compile(r"\b([A-Z][A-Z0-9]{2,5})\.E\b")
_D = r"(\d{2}/\d{2}/\d{4})"
_RANGE = re.compile(_D + r"\s+tarihli\s+işlemlerden.{0,60}?" + _D + r"\s+tarihli\s+işlemlere.{0,60}?kadar\s+([^.]{0,150})",
                    re.I | re.S)
_TAG = re.compile(r"<[^>]*>")
_WS = re.compile(r"\s+")


def clean_text(raw: str) -> str:
    t = html.unescape(raw or "")
    t = _TAG.sub(" ", t)
    t = html.unescape(t).replace("\xa0", " ")
    return _WS.sub(" ", t).strip()


def _kinds(tail: str) -> List[str]:
    t = tail.casefold()
    out = []
    if "brüt takas" in t or "brut takas" in t:
        out.append(GROSS_SETTLEMENT)
    if "tek fiyat" in t:
        out.append(SINGLE_PRICE)
    if "emir paketi" in t:
        out.append(ORDER_PACKAGE)
    return out


def _pd(s: str) -> Optional[date]:
    try:
        return datetime.strptime(s, "%d/%m/%Y").date()
    except ValueError:
        return None


def _publish(v) -> Optional[date]:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    for f in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(str(v).strip(), f).date()
        except ValueError:
            continue
    return None


def parse_measure_body(html_or_text, publish_date=None, announcement_id="") -> List[Measure]:
    """Return the per-symbol measures found in one announcement body ([] + warning when nothing parses)."""
    if not isinstance(html_or_text, str) or not html_or_text.strip():
        log.warning("measures.parse: empty/non-text body (id=%s)", announcement_id)
        return []
    text = clean_text(html_or_text)
    pub = _publish(publish_date)
    syms = list(_SYM.finditer(text))
    if not syms:
        log.warning("measures.parse: no SYMBOL.E token (id=%s)", announcement_id)
        return []
    out: List[Measure] = []
    pending: List[str] = []
    for k, m in enumerate(syms):
        pending.append(m.group(1))
        end_pos = syms[k + 1].start() if k + 1 < len(syms) else len(text)
        chunk = text[m.end():end_pos]
        found = False
        for r in _RANGE.finditer(chunk):
            s, e, kinds = _pd(r.group(1)), _pd(r.group(2)), _kinds(r.group(3))
            if s is None or e is None or e < s or not kinds:
                continue
            found = True
            for sym in dict.fromkeys(pending):
                for kd in kinds:
                    out.append(Measure(sym, kd, s, e, str(announcement_id), pub))
        if found:
            pending = []
    if not out:
        log.warning("measures.parse: no measure sentence parsed (id=%s)", announcement_id)
    return out
