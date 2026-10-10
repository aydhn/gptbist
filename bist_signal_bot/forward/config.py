"""Forward shadow config, paths and the FROZEN portfolio set. Simulation only; no real order is ever sent."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from bist_signal_bot.forward import NO_ORDER

SCENARIOS = ("zero_commission", "placeholder_commission")
PRIMARY = "placeholder_commission"
LEDGER_FAMILY_SUFFIX = "_daily_xs_ew"  # excess-over-EW trials (primary candidacy stream)
SELECTION_RULE = ("per registered daily family and horizon: the ledger trial (family <fam>_daily_xs_ew, "
                  "no regime scaling, status ok) with the highest in-sample net excess Sharpe; frozen at "
                  "registration time and never re-optimised")

DECISION_RULE = (
    "A portfolio gets a verdict only after >= {min_days} live trading days AND >= {min_cal} calendar days since its "
    "first decision (otherwise INSUFFICIENT). PASS iff ALL hold under the placeholder_commission scenario: "
    "(1) cumulative excess return over the equal-weight universe benchmark > 0; (2) NAV alpha over cash > 0; "
    "(3) Newey-West (overlap-aware) t-stat of the mean daily excess over EW >= max({min_t}, z(1-0.05/K)) with K = "
    "number of frozen portfolios (Bonferroni); (4) >= {min_baskets} closed baskets and basket-level hit-rate vs EW "
    ">= 50%; (5) max drawdown < {max_dd:.0%}. Otherwise FAIL. Parameters are never retuned; any change starts a "
    "new forward directory with a new plan.")


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _get(settings, key, default):
    if settings is None:
        return default
    try:
        v = getattr(settings, key)
    except AttributeError:
        return default
    return default if v is None else v


@dataclass
class ForwardConfig:
    settings: object
    forward_dir: Path
    archive_path: Optional[Path] = None
    ledger_path: Optional[Path] = None

    @classmethod
    def from_settings(cls, settings=None, forward_dir=None, archive_path=None, ledger_path=None) -> "ForwardConfig":
        if settings is None:
            from bist_signal_bot.config.settings import get_settings
            settings = get_settings()
        from bist_signal_bot.storage.paths import get_data_dir
        fd = Path(forward_dir) if forward_dir else get_data_dir(settings) / "forward"
        return cls(settings, fd, Path(archive_path) if archive_path else None,
                   Path(ledger_path) if ledger_path else None)

    def ensure(self) -> None:
        for d in (self.forward_dir, self.nav_dir, self.health_dir, self.reports_dir):
            d.mkdir(parents=True, exist_ok=True)

    # ---- paths ----
    decisions_path = property(lambda s: s.forward_dir / "decisions.jsonl")
    outcomes_path = property(lambda s: s.forward_dir / "outcomes.jsonl")
    portfolios_path = property(lambda s: s.forward_dir / "portfolios.json")
    runs_path = property(lambda s: s.forward_dir / "runs.jsonl")
    alerts_path = property(lambda s: s.forward_dir / "alerts.jsonl")
    heartbeat_path = property(lambda s: s.forward_dir / "heartbeats.jsonl")
    state_path = property(lambda s: s.forward_dir / "state.json")
    lock_path = property(lambda s: s.forward_dir / ".run.lock")
    nav_dir = property(lambda s: s.forward_dir / "nav")
    health_dir = property(lambda s: s.forward_dir / "health")
    reports_dir = property(lambda s: s.forward_dir / "reports")

    # ---- typed settings ----
    def f(self, key, default) -> float:
        return float(_get(self.settings, key, default))

    def i(self, key, default) -> int:
        return int(_get(self.settings, key, default))

    def s(self, key, default) -> str:
        return str(_get(self.settings, key, default))

    @property
    def data_dir(self) -> Path:
        from bist_signal_bot.storage.paths import get_data_dir
        return get_data_dir(self.settings)

    def resolve_ledger_path(self) -> Path:
        if self.ledger_path:
            return self.ledger_path
        from bist_signal_bot.edge_validation.ledger import default_ledger_path
        return default_ledger_path(self.settings)

    def plan(self) -> dict:
        p = dict(min_days=self.i("FORWARD_MIN_LIVE_DAYS", 60), min_cal=self.i("FORWARD_MIN_CALENDAR_DAYS", 90),
                 min_t=self.f("FORWARD_MIN_TSTAT", 2.0), min_baskets=self.i("FORWARD_MIN_BASKETS", 6),
                 max_dd=self.f("FORWARD_MAX_DD_PASS", 0.20))
        return {"planned_min_window_calendar_days": p["min_cal"], "min_live_trading_days": p["min_days"],
                "min_tstat": p["min_t"], "min_baskets": p["min_baskets"], "max_drawdown_pass": p["max_dd"],
                "decision_rule": DECISION_RULE.format(**p), "primary_scenario": PRIMARY,
                "benchmarks": ["ew_universe", "xu100", "cash"], "never_retune": True,
                "doc": "docs/runbooks/forward_paper_plan.md"}


def _params_hash(params: dict) -> str:
    return hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:8]


def portfolio_id(family: str, params: dict, horizon: int, top_n: int) -> str:
    return f"{family}__h{int(horizon)}__top{int(top_n)}__{_params_hash(params)}"


def _content_hash(doc: dict) -> str:
    body = {k: v for k, v in doc.items() if k != "content_hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def select_from_ledger(ledger_path, families, horizons, default_top_n: int = 8) -> list:
    """Best (highest ledger net excess Sharpe) trial per (family, horizon). Read-only SQLite access."""
    out = []
    con = sqlite3.connect(f"file:{Path(ledger_path).as_posix()}?mode=ro", uri=True)
    try:
        for fam in sorted(families):
            rows = con.execute("SELECT trial_id, params_json, universe, sharpe FROM trials WHERE strategy_family=? "
                               "AND status='ok' AND sharpe IS NOT NULL", (fam + LEDGER_FAMILY_SUFFIX,)).fetchall()
            best: dict = {}
            for tid, pj, uni, sh in rows:
                m = re.search(r"\|h(\d+)\|top(\d+)\|nors$", uni or "")
                if not m or int(m.group(1)) not in horizons:
                    continue
                h, top = int(m.group(1)), int(m.group(2))
                if h not in best or (sh, tid) > (best[h][0], best[h][1]):
                    best[h] = (sh, tid, json.loads(pj or "{}"), top)
            for h in sorted(best):
                sh, tid, params, top = best[h]
                out.append({"id": portfolio_id(fam, params, h, top), "family": fam, "params": params,
                            "horizon": h, "top_n": top or default_top_n, "ledger_sharpe": float(sh),
                            "ledger_trial_id": tid})
    finally:
        con.close()
    return out


def parse_portfolios_setting(raw, default_top_n: int) -> list:
    if raw in (None, "", []):
        return []
    lst = json.loads(raw) if isinstance(raw, str) else list(raw)
    out = []
    for p in lst:
        params, h = dict(p.get("params") or {}), int(p["horizon"])
        top = int(p.get("top_n") or default_top_n)
        out.append({"id": portfolio_id(p["family"], params, h, top), "family": p["family"], "params": params,
                    "horizon": h, "top_n": top, "ledger_sharpe": None, "ledger_trial_id": None})
    return out


def freeze_portfolios(cfg: ForwardConfig, families=None) -> dict:
    """Create portfolios.json ONCE. Existing file is returned untouched (verified) - never re-selected."""
    if cfg.portfolios_path.exists():
        return load_portfolios(cfg)
    from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
    fams = list(families) if families is not None else list(DAILY_FAMILIES)
    top = cfg.i("FORWARD_TOP_N", 8)
    manual = parse_portfolios_setting(_get(cfg.settings, "FORWARD_PORTFOLIOS", ""), top)
    if manual:
        unknown = [p["family"] for p in manual if p["family"] not in DAILY_FAMILIES]
        if unknown:
            raise ValueError(f"FORWARD_PORTFOLIOS names unknown daily families: {unknown}")
        pf, source = manual, "settings:FORWARD_PORTFOLIOS"
    else:
        hs = [int(x) for x in cfg.s("FORWARD_HORIZONS", "5,10").split(",") if x.strip()]
        lp = cfg.resolve_ledger_path()
        if not lp.exists():
            raise FileNotFoundError(f"trial ledger not found: {lp} (cannot select portfolios)")
        pf, source = select_from_ledger(lp, fams, hs, top), f"ledger:{lp.name}"
    if not pf:
        raise ValueError("no portfolios selected (ledger has no matching trials)")
    cfg.ensure()
    doc = {"schema_version": 1, "freeze_version": 1, "created_at": utcnow_iso(), "source": source,
           "selection_rule": SELECTION_RULE, "n_portfolios": len(pf), "portfolios": pf, "disclaimer": NO_ORDER}
    doc["content_hash"] = _content_hash(doc)
    cfg.portfolios_path.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")
    return doc


def load_portfolios(cfg: ForwardConfig) -> dict:
    doc = json.loads(cfg.portfolios_path.read_text(encoding="utf-8"))
    if doc.get("content_hash") != _content_hash(doc):
        raise ValueError("portfolios.json content hash mismatch (frozen set was modified) - refusing to run")
    return doc
