"""CandidateGate: multi-criteria statistical gate. Research only; never an order path."""
from __future__ import annotations

import json
import math
from datetime import datetime
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from bist_signal_bot.edge_validation import stats as st
from bist_signal_bot.edge_validation.costs import IntradayCostModel
from bist_signal_bot.edge_validation.cv import CombinatorialPurgedCV, assert_no_leakage

DISCLAIMER = "Aday, kazanç garantisi değildir; yalnız ölçülmüş kanıt. No real order sent."
TZ = "Europe/Istanbul"
ANN = 252.0


class GateConfig(BaseModel):
    min_events: int = 300
    min_active_days: int = 60
    dsr_min: float = 0.95
    pbo_max: float = 0.25
    fdr_alpha: float = 0.05
    reality_check_alpha: float = 0.05
    min_positive_path_fraction: float = 0.7
    ci_alpha: float = 0.05
    embargo_days: int = 1
    cpcv_groups: int = 6
    cpcv_test_groups: int = 2
    pbo_blocks: int = 16
    n_boot: int = 1000
    seed: int = 0

    @classmethod
    def from_settings(cls, settings=None) -> "GateConfig":
        if settings is None:
            from bist_signal_bot.config.settings import get_settings
            settings = get_settings()
        g = lambda k: getattr(settings, "EDGE_GATE_" + k)  # noqa: E731
        return cls(min_events=int(g("MIN_EVENTS")), min_active_days=int(g("MIN_ACTIVE_DAYS")),
                   dsr_min=float(g("DSR_MIN")), pbo_max=float(g("PBO_MAX")),
                   fdr_alpha=float(g("FDR_ALPHA")),
                   reality_check_alpha=float(g("REALITY_CHECK_ALPHA")),
                   min_positive_path_fraction=float(g("MIN_POSITIVE_PATH_FRACTION")),
                   ci_alpha=float(g("CI_ALPHA")), embargo_days=int(g("EMBARGO_DAYS")))


class GateReport(BaseModel):
    family: str
    selected_trial_id: Optional[str] = None
    interval: str = ""
    verdict: str = "INSUFFICIENT_DATA"  # CANDIDATE | REJECTED | INSUFFICIENT_DATA
    failed_criteria: List[str] = Field(default_factory=list)
    n_events: int = 0
    n_events_disallowed: int = 0
    active_days: int = 0
    grid_days: int = 0
    gross_mean_daily: Optional[float] = None
    net_mean_daily: Optional[float] = None
    gross_sharpe_period: Optional[float] = None
    net_sharpe_period: Optional[float] = None
    gross_sharpe_annual: Optional[float] = None
    net_sharpe_annual: Optional[float] = None
    net_mean_event_bps: Optional[float] = None
    n_trials_ledger: int = 0
    trial_sharpe_variance: Optional[float] = None
    expected_max_sharpe: Optional[float] = None
    dsr: Optional[float] = None
    pbo: Optional[float] = None
    n_trials_evaluated: int = 0
    selected_p_value: Optional[float] = None
    selected_p_bh: Optional[float] = None
    reality_check_p: Optional[float] = None
    ci_mean_daily_net: Optional[List[Optional[float]]] = None
    n_paths: int = 0
    path_sharpes: List[Optional[float]] = Field(default_factory=list)
    positive_path_fraction: Optional[float] = None
    path_sharpe_mean: Optional[float] = None
    path_sharpe_std: Optional[float] = None
    leakage_splits_checked: int = 0
    thresholds: dict = Field(default_factory=dict)
    notes: List[str] = Field(default_factory=list)
    report_path: Optional[str] = None
    disclaimer: str = DISCLAIMER


def _f(x) -> Optional[float]:
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _day(ts) -> pd.DatetimeIndex:
    idx = pd.DatetimeIndex(ts)
    idx = idx.tz_localize(TZ) if idx.tz is None else idx.tz_convert(TZ)
    return idx.normalize()


def daily_series(events: pd.DataFrame, col: str, grid: pd.DatetimeIndex) -> pd.Series:
    """Mean per-event return realised each day (by t1), zero on idle days."""
    if events is None or len(events) == 0:
        return pd.Series(0.0, index=grid)
    s = pd.Series(events[col].to_numpy(float), index=_day(events["t1"]))
    return s.groupby(level=0).mean().reindex(grid).fillna(0.0)


def _sr(x) -> float:
    return st.sharpe(np.asarray(x, dtype=float))


class CandidateGate:
    def __init__(self, config: Optional[GateConfig] = None, settings=None,
                 cost_model: Optional[IntradayCostModel] = None, save: bool = True):
        self.config = config or GateConfig()
        self.settings = settings
        self._cost_model = cost_model
        self.save = save

    @property
    def cost_model(self) -> IntradayCostModel:
        if self._cost_model is None:
            self._cost_model = IntradayCostModel.from_settings(self.settings)
        return self._cost_model

    # ------------------------------------------------------------------ helpers
    def _net(self, ev: pd.DataFrame) -> pd.DataFrame:
        if ev is None or len(ev) == 0:
            return pd.DataFrame(columns=["t0", "t1", "symbol", "gross_ret", "net_ret"])
        ev = ev.copy().reset_index(drop=True)
        kw = {}  # daily events may carry price_limit_flag (entry unfillable at a price limit) -> cost NaN -> excluded
        if "price_limit_flag" in ev.columns and getattr(self.cost_model, "supports_price_limit_flags", False):
            kw["price_limit_flags"] = ev["price_limit_flag"].to_numpy(bool)
        ev["net_ret"] = self.cost_model.apply_costs(
            ev["gross_ret"].to_numpy(float), ev["price"].to_numpy(float),
            ev["order_value"].to_numpy(float), ev["bar_value_try"].to_numpy(float), **kw)
        return ev

    def _cpcv(self, pool: pd.DataFrame, trial_ids: Sequence[str], grid: pd.DatetimeIndex, rep: GateReport):
        c = self.config
        cv = CombinatorialPurgedCV(c.cpcv_groups, c.cpcv_test_groups, embargo=pd.Timedelta(days=c.embargo_days))
        t0, t1 = pool["t0"], pool["t1"]
        groups = cv.group_indices(t0)
        tid = pool["trial_id"].to_numpy()
        group_days = []
        for g in groups:
            d = _day(pool["t0"].iloc[g])
            group_days.append((d.min(), d.max()))
        preds = []
        for train, test, combo in cv.split(t0, t1):
            assert_no_leakage(train, test, t0, t1, embargo=pd.Timedelta(days=c.embargo_days))
            rep.leakage_splits_checked += 1
            tr = pool.iloc[train]
            best, best_sr = None, -np.inf
            for k in trial_ids:
                e = tr[tr["trial_id"] == k]
                if len(e) < 5:
                    continue
                d = daily_series(e, "net_ret", grid)
                d = d[d.index.isin(_day(e["t1"]))]  # active days only for selection
                s = _sr(d)
                if np.isfinite(s) and s > best_sr:
                    best, best_sr = k, s
            test_set = set(test.tolist())
            entry = {}
            for g in combo:
                idx = np.array([i for i in groups[g] if i in test_set and tid[i] == best], dtype=int)
                entry[g] = pool.iloc[idx][["t1", "net_ret"]] if best is not None else pool.iloc[[]][["t1", "net_ret"]]
            preds.append(entry)
        out = []
        for path in cv.assemble_paths(preds):
            frames = [path[g] for g in sorted(path)]
            ev = pd.concat(frames) if frames else pd.DataFrame(columns=["t1", "net_ret"])
            days = []
            for g in path:
                a, b = group_days[g]
                days.append(grid[(grid >= a) & (grid <= b)])
            pgrid = days[0]
            for d in days[1:]:
                pgrid = pgrid.union(d)
            if len(ev) == 0 or len(pgrid) < 3:
                out.append(float("nan"))
                continue
            out.append(_sr(daily_series(ev, "net_ret", pgrid)))
        return out

    # ------------------------------------------------------------------ main
    def evaluate(self, family: str, selected_trial_id: Optional[str],
                 events_by_trial: Dict[str, pd.DataFrame], ledger, interval: str = "",
                 trading_days: Optional[Sequence] = None) -> GateReport:
        c = self.config
        rep = GateReport(family=family, selected_trial_id=selected_trial_id, interval=str(interval),
                         thresholds=c.model_dump())
        nets: Dict[str, pd.DataFrame] = {}
        disallowed = 0
        for k, ev in (events_by_trial or {}).items():
            full = self._net(ev)
            ok = full.dropna(subset=["net_ret"]) if len(full) else full
            if k == selected_trial_id:
                disallowed = len(full) - len(ok)
            nets[k] = ok
        sel = nets.get(selected_trial_id)
        rep.n_events_disallowed = int(disallowed)
        rep.n_trials_ledger = int(ledger.n_trials(family)) if ledger is not None else 0
        if sel is None or len(sel) == 0:
            rep.notes.append("no events for selected trial")
            rep.failed_criteria = ["min_events"]
            return self._finish(rep)

        if trading_days is not None:
            grid = _day(pd.DatetimeIndex(trading_days)).unique().sort_values()
        else:
            grid = pd.DatetimeIndex(sorted(set().union(*[set(_day(e["t1"])) for e in nets.values() if len(e)])))
        rep.grid_days = len(grid)
        rep.n_events = len(sel)
        rep.active_days = int(_day(sel["t1"]).nunique())
        g_daily = daily_series(sel, "gross_ret", grid)
        n_daily = daily_series(sel, "net_ret", grid)
        rep.gross_mean_daily, rep.net_mean_daily = _f(g_daily.mean()), _f(n_daily.mean())
        rep.gross_sharpe_period, rep.net_sharpe_period = _f(_sr(g_daily)), _f(_sr(n_daily))
        rep.gross_sharpe_annual = _f(_sr(g_daily) * math.sqrt(ANN))
        rep.net_sharpe_annual = _f(_sr(n_daily) * math.sqrt(ANN))
        rep.net_mean_event_bps = _f(sel["net_ret"].mean() * 1e4)

        failed: List[str] = []
        if rep.n_events < c.min_events:
            failed.append("min_events")
        if rep.active_days < c.min_active_days:
            failed.append("min_active_days")
        if failed:
            rep.failed_criteria = failed
            rep.notes.append("insufficient data: statistics not evaluated")
            return self._finish(rep)

        # DSR
        n_tr = max(rep.n_trials_ledger, len(nets), 1)
        var = ledger.trial_sharpe_variance(family) if ledger is not None else float("nan")
        trial_daily = {k: daily_series(e, "net_ret", grid) for k, e in nets.items() if len(e)}
        if not np.isfinite(var):
            local = np.array([_sr(v) for v in trial_daily.values()], dtype=float)
            local = local[np.isfinite(local)]
            var = float(np.var(local, ddof=1)) if local.size >= 2 else float("nan")
            rep.notes.append("trial Sharpe variance from current run (ledger had <2 Sharpes)")
        if not np.isfinite(var) and n_tr <= 1:
            var = 0.0
        rep.n_trials_ledger = n_tr if rep.n_trials_ledger == 0 else rep.n_trials_ledger
        rep.trial_sharpe_variance = _f(var)
        rep.expected_max_sharpe = _f(st.expected_max_sharpe(n_tr, var))
        rep.dsr = _f(st.deflated_sharpe_ratio(n_daily.to_numpy(), n_tr, var))
        if rep.dsr is None or rep.dsr < c.dsr_min:
            failed.append("dsr")

        # PBO (CSCV on the family's daily matrix)
        rep.n_trials_evaluated = len(trial_daily)
        M = pd.DataFrame(trial_daily).to_numpy(float) if trial_daily else np.zeros((0, 0))
        pbo = float("nan")
        if M.ndim == 2 and M.shape[1] >= 2 and M.shape[0] >= 2 * c.pbo_blocks:
            pbo = st.probability_of_backtest_overfitting(M, n_blocks=c.pbo_blocks)["pbo"]
        else:
            rep.notes.append("PBO undefined (need >=2 trials and enough days)")
        rep.pbo = _f(pbo)
        if rep.pbo is None or rep.pbo > c.pbo_max:
            failed.append("pbo")

        # FDR across all family trials
        keys = list(trial_daily)
        pv = np.array([st.sharpe_pvalue(trial_daily[k].to_numpy()) for k in keys], dtype=float)
        pv = np.where(np.isfinite(pv), pv, 1.0)
        adj, _ = st.benjamini_hochberg(pv, c.fdr_alpha)
        if selected_trial_id in keys:
            i = keys.index(selected_trial_id)
            rep.selected_p_value, rep.selected_p_bh = _f(pv[i]), _f(adj[i])
        if rep.selected_p_bh is None or rep.selected_p_bh > c.fdr_alpha:
            failed.append("fdr_bh")

        # White reality check over all trials vs zero
        rc = st.white_reality_check(M, n_boot=c.n_boot, seed=c.seed) if M.size else float("nan")
        rep.reality_check_p = _f(rc)
        if rep.reality_check_p is None or rep.reality_check_p > c.reality_check_alpha:
            failed.append("reality_check")

        # Block-bootstrap CI of the mean daily net return
        lo, hi = st.block_bootstrap_ci(n_daily.to_numpy(), alpha=c.ci_alpha, seed=c.seed)
        rep.ci_mean_daily_net = [_f(lo), _f(hi)]
        if rep.ci_mean_daily_net[0] is None or rep.ci_mean_daily_net[0] <= 0:
            failed.append("ci_lower_positive")

        # CPCV over pooled events (selection inside each train fold; evaluation on OOS groups)
        pool = pd.concat([e.assign(trial_id=k) for k, e in nets.items() if len(e)], ignore_index=True)
        pool = pool.sort_values("t0", kind="stable").reset_index(drop=True)
        paths: List[float] = []
        if len(pool) >= c.cpcv_groups:
            paths = self._cpcv(pool, list(trial_daily), grid, rep)
        rep.n_paths = len(paths)
        rep.path_sharpes = [_f(p) for p in paths]
        arr = np.array(paths, dtype=float)
        if arr.size:
            rep.positive_path_fraction = _f(float(np.mean(np.where(np.isfinite(arr), arr, -1.0) > 0)))
            fin = arr[np.isfinite(arr)]
            rep.path_sharpe_mean = _f(fin.mean()) if fin.size else None
            rep.path_sharpe_std = _f(fin.std(ddof=1)) if fin.size > 1 else None
        if rep.positive_path_fraction is None or rep.positive_path_fraction < c.min_positive_path_fraction:
            failed.append("positive_paths")

        rep.failed_criteria = failed
        return self._finish(rep)

    def _finish(self, rep: GateReport) -> GateReport:
        c = self.config
        if rep.failed_criteria and set(rep.failed_criteria) <= {"min_events", "min_active_days"}:
            rep.verdict = "INSUFFICIENT_DATA"
        elif rep.failed_criteria:
            rep.verdict = "REJECTED"
        else:
            rep.verdict = "CANDIDATE"
        if self.save:
            rep.report_path = str(self.save_report(rep))
            _write_json(rep)
        return rep

    def save_report(self, rep: GateReport):
        from bist_signal_bot.storage.paths import get_edge_validation_dir
        d = get_edge_validation_dir(self.settings) / "reports"
        d.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        return d / f"{rep.family}_{ts}.json"


def _write_json(rep: GateReport) -> None:
    """Write the report JSON to rep.report_path (path is part of the saved JSON)."""
    with open(rep.report_path, "w", encoding="utf-8") as fh:
        json.dump(rep.model_dump(mode="json"), fh, ensure_ascii=False, indent=2)
