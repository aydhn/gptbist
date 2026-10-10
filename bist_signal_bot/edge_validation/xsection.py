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

from bist_signal_bot.edge_validation.cash_benchmark import daily_cash_returns, daily_cash_returns_series
from bist_signal_bot.edge_validation.fills_daily import (DailySemantics, bar_health, limit_matrices, limit_pct_series,
                                                         resolve_window)

NO_ORDER = "No real order sent."
SURVIVORSHIP_WARNING = ("Survivorship bias: universe = currently active symbols; delisted names are absent, "
                        "so results are optimistic.")
EVENT_COLS_V1 = ["t0", "t_entry", "t1", "symbol", "gross_ret", "raw_ret", "price", "order_value",
                 "bar_value_try", "rebalance_date", "rank", "score", "exposure_scale"]
# V2 adds realised-exit / capacity / price-limit columns (consumers must tolerate their absence in old frames)
EVENT_COLS = EVENT_COLS_V1 + ["t_exit", "exit_price", "exit_deferred", "entry_value_try", "price_limit_flag"]
# New statistic (fill/lock/health semantics + spread proxy) => NEW ledger family, old '_daily_xs_ew' rows stay untouched.
LEDGER_SUFFIX_V2 = "_daily_xs_ew2"
LEDGER_SUFFIX_BY_MODE_V2 = {"ew_universe": "_xs_ew2", "cash": "_xs_cash2", "none": ""}


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
                 usdtry: Optional[pd.Series] = None, high: Optional[pd.DataFrame] = None,
                 low: Optional[pd.DataFrame] = None, semantics: Optional[DailySemantics] = None,
                 cash_rate_series: Optional[pd.Series] = None):
        idx = close.index
        self.semantics: DailySemantics = semantics or DailySemantics()
        self.has_hl = high is not None and low is not None
        self.open = open_.reindex(index=idx, columns=close.columns).astype(float)
        self.close = close.astype(float)
        self.volume = volume.reindex(index=idx, columns=close.columns).astype(float)
        self.high = (high.reindex(index=idx, columns=close.columns).astype(float) if self.has_hl else self.open)
        self.low = (low.reindex(index=idx, columns=close.columns).astype(float) if self.has_hl else self.open)
        self.value = self.close * self.volume  # traded value TRY
        self.symbols: List[str] = list(close.columns)
        self.index: pd.DatetimeIndex = pd.DatetimeIndex(idx)
        self.benchmark = None if benchmark is None else benchmark.reindex(self.index).astype(float)
        self.usdtry = self._align_series(usdtry, self.index)
        self.min_adv, self.adv_window, self.min_history = float(min_adv), int(adv_window), int(min_history)
        self.min_price, self.capital = float(min_price), float(capital)
        self.cash_rate, self.cash_withholding = float(cash_rate), float(cash_withholding)
        # optional time-varying annual rate (e.g. TLREF); default = constant ``cash_rate`` (unchanged behaviour)
        self.cash_rate_series = cash_rate_series
        if cash_ret is not None:
            self.cash_ret = cash_ret.reindex(self.index).fillna(0.0)
        elif cash_rate_series is not None and len(cash_rate_series):
            self.cash_ret = daily_cash_returns_series(self.index, cash_rate_series, self.cash_withholding,
                                                      fallback_rate=self.cash_rate)
        else:
            self.cash_ret = daily_cash_returns(self.index, self.cash_rate, self.cash_withholding)
        self._adv = self._mask = self._limits = self._healthy = None

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
        has_hl = all(("high" in panel[s].columns and "low" in panel[s].columns) for s in syms)
        kw = dict(min_adv=float(_setting(settings, "DAILY_MIN_ADV_TRY", 5e6)),
                  adv_window=int(_setting(settings, "DAILY_ADV_WINDOW", 20)),
                  min_history=int(_setting(settings, "DAILY_MIN_HISTORY_DAYS", 60)),
                  min_price=float(_setting(settings, "DAILY_MIN_PRICE_TRY", 1.0)),
                  capital=float(_setting(settings, "DAILY_CAPITAL_TRY", 100_000.0)),
                  cash_rate=float(_setting(settings, "CASH_BENCHMARK_ANNUAL_RATE", 0.37)),
                  cash_withholding=float(_setting(settings, "CASH_BENCHMARK_WITHHOLDING", 0.0)))
        kw.setdefault("semantics", DailySemantics.from_settings(settings))
        kw.update(overrides)
        if has_hl:
            kw.setdefault("high", mk("high"))
            kw.setdefault("low", mk("low"))
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
    def limit_pct(self) -> pd.Series:
        """Daily price-limit fraction per session (date dependent; history UNVERIFIED, see sessions)."""
        return self._limit_tables()[0]

    @property
    def limit_down(self) -> pd.DataFrame:
        return self._limit_tables()[1]

    @property
    def limit_up(self) -> pd.DataFrame:
        """Limit-up price per session from the previous (forward-filled) close, tick-floored."""
        return self._limit_tables()[2]

    def _limit_tables(self):
        if self._limits is None:
            pct = limit_pct_series(self.index, self.semantics)
            lo, hi = limit_matrices(self.close, pct)
            self._limits = (pct, lo, hi)
        return self._limits

    @property
    def healthy(self) -> pd.DataFrame:
        """Causal bar-health mask (True = usable bar); see ``fills_daily.bar_health``."""
        if self._healthy is None:
            self._healthy = bar_health(self)
        return self._healthy

    @property
    def universe_mask(self) -> pd.DataFrame:
        """Point-in-time eligibility at the close of t: ADV>=min, enough history, price>=min, traded today and
        (unless legacy) a healthy bar."""
        if self._mask is None:
            hist = self.close.notna().cumsum()
            m = ((self.adv >= self.min_adv) & (hist >= self.min_history) &
                 (self.close >= self.min_price) & (self.volume > 0) & self.close.notna())
            if self.semantics.bar_health:
                m = m & self.healthy
            self._mask = m
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
                            usdtry=None if self.usdtry is None else self.usdtry.iloc[sl],
                            high=self.high.iloc[sl] if self.has_hl else None,
                            low=self.low.iloc[sl] if self.has_hl else None, semantics=self.semantics)

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
    n_unfillable_entry: int = 0   # entries blocked by limit-up open / locked bar (policy cash|next_ranked|flag)
    n_exit_deferred: int = 0      # exits postponed (locked limit-down close or NaN exit close)
    n_exit_carried: int = 0       # subset of the above where the nominal exit close was NaN

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
    Eligible = point-in-time universe mask at t0 AND finite score. Execution semantics come from
    ``ctx.semantics`` (``fills_daily``): entries that are unfillable (zero volume, open at/above limit-up, H==L lock)
    follow the entry policy ('cash' default = slot stays in cash, 'next_ranked', 'flag'); an exit on a locked
    limit-down close is deferred to the first unlocked session and a NaN exit close is carried to the next close
    (legacy semantics: names without an open price/volume or exit close are simply dropped). Events carry
    ``t_exit``/``exit_price``/``exit_deferred``/``entry_value_try``/``price_limit_flag``.
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
    ADV, VAL = ctx.adv.to_numpy(float), ctx.value.to_numpy(float)
    policy = ctx.semantics.entry_policy
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
    rows, dropped, n_reb, n_unfill, n_defer, n_carry = [], 0, 0, 0, 0, 0
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
                ranked = cand[order]
                scale = float(sc[i])
                cash_hold = float(np.prod(1.0 + cash[e:x + 1]) - 1.0)
                w = resolve_window(ctx, i, e, x)
                taken = 0
                for rank, j in enumerate(ranked, 1):
                    if taken >= top_n or (policy != "next_ranked" and rank > top_n):
                        break
                    flag = False
                    if not w.price_ok[j] or w.exit_pos[j] < 0 or not np.isfinite(w.raw[j]):
                        dropped += 1
                        continue
                    if not w.entry_ok[j]:
                        n_unfill += 1
                        if policy == "flag":
                            flag = True
                        else:  # cash: slot stays in cash; next_ranked: try the next name
                            continue
                    px, xr = OP[e, j], int(w.exit_pos[j])
                    if xr > x:
                        n_defer += 1
                        n_carry += int(not np.isfinite(CL[x, j]))
                    taken += 1
                    raw = float(w.raw[j])
                    rows.append((idx[i], idx[e], idx[x], syms[j], scale * raw + (1.0 - scale) * cash_hold,
                                 raw, px, ctx.capital / top_n * scale, ADV[i, j], idx[i], rank, S[i, j], scale,
                                 idx[xr], float(w.exit_px[j]), xr - x, VAL[e, j], flag))
            i += every
    ev = pd.DataFrame(rows, columns=EVENT_COLS)
    res = PortfolioResult(ev, ctx, horizon, top_n, every, n_reb, dropped, n_unfillable_entry=n_unfill,
                          n_exit_deferred=n_defer, n_exit_carried=n_carry)
    res.nav_gross = nav_returns(ctx, ev, None)
    res.benchmarks = ctx.benchmarks()
    return res


from bist_signal_bot.edge_validation.capacity_daily import capacity_report  # noqa: E402,F401  (re-export)

BENCHMARK_MODES = ("ew_universe", "cash", "none")
LEDGER_SUFFIX = {"ew_universe": "_xs_ew", "cash": "_xs_cash", "none": ""}


def ledger_family_name(family: str, benchmark: str, v2: bool = True, placebo: bool = False) -> str:
    """Ledger family for a daily trial stream. v2 (default) = ``LEDGER_SUFFIX_BY_MODE_V2`` (new fill/lock/health/spread
    semantics => new statistic => new family); v2=False reproduces the legacy name (``LEDGER_SUFFIX``)."""
    suf = (LEDGER_SUFFIX_BY_MODE_V2 if v2 else LEDGER_SUFFIX)[benchmark]
    return family + "_daily" + suf + ("__placebo" if placebo else "")


def check_benchmark_mode(mode: str) -> str:
    if mode not in BENCHMARK_MODES:
        raise ValueError(f"benchmark must be in {BENCHMARK_MODES}, got {mode!r}")
    return mode


def benchmark_event_returns(ctx: DailyContext, events: pd.DataFrame, mode: str) -> np.ndarray:
    """Per-event benchmark return over the IDENTICAL window t_entry(open) .. t1(close), on the slot capital.

    * 'ew_universe': ``scale*ew_raw + (1-scale)*cash_hold`` where ``ew_raw`` is the mean of close[t1]/open[t_entry]-1
      over the point-in-time eligible universe at t0 (``universe_mask[t0]``) restricted to names that could be bought
      at the entry open and have an exit close (same fill / lock-deferral / carry rule as the strategy:
      ``fills_daily.resolve_window``). The same exposure scale as the
      event is used, so with regime scaling the excess = scale*(raw - ew_raw).
    * 'cash': cash compounded over the same window (calendar-day accrual of ``ctx.cash_ret``).
    The benchmark leg is frictionless (no costs): conservative for the strategy.
    """
    check_benchmark_mode(mode)
    out = np.zeros(len(events))
    if mode == "none" or len(events) == 0:
        return out
    pos = pd.Series(np.arange(len(ctx.index)), index=ctx.index)
    cash = ctx.cash_ret.to_numpy(float)
    M = ctx.universe_mask.to_numpy(bool)
    scale = events["exposure_scale"].to_numpy(float)
    keys = events[["t0", "t_entry", "t1"]].astype("datetime64[ns]").to_numpy().astype("int64")
    cache: Dict[tuple, tuple] = {}
    for k in range(len(events)):
        key = tuple(keys[k])
        if key not in cache:
            i, e, x = (int(pos[events["t0"].iloc[k]]), int(pos[events["t_entry"].iloc[k]]),
                       int(pos[events["t1"].iloc[k]]))
            cash_hold = float(np.prod(1.0 + cash[e:x + 1]) - 1.0)
            ew = 0.0
            if mode == "ew_universe":
                w = resolve_window(ctx, i, e, x)  # IDENTICAL entry/exit semantics as events and labels
                ok = M[i] & w.ok
                ew = float(w.raw[ok].mean()) if ok.any() else 0.0
            cache[key] = (ew, cash_hold)
        ew, cash_hold = cache[key]
        s = scale[k]
        out[k] = (s * ew + (1.0 - s) * cash_hold) if mode == "ew_universe" else cash_hold
    return out


def apply_benchmark(ctx: DailyContext, events: pd.DataFrame, mode: str,
                    bench_ctx: Optional[DailyContext] = None) -> pd.DataFrame:
    """Events whose ``gross_ret`` is the EXCESS over the benchmark (costs are applied on top by the gate, on the
    strategy leg only). Keeps ``abs_gross_ret`` and ``bench_ret``. mode 'none' returns the events unchanged."""
    check_benchmark_mode(mode)
    if mode == "none" or len(events) == 0:
        return events
    b = benchmark_event_returns(bench_ctx or ctx, events, mode)
    ev = events.copy()
    ev["abs_gross_ret"] = ev["gross_ret"]
    ev["bench_ret"] = b
    ev["gross_ret"] = ev["gross_ret"].to_numpy(float) - b
    return ev


def subset_ctx(ctx: DailyContext, symbols: Sequence[str]) -> DailyContext:
    """Same sessions/params, restricted to ``symbols`` (diagnostics)."""
    cols = [s for s in ctx.symbols if s in set(symbols)]
    return DailyContext(ctx.open[cols], ctx.close[cols], ctx.volume[cols], ctx.benchmark, ctx.cash_ret,
                        min_adv=ctx.min_adv, adv_window=ctx.adv_window, min_history=ctx.min_history,
                        min_price=ctx.min_price, capital=ctx.capital, cash_rate=ctx.cash_rate,
                        cash_withholding=ctx.cash_withholding, usdtry=ctx.usdtry,
                        high=ctx.high[cols] if ctx.has_hl else None, low=ctx.low[cols] if ctx.has_hl else None,
                        semantics=ctx.semantics)


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
        kw = {}
        if "price_limit_flag" in ev.columns and getattr(cost_model, "supports_price_limit_flags", False):
            kw["price_limit_flags"] = ev["price_limit_flag"].to_numpy(bool)
        cf = -np.asarray(cost_model.apply_costs(np.zeros(len(ev)), ev["price"].to_numpy(float),
                                                ev["order_value"].to_numpy(float),
                                                ev["bar_value_try"].to_numpy(float), **kw), dtype=float)
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
            P = CLf[e:x + 1][:, j].copy()
            if "exit_price" in g.columns:  # realised exit (deferred / carried exits are booked at t1 at the real price)
                xpx = g["exit_price"].to_numpy(float)
                P[-1] = np.where(np.isfinite(xpx), xpx, P[-1])
            rel = ((P / OP[e, j]) * w).sum(axis=1) + (1.0 - W) * np.cumprod(1.0 + cash[e:x + 1])
            rel[-1] -= float((w * g["cost_frac"].to_numpy(float)).sum())
            prev = np.concatenate([[1.0], rel[:-1]])
            ret[e:x + 1] = rel / prev - 1.0
            hold_n[e:x + 1] = len(g)
            invested[e:x + 1] = W
    ret = np.nan_to_num(ret, nan=0.0)
    return pd.DataFrame({"ret": ret, "nav": np.cumprod(1.0 + ret), "holdings": hold_n,
                         "invested_frac": invested}, index=idx)
