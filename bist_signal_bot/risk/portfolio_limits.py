"""Portfolio-level limits checked before a proposed paper order. Research / paper only."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from bist_signal_bot.risk.sizing_intraday import _cfg, _get, _finite, position_notional

NO_ORDER_NOTE = "No real order sent."


@dataclass
class LimitResult:
    allowed: bool
    reasons: list[str] = field(default_factory=list)
    note: str = NO_ORDER_NOTE


def _corr(corr_matrix: Any, a: str, b: str) -> float | None:
    try:
        if hasattr(corr_matrix, "loc"):
            v = corr_matrix.loc[a, b]
        else:
            v = corr_matrix[a][b]
        return float(v) if _finite(v) else None
    except (KeyError, IndexError, TypeError, ValueError):
        return None


class PortfolioLimits:
    def __init__(self, settings: Any = None):
        self.settings = settings

    def check(self, proposed_order: Any, open_positions: Sequence[Any] | None, equity: float,
              sector_map: dict[str, str] | None = None, corr_matrix: Any = None,
              settings: Any = None, *, traded_today_value: float = 0.0) -> LimitResult:
        """proposed_order / positions: dict or object with symbol and notional (or qty*price).

        traded_today_value: TRY notional already traded today (for the turnover limit).
        """
        s = settings if settings is not None else self.settings
        positions = list(open_positions or [])
        reasons: list[str] = []
        if not _finite(equity) or equity <= 0:
            return LimitResult(False, ["invalid_equity"])

        sym = _get(proposed_order, "symbol", None)
        notional = position_notional(proposed_order)
        by_symbol: dict[str, float] = {}
        for p in positions:
            k = _get(p, "symbol", None)
            by_symbol[k] = by_symbol.get(k, 0.0) + position_notional(p)
        gross = sum(by_symbol.values())

        if sym in by_symbol:
            reasons.append("duplicate_symbol")

        max_open = int(_cfg(s, "RISK_MAX_OPEN_POSITIONS", 10))
        if sym not in by_symbol and len(by_symbol) + 1 > max_open:
            reasons.append("max_open_positions")

        if (gross + notional) > float(_cfg(s, "RISK_MAX_GROSS_EXPOSURE_PCT", 1.0)) * equity + 1e-9:
            reasons.append("max_gross_exposure")

        if (by_symbol.get(sym, 0.0) + notional) > float(_cfg(s, "RISK_MAX_POSITION_PCT", 0.10)) * equity + 1e-9:
            reasons.append("max_single_name")

        if sector_map and sym in sector_map:
            sec = sector_map[sym]
            sec_exp = sum(v for k, v in by_symbol.items() if sector_map.get(k) == sec) + notional
            if sec_exp > float(_cfg(s, "RISK_MAX_SECTOR_PCT", 0.30)) * equity + 1e-9:
                reasons.append("max_sector")

        if corr_matrix is not None:
            thr = float(_cfg(s, "RISK_CORR_THRESHOLD", 0.8))
            cluster = notional
            for k, v in by_symbol.items():
                c = _corr(corr_matrix, sym, k)
                if c is not None and abs(c) > thr:
                    cluster += v
            if cluster > float(_cfg(s, "RISK_MAX_CLUSTER_PCT", 0.25)) * equity + 1e-9 and cluster > notional:
                reasons.append("max_cluster_exposure")

        if (float(traded_today_value) + notional) > float(_cfg(s, "RISK_MAX_DAILY_TURNOVER_PCT", 2.0)) * equity + 1e-9:
            reasons.append("max_daily_turnover")

        return LimitResult(not reasons, reasons)
