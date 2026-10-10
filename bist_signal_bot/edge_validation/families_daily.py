"""Daily cross-sectional score families + registry. Research only; every score uses data <= its row date.

To add a family: implement the ``ScoreFamily`` protocol (name, default_grid, valid(params), score(ctx, params))
and call ``register_family(instance)``. Run ``check_score_causality`` on it in a test.
"""
from __future__ import annotations

from typing import Dict

import pandas as pd

from bist_signal_bot.edge_validation.xsection import DailyContext, ScoreFamily


class XSMomentum:
    """score = close[t-skip] / close[t-lookback] - 1 (return over [t-lookback, t-skip]); higher = better."""
    name = "xs_momentum"
    default_grid = {"lookback": [20, 60, 120, 250], "skip": [0, 5, 20]}

    def valid(self, params: dict) -> bool:
        return 0 <= params.get("skip", 0) < params.get("lookback", 1)

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        lb, sk = int(params["lookback"]), int(params.get("skip", 0))
        if not self.valid({"lookback": lb, "skip": sk}):
            raise ValueError("need 0 <= skip < lookback")
        c = ctx.close
        return c.shift(sk) / c.shift(lb) - 1.0


DAILY_FAMILIES: Dict[str, ScoreFamily] = {}


def register_family(fam: ScoreFamily, overwrite: bool = False) -> ScoreFamily:
    if fam.name in DAILY_FAMILIES and not overwrite:
        raise ValueError(f"daily family {fam.name!r} already registered")
    DAILY_FAMILIES[fam.name] = fam
    return fam


register_family(XSMomentum())


# Additional families live in their own modules and self-register on import.
for _mod in ("families_daily_price", "families_daily_macro", "families_daily_ml", "families_daily_i"):
    try:
        __import__(f"bist_signal_bot.edge_validation.{_mod}")
    except ModuleNotFoundError as _exc:  # module not present yet
        if _mod not in str(_exc):
            raise
