"""Current exposure scale from the paper book's daily NAV history (reuses risk.daily_overlay.apply_overlay).

Causal: only COMPLETED sessions (dates strictly before ``asof``) feed the overlay; one extra zero-return
"tomorrow" row is appended so the last exposure is the one decided from information known today.
Note: the NAV already reflects past de-risking, so it is treated as the strategy return stream (approximation).

Fail-closed convention: fewer than 2 completed NAV points => scale 1.0 with reason 'warmup' (nothing to
de-risk on); any exception => scale 0.5 with reason 'overlay_error' (logged). Scale is always in [0, 1].

Paper/simulation only. No real order sent.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)
NO_ORDER = "No real order sent."
ERROR_SCALE = 0.5


@dataclass
class OverlayGateResult:
    scale: float
    reasons: list = field(default_factory=list)
    n_nav_points: int = 0
    note: str = NO_ORDER

    def to_dict(self) -> dict:
        return {"scale": self.scale, "reasons": list(self.reasons), "n_nav_points": self.n_nav_points,
                "note": self.note}


class OverlayGate:
    def __init__(self, settings: Any = None, nav_history: Optional[pd.Series] = None, path: Any = None,
                 regime_scale: Optional[pd.Series] = None):
        self.settings = settings
        self._nav: dict[date, float] = {}
        self._path = Path(path) if path is not None else None
        self.regime_scale = regime_scale
        if nav_history is not None:
            for k, v in pd.Series(nav_history).items():
                self._nav[pd.Timestamp(k).date()] = float(v)
        elif self._path is not None:
            self._load()

    # ------------------------------------------------------------ history
    def _load(self) -> None:
        try:
            if self._path is not None and self._path.exists():
                raw = json.loads(self._path.read_text(encoding="utf-8"))
                self._nav = {date.fromisoformat(k): float(v) for k, v in raw.items()}
        except Exception as e:
            logger.warning("overlay nav history load failed: %s", e)

    def record(self, day: Any, equity: float) -> None:
        """Remember the latest equity of ``day`` (last write of a date wins)."""
        d = day.date() if isinstance(day, datetime) else pd.Timestamp(day).date()
        eq = float(equity)
        if not (eq > 0) or eq != eq or eq in (float("inf"),):
            return
        self._nav[d] = eq
        if self._path is not None:
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                self._path.write_text(json.dumps({k.isoformat(): v for k, v in sorted(self._nav.items())}),
                                      encoding="utf-8")
            except Exception as e:
                logger.debug("overlay nav history save failed: %s", e)

    # ------------------------------------------------------------ scale
    def current_scale(self, asof: Any = None) -> OverlayGateResult:
        try:
            return self._compute(asof)
        except Exception as e:
            logger.error("overlay gate error, falling back to scale %.2f: %s", ERROR_SCALE, e)
            return OverlayGateResult(ERROR_SCALE, [f"overlay_error:{e}"], len(self._nav))

    def _compute(self, asof: Any) -> OverlayGateResult:
        from bist_signal_bot.risk.daily_overlay import HALT_EXPOSURE, OverlayConfig, apply_overlay, dd_scale

        today = None if asof is None else (asof.date() if isinstance(asof, datetime) else pd.Timestamp(asof).date())
        days = sorted(d for d in self._nav if today is None or d < today)
        if len(days) < 2:
            return OverlayGateResult(1.0, ["warmup"], len(days))
        nav = pd.Series([self._nav[d] for d in days], index=pd.DatetimeIndex([pd.Timestamp(d) for d in days]))
        rets = nav.pct_change().dropna()
        nxt = rets.index[-1] + pd.tseries.offsets.BDay(1)
        rets = pd.concat([rets, pd.Series([0.0], index=pd.DatetimeIndex([nxt]))])  # tomorrow: exposure only
        cfg = OverlayConfig.from_settings(self.settings)
        res = apply_overlay(rets, self.regime_scale, pd.Series(0.0, index=rets.index), cfg)
        scale = max(0.0, min(1.0, float(res.exposure.iloc[-1])))
        comp = res.components.iloc[-1]
        reasons: list = []
        if scale <= HALT_EXPOSURE:
            reasons.append("halt")
        if dd_scale(float(comp["dd_eff"]), cfg) < 0.999 or float(comp["ramp"]) < 0.999:
            reasons.append("drawdown derisk")
        if float(comp["vol_scale"]) < 0.999:
            reasons.append("vol target")
        if float(comp["regime_scale"]) < 0.999:
            reasons.append("regime")
        return OverlayGateResult(scale, reasons, len(days))
