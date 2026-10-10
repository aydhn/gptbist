"""Random-score PLACEBO family for forward noise calibration. Simulation only; no real order is ever sent.

Scores are a stateless hash of (seed, session date, symbol): fully deterministic, causal (a date's score never depends
on other dates or on which other symbols exist) and identical on every re-run. NOT registered in the research
registry (``DAILY_FAMILIES``); only the forward job resolves it through ``all_families``.
"""
from __future__ import annotations

import zlib

import numpy as np
import pandas as pd

NAME = "placebo_random"
_M = (1 << 64) - 1


def _mix(x: np.ndarray) -> np.ndarray:  # splitmix64 finaliser (array ops wrap modulo 2**64 silently)
    x = x ^ (x >> np.uint64(30))
    x = x * np.uint64(0xBF58476D1CE4E5B9)
    x = x ^ (x >> np.uint64(27))
    x = x * np.uint64(0x94D049BB133111EB)
    return x ^ (x >> np.uint64(31))


class RandomScorePlacebo:
    name = NAME
    default_grid = {"seed": [0]}

    def valid(self, params: dict) -> bool:
        return True

    def score(self, ctx, params: dict) -> pd.DataFrame:
        seed = int(params.get("seed", 0))
        sym = np.array([zlib.crc32(s.encode("utf-8")) for s in ctx.symbols], dtype=np.uint64)
        day = np.array([pd.Timestamp(d).toordinal() for d in ctx.index], dtype=np.uint64)
        salt = np.uint64((seed * 0x9E3779B97F4A7C15 + 0x1234567) & _M)
        x = _mix(_mix(sym[None, :] ^ salt) + day[:, None] * np.uint64(0xD6E8FEB86659FD93))
        return pd.DataFrame((x >> np.uint64(11)).astype(np.float64) / float(1 << 53), index=ctx.index,
                            columns=ctx.symbols)


PLACEBO = RandomScorePlacebo()


def all_families() -> dict:
    """Research daily families + the forward-only placebo."""
    from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
    return {**DAILY_FAMILIES, NAME: PLACEBO}
