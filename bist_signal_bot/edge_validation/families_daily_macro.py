"""Macro / relative-strength / calendar daily families (self-registering). Research only; no real order is sent.

All scores use data <= their row date. Calendar masks use only the (known-in-advance) BIST calendar
(``intraday/sessions.py`` + ``bist_holidays.json``; weekends + fixed holidays + JSON list; religious holidays are
UNVERIFIED, confirm with Borsa Istanbul), never prices. Every grid combination is one ledger trial: grids are
deliberately tiny.

Honest data notes
  * Sector master data does NOT exist locally (``data/universe`` has no sector field; ``InstrumentRecord.sector`` is
    never populated). ``xs_rel_strength_sector`` therefore uses a DATA-DRIVEN PROXY: monthly-refreshed
    return-correlation clusters (market factor removed), not real sectors.
  * No interest-rate (TCMB policy rate) series exists locally; none is invented here.
  * ``DailyContext.from_archive`` carries USDTRY (``ctx.usdtry``, truncated together with the context); manual
    ``attach_usdtry(ctx, s)`` / ``FX_SENSITIVITY.set_usdtry(s)`` still work as overrides. Without any series ``xs_fx_sensitivity`` raises
    (the runner records a failed trial) instead of guessing.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.families_daily import register_family
from bist_signal_bot.edge_validation.xsection import DailyContext


# ------------------------------------------------------------------ helpers
def _ret(ctx: DailyContext, l: int) -> pd.DataFrame:
    return ctx.close / ctx.close.shift(int(l)) - 1.0


def _tiebreak(ctx: DailyContext, how: str) -> pd.DataFrame:
    """Neutral ranking score used by calendar-timing families (timing is the hypothesis, not stock picking)."""
    if how == "liquidity":  # most liquid names: lowest cost; log ADV(20d)
        return np.log(ctx.adv.where(ctx.adv > 0))
    if how == "momentum":  # 60d return
        return _ret(ctx, 60)
    raise ValueError("tiebreak must be 'liquidity' or 'momentum'")


def attach_usdtry(ctx: DailyContext, usdtry: pd.Series) -> DailyContext:
    ctx.usdtry = DailyContext._align_series(usdtry, ctx.index)
    return ctx


def load_usdtry(archive) -> pd.Series:
    from bist_signal_bot.daily.panel import load_benchmark
    df = load_benchmark(archive, "USDTRY")
    return df["close"] if len(df) else pd.Series(dtype=float)


def _calendar_days(ctx: DailyContext):
    """Calendar trading days (weekday & not holiday) covering the context span +/- 45 days (deterministic)."""
    from bist_signal_bot.intraday.sessions import is_trading_day
    lo, hi = ctx.index[0].date() - timedelta(days=45), ctx.index[-1].date() + timedelta(days=45)
    out, d = [], lo
    while d <= hi:
        if is_trading_day(d):
            out.append(d)
        d += timedelta(days=1)
    return out


def _mask_from_dates(ctx: DailyContext, dates) -> pd.Series:
    s = set(pd.Timestamp(d) for d in dates)
    return pd.Series([t in s for t in ctx.index], index=ctx.index, dtype=bool)


# ------------------------------------------------------------------ relative strength
class XSRelStrengthIndex:
    """Relative strength vs XU100: stock l-day return minus beta * index l-day return (beta = rolling 120d).

    Hypothesis: stocks outperforming the index continue to (RS momentum; Levy 1967; Jegadeesh-Titman 1993
    on residual/industry-adjusted variants, Moskowitz-Grinblatt 1999). NOTE: with ``adjust='none'`` the score is
    ``ret - index_ret`` where the subtracted term is identical for all stocks on a date, so the cross-sectional
    RANK equals plain ``xs_momentum(skip=0)`` (a duplicate trial, only available explicitly). The default grid uses
    the beta-adjusted residual, which is not a pure rank duplicate. Needs ``ctx.benchmark`` (XU100); else raises.
    """
    name = "xs_rel_strength_index"
    default_grid = {"lookback": [20, 60, 120], "adjust": ["beta"]}

    def valid(self, params: dict) -> bool:
        return int(params.get("lookback", 0)) >= 2 and params.get("adjust", "beta") in ("beta", "none")

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        if ctx.benchmark is None:
            raise ValueError("xs_rel_strength_index needs the XU100 benchmark in the context")
        l, adj = int(params["lookback"]), params.get("adjust", "beta")
        if not self.valid({"lookback": l, "adjust": adj}):
            raise ValueError("bad params")
        b = ctx.benchmark.ffill()
        bl = b / b.shift(l) - 1.0
        rl = _ret(ctx, l)
        if adj == "none":
            return rl.sub(bl, axis=0)
        w = 120
        r = ctx.close.pct_change(fill_method=None)
        rb = b.pct_change(fill_method=None)
        beta = r.rolling(w, min_periods=int(w * 0.8)).cov(rb).div(rb.rolling(w, min_periods=int(w * 0.8)).var(), axis=0)
        return rl - beta.mul(bl, axis=0)


class XSRelStrengthSector:
    """Return relative to the mean of its (proxy) peer cluster over l days.

    NO real sector data exists locally, so peers are DATA-DRIVEN: every first session of a calendar month, symbols
    are clustered (average-linkage, distance sqrt(.5(1-corr))) on the past ``corr_window`` days of market-demeaned
    daily returns using data strictly before that session; labels are held until the next refresh (causal). Symbols
    with < 60% valid history in the window get no cluster (score NaN). Hypothesis: industry momentum / lead-lag
    (Moskowitz-Grinblatt 1999); here a statistical-peer proxy, not an economic sector. ``n_clusters`` is fixed at
    8 in the default grid to keep the trial count honest.
    """
    name = "xs_rel_strength_sector"
    default_grid = {"lookback": [20, 60, 120], "n_clusters": [8], "corr_window": [250]}

    def valid(self, params: dict) -> bool:
        return (int(params.get("lookback", 0)) >= 2 and int(params.get("n_clusters", 0)) >= 2
                and int(params.get("corr_window", 0)) >= 60)

    def clusters(self, ctx: DailyContext, k: int, win: int) -> pd.DataFrame:
        """DataFrame(date x symbol) of float cluster ids (NaN = unassigned); row t uses data < refresh row only.
        Cached per context object (a truncated context is a new object, so no stale/future data is reused)."""
        cache = ctx.__dict__.setdefault("_cluster_cache", {})
        if (k, win) not in cache:
            cache[(k, win)] = self._clusters(ctx, k, win)
        return cache[(k, win)].copy()

    @staticmethod
    def peer_mean(R: np.ndarray, L: np.ndarray) -> np.ndarray:
        """Per row: mean of R over each cluster (finite R only); NaN where label or R is NaN. Vectorised over rows."""
        P = np.full(R.shape, np.nan)
        fin = np.isfinite(R)
        Rz = np.where(fin, R, 0.0)
        for c in np.unique(L[np.isfinite(L)]):
            m = L == c
            ok = m & fin
            cnt = ok.sum(axis=1)
            tot = np.where(ok, Rz, 0.0).sum(axis=1)
            with np.errstate(invalid="ignore", divide="ignore"):
                mean = np.where(cnt > 0, tot / np.maximum(cnt, 1), np.nan)
            P = np.where(ok, mean[:, None], P)
        return P

    def _clusters(self, ctx: DailyContext, k: int, win: int) -> pd.DataFrame:
        from scipy.cluster.hierarchy import fcluster, linkage
        from scipy.spatial.distance import squareform
        r = ctx.close.pct_change(fill_method=None)
        r = r.sub(r.mean(axis=1), axis=0)
        n = len(ctx.index)
        months = ctx.index.to_period("M")
        out = np.full((n, len(ctx.symbols)), np.nan)
        cur = None
        for i in range(n):
            if i > 0 and months[i] != months[i - 1] and i >= win // 2:
                w = r.iloc[max(0, i - win):i]  # strictly before the refresh session
                ok = w.notna().sum() >= 0.6 * win
                cols = np.flatnonzero(ok.to_numpy())
                lab = np.full(len(ctx.symbols), np.nan)
                if len(cols) > k:
                    c = w.iloc[:, cols].corr(min_periods=int(0.5 * win)).fillna(0.0).to_numpy(copy=True)
                    np.fill_diagonal(c, 1.0)
                    d = np.sqrt(np.clip(0.5 * (1.0 - c), 0.0, None))
                    d = (d + d.T) / 2.0
                    np.fill_diagonal(d, 0.0)
                    z = linkage(squareform(d, checks=False), method="average")
                    lab[cols] = fcluster(z, t=k, criterion="maxclust")
                cur = lab
            if cur is not None:
                out[i] = cur
        return pd.DataFrame(out, index=ctx.index, columns=ctx.symbols)

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        l, k, win = int(params["lookback"]), int(params.get("n_clusters", 8)), int(params.get("corr_window", 250))
        if not self.valid({"lookback": l, "n_clusters": k, "corr_window": win}):
            raise ValueError("bad params")
        rl = _ret(ctx, l)
        lab = self.clusters(ctx, k, win)
        P = self.peer_mean(rl.to_numpy(float), lab.to_numpy(float))
        peer = pd.DataFrame(P, index=rl.index, columns=rl.columns)
        return rl - peer


# ------------------------------------------------------------------ macro: FX sensitivity
class XSFxSensitivity:
    """Rolling beta of each stock to USDTRY returns, signed by the USDTRY regime.

    Hypothesis: when TRY depreciates fast (20d USDTRY return > thr x its 120d-vol-scaled move), FX earners
    (high positive FX beta; exporters) re-rate in nominal TRY terms; when the lira is stable/appreciating, low-beta
    (domestic / FX-debtor-light) names are favoured. Score = sign * beta, sign = +1 if z > thr else -1, where
    z = USDTRY 20d return / (daily vol over 120d * sqrt(20)). Literature: exchange-rate exposure of firms
    (Jorion 1990; Dumas-Solnik 1995); EM currency-crisis equity reactions. Beta windows 120/250d, causal.
    Contemporaneous betas can be biased by quote-time asynchrony of the Yahoo USDTRY series. Interest-rate
    sensitivity is NOT implemented: there is no local TCMB policy-rate series and none is fabricated.
    """
    name = "xs_fx_sensitivity"
    default_grid = {"beta_window": [120, 250], "thr": [0.5, 1.0]}

    def __init__(self):
        self.usdtry: Optional[pd.Series] = None

    def set_usdtry(self, s: Optional[pd.Series]) -> None:
        self.usdtry = s

    def valid(self, params: dict) -> bool:
        return int(params.get("beta_window", 0)) >= 30 and float(params.get("thr", 0)) >= 0

    def _fx(self, ctx: DailyContext) -> pd.Series:
        s = getattr(ctx, "usdtry", None)
        if s is None:
            s = self.usdtry
        if s is None or len(s) == 0:
            raise ValueError("USDTRY series not available (use attach_usdtry / set_usdtry / load_usdtry)")
        s = s.astype(float).sort_index()
        return s.reindex(s.index.union(ctx.index)).ffill().reindex(ctx.index)

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        w, thr = int(params["beta_window"]), float(params.get("thr", 1.0))
        if not self.valid({"beta_window": w, "thr": thr}):
            raise ValueError("bad params")
        fx = self._fx(ctx)
        rf = fx.pct_change(fill_method=None)
        r = ctx.close.pct_change(fill_method=None)
        mp = int(w * 0.8)
        beta = r.rolling(w, min_periods=mp).cov(rf).div(rf.rolling(w, min_periods=mp).var(), axis=0)
        z = (fx / fx.shift(20) - 1.0) / (rf.rolling(120, min_periods=96).std() * np.sqrt(20))
        sign = pd.Series(np.where(z.isna(), np.nan, np.where(z > thr, 1.0, -1.0)), index=ctx.index)
        return beta.mul(sign, axis=0)


FX_SENSITIVITY = XSFxSensitivity()


# ------------------------------------------------------------------ calendar timing families
class _CalendarFamily:
    """Calendar timing: ``rebalance_mask`` marks decision dates (close of t0); other days = cash. The holding
    horizon comes from the runner (``horizons``): use 5 for turn-of-month (2 last + 3 first sessions)."""
    name = ""
    default_grid: dict = {}

    def valid(self, params: dict) -> bool:
        return params.get("tiebreak", "liquidity") in ("liquidity", "momentum")

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        return _tiebreak(ctx, params.get("tiebreak", "liquidity"))

    def decision_dates(self, ctx: DailyContext, params: dict):
        raise NotImplementedError

    def rebalance_mask(self, ctx: DailyContext, params: dict) -> pd.Series:
        return _mask_from_dates(ctx, self.decision_dates(ctx, params))


class CalTurnOfMonth(_CalendarFamily):
    """Turn-of-month effect: be long from the open of the 2nd-last trading day of a month (decision at the close of
    the 3rd-last) and, with horizon 5, through the 3rd session of the next month. Literature: Ariel 1987, Lakonishok &
    Smidt 1988, McConnell & Xu 2008 (strong in many markets); liquidity/pension-flow explanations. Score is a neutral
    tie-break (liquidity or 60d momentum), so the test is the timing."""
    name = "cal_turn_of_month"
    default_grid = {"tiebreak": ["liquidity", "momentum"]}

    def decision_dates(self, ctx, params):
        days = _calendar_days(ctx)
        by_month: dict = {}
        for d in days:
            by_month.setdefault((d.year, d.month), []).append(d)
        return [v[-3] for v in by_month.values() if len(v) >= 3]


class CalPreHoliday(_CalendarFamily):
    """Pre-holiday effect: decision at the close of the session before the last session preceding a BIST holiday
    (so entry = open of the pre-holiday session; horizon 1 captures that session, >=2 also the holiday gap).
    Literature: Ariel 1990, Lakonishok & Smidt 1988, Kim & Park 1994 (abnormal pre-holiday returns). Holiday list is
    calendar-only (religious holidays unverified; confirm with Borsa Istanbul)."""
    name = "cal_pre_holiday"
    default_grid = {"tiebreak": ["liquidity", "momentum"]}

    def decision_dates(self, ctx, params):
        from bist_signal_bot.intraday.sessions import is_holiday
        days = _calendar_days(ctx)
        out = []
        for a, n1 in zip(days[:-1], days[1:]):  # a = decision date, n1 = next session (pre-holiday candidate)
            d = n1 + timedelta(days=1)
            while d.weekday() >= 5:
                d += timedelta(days=1)
            if is_holiday(d):
                out.append(a)
        return out


class CalMonthEndReversal:
    """Month-end reversal: decision at the close of the last trading day of the month; buy the prior-l-day losers
    (score = -l-day return), held from the next open. Literature: short-term reversal (Jegadeesh 1990; Lehmann 1990)
    concentrated around month turns by flow/window-dressing effects (Haugen & Lakonishok 1988). Timing via mask."""
    name = "cal_month_end_reversal"
    default_grid = {"lookback": [5, 10, 21]}

    def valid(self, params: dict) -> bool:
        return int(params.get("lookback", 0)) >= 2

    def score(self, ctx: DailyContext, params: dict) -> pd.DataFrame:
        if not self.valid(params):
            raise ValueError("bad params")
        return -_ret(ctx, int(params["lookback"]))

    def rebalance_mask(self, ctx: DailyContext, params: dict) -> pd.Series:
        by_month: dict = {}
        for d in _calendar_days(ctx):
            by_month.setdefault((d.year, d.month), []).append(d)
        return _mask_from_dates(ctx, [v[-1] for v in by_month.values()])


for _f in (XSRelStrengthIndex(), XSRelStrengthSector(), FX_SENSITIVITY, CalTurnOfMonth(), CalPreHoliday(),
           CalMonthEndReversal()):
    register_family(_f, overwrite=True)
