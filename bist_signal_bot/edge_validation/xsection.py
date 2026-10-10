"""Cross-sectional daily research layer: DailyContext, ScoreFamily protocol, portfolio events + NAV.

Research/paper only; long-only, equal weight, no leverage. No real order is ever sent.

Timing convention (same as ``labels_daily``): the decision is taken at the CLOSE of day ``t0`` using data <= t0;
entry at the OPEN of the next session (``t_entry``); exit at the CLOSE of ``t0 + horizon`` trading days (``t1``).
With ``rebalance_every >= horizon`` holds never overlap: a basket is bought at open t0+1 and sold at close
t0+h, the next decision is at close t0+h (or later) and its entry is the following open.

Survivorship: the panel only contains the symbols the archive holds (currently active names). Delisted names
are absent, so results are optimistic (survivorship bias). Always carry ``SURVIVORSHIP_WARNING`` into reports.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Sequence, runtime_checkable

import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.cash_benchmark import daily_cash_returns

NO_ORDER = "No real order sent."
SURVIVORSHIP_WARNING = ("Survivorship bias: universe = currently active symbols; delisted names are absent, "
                        "so results are optimistic.")
EVENT_COLS = ["t0", "t_entry", "t1", "symbol", "gross_ret", "raw_ret", "price", "order_value",
              "bar_value_try", "rebalance_date", "rank", "score", "exposure_scale"]


def _setting(settings, key, default):
    if settings is None:
        return default
    try:
        v = getattr(settings, key)
        return default if v is None else v
    except AttributeError:
        return default


class DailyContext:
    """Aligned daily matrices (date x symbol) + benchmark XU100 + cash returns.

    All derived quantities (ADV, universe mask) are causal: row t depends on rows <= t only.
    """

    def __init__(self, open_: pd.DataFrame, close: pd.DataFrame, volume: pd.DataFrame,
                 benchmark: Optional[pd.Series] = None, cash_ret: Optional[pd.Series] = None, *,
                 min_adv: float = 5e6, adv_window: int = 20, min_history: int = 60, min_price: float = 1.0,
                 capital: float = 100_000.0, cash_rate: float = 0.37, cash_withholding: float = 0.0,
                 usdtry: Optional[pd.Series] = None):
        idx = close.index
        self.open = open_.reindex(index=idx, columns=close.columns).astype(float)
        self.close = close.astype(float)
        self.volume = volume.reindex(index=idx, columns=close.columns).astype(float)
        self.value = self.close * self.volume  # traded value TRY
        self.symbols: List[str] = list(close.columns)
        self.index: pd.DatetimeIndex = pd.DatetimeIndex(idx)
        self.benchmark = None if benchmark is None else benchmark.reindex(self.index).astype(float)
        self.usdtry = self._align_series(usdtry, self.index)
        self.min_adv, self.adv_window, self.min_history = float(min_adv), int(adv_window), int(min_history)
        self.min_price, self.capital = float(min_price), float(capital)
        self.cash_rate, self.cash_withholding = float(cash_rate), float(cash_withholding)
        self.cash_ret = (cash_ret.reindex(self.index).fillna(0.0) if cash_ret is not None else
                         daily_cash_returns(self.index, self.cash_rate, self.cash_withholding))
        self._adv = self._mask = None

    @staticmethod
    def _align_series(s: Optional[pd.Series], index) -> Optional[pd.Series]:
        """Causal alignment of an external daily series (last known value carried forward onto the sessions)."""
        if s is None or len(s) == 0:
            return None
        s = s.astype(float).sort_index()
        s = s[~s.index.duplicated(keep="last")]
        return s.reindex(s.index.union(index)).ffill().reindex(index)

    # ---- construction ----
    @classmethod
    def from_panel(cls, panel: Dict[str, pd.DataFrame], benchmark: Optional[pd.Series] = None,
                   settings=None, usdtry: Optional[pd.Series] = None, **overrides) -> "DailyContext":
        syms = sorted(panel)
        if not syms:
            raise ValueError("empty panel")
        idx = pd.DatetimeIndex(sorted(set().union(*[set(d.index) for d in panel.values()])))
        mk = lambda c: pd.DataFrame({s: panel[s][c] for s in syms}).reindex(idx)  # noqa: E731
        kw = dict(min_adv=float(_setting(settings, "DAILY_MIN_ADV_TRY", 5e6)),
                  adv_window=int(_setting(settings, "DAILY_ADV_WINDOW", 20)),
                  min_history=int(_setting(settings, "DAILY_MIN_HISTORY_DAYS", 60)),
                  min_price=float(_setting(settings, "DAILY_MIN_PRICE_TRY", 1.0)),
                  capital=float(_setting(settings, "DAILY_CAPITAL_TRY", 100_000.0)),
                  cash_rate=float(_setting(settings, "CASH_BENCHMARK_ANNUAL_RATE", 0.37)),
                  cash_withholding=float(_setting(settings, "CASH_BENCHMARK_WITHHOLDING", 0.0)))
        kw.update(overrides)
        return cls(mk("open"), mk("close"), mk("volume"), benchmark, None, usdtry=usdtry, **kw)

    @classmethod
    def from_archive(cls, archive, symbols=None, settings=None, **overrides) -> "DailyContext":
        from bist_signal_bot.daily.panel import load_benchmark, load_daily_panel
        panel = load_daily_panel(archive, symbols)
        bm = load_benchmark(archive, "XU100")
        fx = load_benchmark(archive, "USDTRY")
        return cls.from_panel(panel, bm["close"] if len(bm) else None, settings,
                              usdtry=fx["close"] if len(fx) else None, **overrides)

    # ---- causal derived data ----
    @property
    def adv(self) -> pd.DataFrame:
        """ADV (TRY) over ``adv_window`` sessions ending at t (inclusive), min_periods=window."""
        if self._adv is None:
            self._adv = self.value.rolling(self.adv_window, min_periods=self.adv_window).mean()
        return self._adv

    @property
    def universe_mask(self) -> pd.DataFrame:
        """Point-in-time eligibility at the close of t: ADV>=min, enough history, price>=min, traded today."""
        if self._mask is None:
            hist = self.close.notna().cumsum()
            self._mask = ((self.adv >= self.min_adv) & (hist >= self.min_history) &
                          (self.close >= self.min_price) & (self.volume > 0) & self.close.notna())
        return self._mask

    def lag(self, df: pd.DataFrame, k: int = 1) -> pd.DataFrame:
        """Strictly causal shift: row t holds the value known k sessions earlier."""
        if k < 0:
            raise ValueError("lag must be >= 0 (negative would look ahead)")
        return df.shift(k)

    def truncate(self, n_rows: int) -> "DailyContext":
        """Context with only the first ``n_rows`` sessions (used by causality tests)."""
        sl = slice(0, int(n_rows))
        return DailyContext(self.open.iloc[sl], self.close.iloc[sl], self.volume.iloc[sl],
                            None if self.benchmark is None else self.benchmark.iloc[sl], self.cash_ret.iloc[sl],
                            min_adv=self.min_adv, adv_window=self.adv_window, min_history=self.min_history,
                            min_price=self.min_price, capital=self.capital, cash_rate=self.cash_rate,
                            cash_withholding=self.cash_withholding,
                            usdtry=None if self.usdtry is None else self.usdtry.iloc[sl])

    def benchmarks(self) -> pd.DataFrame:
        """Daily returns: cash, xu100 (if available), ew_universe (equal weight of the point-in-time universe
        known at the previous close, close-to-close, no costs)."""
        ret = self.close.pct_change(fill_method=None)
        held = self.universe_mask.shift(1, fill_value=False)
        ew = ret.where(held).mean(axis=1).fillna(0.0)
        out = {"cash": self.cash_ret.astype(float), "ew_universe": ew}
        if self.benchmark is not None:
            out["xu100"] = self.benchmark.pct_change(fill_method=None)
        return pd.DataFrame(out, index=self.index)


@runtime_checkable
class ScoreFamily(Protocol):
    """A cross-sectional score family. ``score`` must use only data <= each row's date (long-only: higher =
    better). Register instances in ``families_daily.DAILY_FAMILIES``."""
    name: str
    default_grid: dict

    def valid(self, params: dict) -> bool: ...

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame: ...


def check_score_causality(family: ScoreFamily, ctx: DailyContext, params: dict,
                          cuts: Sequence[float] = (0.5, 0.7, 0.9), atol: float = 1e-10) -> None:
    """Raise AssertionError if truncating future rows changes any earlier score (look-ahead detector)."""
    full = family.score(ctx, params).reindex(index=ctx.index, columns=ctx.symbols)
    for c in cuts:
        k = max(2, int(len(ctx.index) * c))
        part = family.score(ctx.truncate(k), params).reindex(index=ctx.index[:k], columns=ctx.symbols)
        a, b = full.iloc[:k].to_numpy(float), part.to_numpy(float)
        same = (np.isnan(a) & np.isnan(b)) | np.isclose(a, b, atol=atol, rtol=1e-9, equal_nan=False)
        if not same.all():
            raise AssertionError(f"{family.name}{params}: score changes when future rows are truncated "
                                 f"(cut={k}, {int((~same).sum())} cells) -> look-ahead")


@dataclass
class PortfolioResult:
    events: pd.DataFrame
    ctx: DailyContext
    horizon: int
    top_n: int
    rebalance_every: int
    n_rebalances: int = 0
    n_dropped_untradable: int = 0
    nav_gross: Optional[pd.DataFrame] = None
    benchmarks: Optional[pd.DataFrame] = None
    notes: List[str] = field(default_factory=list)

    def nav_net(self, cost_model) -> pd.DataFrame:
        return nav_returns(self.ctx, self.events, cost_model)


def build_portfolio_events(ctx: DailyContext, scores: pd.DataFrame, horizon: int, top_n: int = 8,
                           rebalance_every: Optional[int] = None, entry: str = "next_open",
                           regime_scale: Optional[pd.Series] = None, regime_fill: float = 1.0,
                           rebalance_mask: Optional[pd.Series] = None) -> PortfolioResult:
    """Top-N long-only equal-weight baskets at each rebalance.

    Events columns: EVENT_COLS. ``gross_ret`` is the return on the SLOT capital: raw position return when
    exposure_scale==1; with regime scaling it is ``scale*raw + (1-scale)*cash_return_over_hold`` (the unused
    part of the slot earns cash). ``raw_ret`` = close[t1]/open[t_entry]-1 (same as
    ``labels_daily.forward_return_labels_daily``). ``order_value = capital/top_n*scale``. Missing regime
    values (warm-up) use ``regime_fill`` (1.0 = fully exposed; documented, not guessed from data).
    Eligible = point-in-time universe mask at t0 AND finite score. Names that cannot be bought at the next open
    (no open price / zero volume that day) or have no exit close are dropped (stay in cash), not replaced.
    ``rebalance_mask`` (optional bool Series over dates, causal: value at t known at close t): a basket is only
    started on a decision date where the mask is True (first True date at/after the previous exit); all other
    days stay in cash (earning the cash rate in ``nav_returns``). None => unchanged behaviour.
    """
    if horizon < 1 or top_n < 1:
        raise ValueError("horizon and top_n must be >= 1")
    if entry != "next_open":
        raise NotImplementedError("only entry='next_open' is supported")
    every = int(rebalance_every or horizon)
    if every < horizon:
        raise ValueError("rebalance_every must be >= horizon (overlapping baskets are not supported)")
    idx, n = ctx.index, len(ctx.index)
    S = scores.reindex(index=idx, columns=ctx.symbols).to_numpy(float)
    M = ctx.universe_mask.to_numpy(bool)
    OP, CL = ctx.open.to_numpy(float), ctx.close.to_numpy(float)
    VOL, ADV = ctx.volume.to_numpy(float), ctx.adv.to_numpy(float)
    syms = np.array(ctx.symbols, dtype=object)
    cash = ctx.cash_ret.to_numpy(float)
    if regime_scale is not None:
        sc = regime_scale.reindex(idx.union(regime_scale.index)).ffill().reindex(idx).fillna(regime_fill)
        sc = sc.clip(0.0, 1.0).to_numpy(float)
    else:
        sc = np.ones(n)
    elig = M & np.isfinite(S)
    RM = None if rebalance_mask is None else (
        rebalance_mask.reindex(idx).fillna(False).astype(bool).to_numpy())
    anyrow = np.flatnonzero(elig.any(axis=1))
    rows, dropped, n_reb = [], 0, 0
    if len(anyrow):
        i = int(anyrow[0])
        while i + horizon <= n - 1:
            if RM is not None and not RM[i]:
                i += 1
                continue
            e, x = i + 1, i + horizon
            cand = np.flatnonzero(elig[i])
            if len(cand):
                n_reb += 1
                order = np.lexsort((cand, -S[i, cand]))  # score desc, ties by column (symbol) order
                pick = cand[order][:top_n]
                scale = float(sc[i])
                cash_hold = float(np.prod(1.0 + cash[e:x + 1]) - 1.0)
                for rank, j in enumerate(pick, 1):
                    px, ex = OP[e, j], CL[x, j]
                    if not (np.isfinite(px) and px > 0 and np.isfinite(ex) and VOL[e, j] > 0):
                        dropped += 1
                        continue
                    raw = ex / px - 1.0
                    rows.append((idx[i], idx[e], idx[x], syms[j], scale * raw + (1.0 - scale) * cash_hold,
                                 raw, px, ctx.capital / top_n * scale, ADV[i, j], idx[i], rank, S[i, j], scale))
            i += every
    ev = pd.DataFrame(rows, columns=EVENT_COLS)
    res = PortfolioResult(ev, ctx, horizon, top_n, every, n_reb, dropped)
    res.nav_gross = nav_returns(ctx, ev, None)
    res.benchmarks = ctx.benchmarks()
    return res


def nav_returns(ctx: DailyContext, events: pd.DataFrame, cost_model=None) -> pd.DataFrame:
    """Daily portfolio returns (all sessions) from non-overlapping baskets; remainder in cash at cash_ret.

    Within a hold: each position is buy-and-hold from the entry open (value = w*close_t/open_entry, w =
    order_value/capital); the uninvested part (1-sum w) compounds at the cash return. Round-trip trading cost
    (cost_model, as fraction of entry notional) is deducted on the exit day; events with NaN cost
    (disallowed by the cost model) are excluded, exactly as the gate excludes them. Idle days earn cash.
    Returns DataFrame[ret, nav, holdings, cash_frac_invested].
    """
    idx, n = ctx.index, len(ctx.index)
    ret = ctx.cash_ret.to_numpy(float).copy()
    cash = ret.copy()
    hold_n, invested = np.zeros(n), np.zeros(n)
    ev = events
    if cost_model is not None and len(ev):
        cf = -np.asarray(cost_model.apply_costs(np.zeros(len(ev)), ev["price"].to_numpy(float),
                                                ev["order_value"].to_numpy(float),
                                                ev["bar_value_try"].to_numpy(float)), dtype=float)
        ev = ev.assign(cost_frac=cf)
        ev = ev[np.isfinite(ev["cost_frac"])]
    else:
        ev = ev.assign(cost_frac=0.0) if len(ev) else ev
    if len(ev):
        pos = pd.Series(np.arange(n), index=idx)
        col = pd.Series(np.arange(len(ctx.symbols)), index=ctx.symbols)
        CLf, OP = ctx.close.ffill().to_numpy(float), ctx.open.to_numpy(float)
        for _, g in ev.groupby("rebalance_date", sort=True):
            e, x = int(pos[g["t_entry"].iloc[0]]), int(pos[g["t1"].iloc[0]])
            j = col[g["symbol"]].to_numpy()
            w = g["order_value"].to_numpy(float) / ctx.capital
            W = float(w.sum())
            rel = ((CLf[e:x + 1][:, j] / OP[e, j]) * w).sum(axis=1) + (1.0 - W) * np.cumprod(1.0 + cash[e:x + 1])
            rel[-1] -= float((w * g["cost_frac"].to_numpy(float)).sum())
            prev = np.concatenate([[1.0], rel[:-1]])
            ret[e:x + 1] = rel / prev - 1.0
            hold_n[e:x + 1] = len(g)
            invested[e:x + 1] = W
    ret = np.nan_to_num(ret, nan=0.0)
    return pd.DataFrame({"ret": ret, "nav": np.cumprod(1.0 + ret), "holdings": hold_n,
                         "invested_frac": invested}, index=idx)
