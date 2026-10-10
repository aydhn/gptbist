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
SCHEMA_VERSION = 2
TIER_CANDIDATE, TIER_CONTROL, TIER_WATCH = "candidate", "control", "watch"
ROLE_CANDIDATE, ROLE_RULE, ROLE_PLACEBO, ROLE_WATCH = "candidate", "rule_control", "placebo", "watch"
REPORT_GLOB = "daily_all_*.json"
SELECTION_RULE = ("per registered daily family and horizon: the v2 ledger trial (family <fam>_daily_xs_ew2, realistic "
                  "fills/robustness statistic, status ok, current FEATURES_VERSION for ML) with the highest net excess "
                  "Sharpe; tier 'candidate' iff the newest v2 daily_all report says CANDIDATE + robust for that "
                  "(family, horizon) (its selected params are used), else tier 'control' (best FORWARD_N_CONTROLS "
                  "families by ledger Sharpe) plus seeded random-score placebo portfolios (one per horizon); frozen at "
                  "registration time and never re-optimised")

DECISION_RULE = (
    "Tiers: 'candidate' (robust v2 CANDIDATE, not demoted by audit), 'watch' (v2 CANDIDATE label demoted by audit; tracked, no verdict weight) and 'control' (rule controls + seeded random placebo). A CANDIDATE "
    "portfolio gets a verdict only after >= {min_days} live trading days AND >= {min_cal} calendar days since its "
    "first decision (otherwise INSUFFICIENT). PASS iff ALL hold under the placeholder_commission scenario: "
    "(1) cumulative excess return over the equal-weight universe benchmark > 0; (2) NAV alpha over cash > 0; "
    "(3) Newey-West (overlap-aware) t-stat of the mean daily excess over EW >= max({min_t}, z(1-0.05/K)) with K = "
    "number of candidate-tier portfolios (Bonferroni); (4) >= {min_baskets} closed baskets and basket-level hit-rate vs "
    "EW >= 50%; (5) max drawdown < {max_dd:.0%}; (6) beats the same-horizon placebo shadow: cumulative excess over the "
    "placebo > 0 AND NW t of the daily difference >= {min_t}. Otherwise FAIL. Controls are informational (no verdict "
    "weight). Overall SUCCESS = >= 1 candidate PASS AND no placebo shows an edge (placebo NW t vs EW < {min_t}). "
    "Parameters are never retuned; any change starts a new forward directory (or an explicit new freeze version) with a "
    "new plan.")


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

    def portfolios_versions(self) -> dict:
        """{version: path} of the frozen files (portfolios.json = v1, portfolios.vN.json = vN)."""
        out = {}
        if self.forward_dir.exists():
            for f in self.forward_dir.iterdir():
                m = re.fullmatch(r"portfolios(?:\.v(\d+))?\.json", f.name)
                if m:
                    out[int(m.group(1)) if m.group(1) else 1] = f
        return out

    def portfolios_file(self, version: int) -> Path:
        return self.forward_dir / ("portfolios.json" if int(version) == 1 else f"portfolios.v{int(version)}.json")

    def active_portfolios_path(self) -> Path:
        v = self.portfolios_versions()
        return v[max(v)] if v else self.portfolios_file(1)

    def ensure(self) -> None:
        for d in (self.forward_dir, self.nav_dir, self.health_dir, self.reports_dir):
            d.mkdir(parents=True, exist_ok=True)

    # ---- paths ----
    decisions_path = property(lambda s: s.forward_dir / "decisions.jsonl")
    outcomes_path = property(lambda s: s.forward_dir / "outcomes.jsonl")
    portfolios_path = property(lambda s: s.active_portfolios_path())  # latest frozen version
    models_dir = property(lambda s: s.forward_dir / "models")
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
                "benchmarks": ["ew_universe", "xu100", "cash"], "never_retune": True, "tiers": [TIER_CANDIDATE, TIER_CONTROL],
                "doc": "docs/runbooks/forward_paper_plan.md"}


def _params_hash(params: dict) -> str:
    return hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()[:8]


def portfolio_id(family: str, params: dict, horizon: int, top_n: int) -> str:
    return f"{family}__h{int(horizon)}__top{int(top_n)}__{_params_hash(params)}"


def _content_hash(doc: dict) -> str:
    body = {k: v for k, v in doc.items() if k != "content_hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_v2_verdicts(reports_dir) -> dict:
    """{(family, horizon): {verdict, robust, selected_params, report}} from the NEWEST v2 ``daily_all_*.json`` that
    contains the (family, horizon). v1 (non-robust / old-suffix) reports are ignored, as are smoke reports and
    reports without a global-multiplicity ``snapshot_rowid``. Placebo rows are skipped."""
    from bist_signal_bot.edge_validation.xsection import LEDGER_SUFFIX_V2
    out: dict = {}
    d = Path(reports_dir) if reports_dir else None
    if d is None or not d.exists():
        return out
    for f in sorted(d.glob(REPORT_GLOB), reverse=True):
        try:
            doc = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        meta = doc.get("meta") or {}
        if not meta.get("robust") or meta.get("ledger_suffix") != LEDGER_SUFFIX_V2:
            continue
        if meta.get("smoke") or meta.get("snapshot_rowid") is None:  # smoke run / batch never finalized by a snapshot
            continue
        for r in doc.get("rows") or []:
            if r.get("placebo") or r.get("error"):
                continue
            k = (r.get("family"), int(r.get("horizon")))
            if k in out:
                continue
            out[k] = {"verdict": (r.get("verdicts") or {}).get(PRIMARY), "robust": r.get("robust"),
                      "selected_params": r.get("selected_params"), "report": f.name, "top_n": meta.get("top_n")}
    return out


def _v2_trials(ledger_path, fam: str, horizons) -> dict:
    """{horizon: [(sharpe, trial_id, params, top)]} of v2 ledger trials of ``fam`` (read-only SQLite)."""
    from bist_signal_bot.edge_validation.families_daily import DAILY_FAMILIES
    from bist_signal_bot.edge_validation.xsection import LEDGER_SUFFIX_V2
    fv_tag = ""
    if getattr(DAILY_FAMILIES.get(fam), "needs_horizon", False):
        from bist_signal_bot.model_loop.daily_features import FEATURES_VERSION
        fv_tag = f"|fv{FEATURES_VERSION}"
    con = sqlite3.connect(f"file:{Path(ledger_path).as_posix()}?mode=ro", uri=True)
    try:
        rows = con.execute("SELECT trial_id, params_json, universe, sharpe FROM trials WHERE strategy_family=? "
                           "AND status='ok' AND sharpe IS NOT NULL", (fam + LEDGER_SUFFIX_V2,)).fetchall()
    finally:
        con.close()
    out: dict = {}
    for tid, pj, uni, sh in rows:
        m = re.search(r"\|h(\d+)\|top(\d+)\|nors$", uni or "")
        if not m or int(m.group(1)) not in horizons or (fv_tag and not tid.endswith(fv_tag)):
            continue
        out.setdefault(int(m.group(1)), []).append((float(sh), tid, json.loads(pj or "{}"), int(m.group(2))))
    return out


def _pf(fam, params, h, top, tier, role, sharpe=None, tid=None, v2=None, source=None):
    return {"id": portfolio_id(fam, params, h, top), "family": fam, "params": params, "horizon": int(h),
            "top_n": int(top), "ledger_sharpe": sharpe, "ledger_trial_id": tid, "tier": tier, "role": role,
            "v2_verdict": (v2 or {}).get("verdict"), "v2_robust": (v2 or {}).get("robust"),
            "verdict_source": (v2 or {}).get("report") or source}


def placebo_portfolios(horizons, top_n: int, base_seed: int) -> list:
    from bist_signal_bot.forward.placebo import NAME
    return [_pf(NAME, {"seed": int(base_seed) + int(h)}, h, top_n, TIER_CONTROL, ROLE_PLACEBO,
                source="forward placebo (hash-seeded random scores, fixed)") for h in sorted(horizons)]


def parse_tier_overrides(raw) -> dict:
    """FORWARD_TIER_OVERRIDES: JSON {\"family|horizon\": \"watch\"} (audit demotions of v2 CANDIDATE labels)."""
    if raw in (None, "", {}):
        return {}
    d = json.loads(raw) if isinstance(raw, str) else dict(raw)
    bad = {k: v for k, v in d.items() if v not in (TIER_WATCH, TIER_CONTROL)}
    if bad:
        raise ValueError(f"FORWARD_TIER_OVERRIDES may only demote to watch/control: {bad}")
    return {str(k): str(v) for k, v in d.items()}


def select_v2(ledger_path, families, horizons, default_top_n: int = 8, reports_dir=None, n_controls: int = 6,
              placebo_seed: int = 20261010, tier_overrides=None) -> list:
    """v2 selection: per (family, horizon) best-Sharpe v2 ledger trial; tier from the newest v2 report verdict.

    * candidate: report verdict CANDIDATE + robust (its ``selected_params`` define the portfolio);
    * control: the best ``n_controls`` non-candidate (family, horizon) pairs (one per family) by ledger Sharpe;
    * placebo: one seeded random-score portfolio per horizon (always).
    Unknown verdict (family/horizon absent from every v2 report) -> control (never candidate)."""
    hs = sorted(set(int(h) for h in horizons))
    ovr = parse_tier_overrides(tier_overrides)
    verdicts = load_v2_verdicts(reports_dir)
    cands, pool = [], []
    for fam in sorted(families):
        trials = _v2_trials(ledger_path, fam, hs)
        for h in hs:
            rows = sorted(trials.get(h, []), key=lambda r: (r[0], r[1]), reverse=True)
            v = verdicts.get((fam, h))
            if v and v["verdict"] == "CANDIDATE" and v["robust"] is True and v.get("selected_params") is not None:
                params = dict(v["selected_params"])
                hit = next((r for r in rows if r[2] == params), None)
                top = hit[3] if hit else int(v.get("top_n") or default_top_n)
                dem = ovr.get(f"{fam}|{h}")  # audit demotion: label stays visible in v2_verdict, tier is lowered
                tier = dem or TIER_CANDIDATE
                role = {TIER_CANDIDATE: ROLE_CANDIDATE, TIER_WATCH: ROLE_WATCH, TIER_CONTROL: ROLE_RULE}[tier]
                cands.append(_pf(fam, params, h, top, tier, role, hit[0] if hit else None,
                                 hit[1] if hit else None, v))
            elif rows:
                sh, tid, params, top = rows[0]
                pool.append(_pf(fam, params, h, top, TIER_CONTROL, ROLE_RULE, sh, tid, v,
                                "unknown (no v2 report row)"))
    best_per_fam: dict = {}
    for p in pool:
        if p["family"] not in best_per_fam or p["ledger_sharpe"] > best_per_fam[p["family"]]["ledger_sharpe"]:
            best_per_fam[p["family"]] = p
    ctrl = sorted(best_per_fam.values(), key=lambda p: (-p["ledger_sharpe"], p["id"]))[:max(0, int(n_controls))]
    return cands + ctrl + placebo_portfolios(hs, default_top_n, placebo_seed)  # cands may hold demoted (watch) rows


def parse_portfolios_setting(raw, default_top_n: int) -> list:
    if raw in (None, "", []):
        return []
    lst = json.loads(raw) if isinstance(raw, str) else list(raw)
    out = []
    for p in lst:
        params, h = dict(p.get("params") or {}), int(p["horizon"])
        top = int(p.get("top_n") or default_top_n)
        tier = p.get("tier") or TIER_CONTROL
        role = p.get("role") or (ROLE_CANDIDATE if tier == TIER_CANDIDATE else ROLE_RULE)
        out.append(_pf(p["family"], params, h, top, tier, role, source="settings:FORWARD_PORTFOLIOS"))
    return out


def default_reports_dir(cfg: "ForwardConfig") -> Path:
    return cfg.resolve_ledger_path().parent / "reports"


def freeze_portfolios(cfg: ForwardConfig, families=None, force_new_version: bool = False) -> dict:
    """Create ``portfolios.json`` (v1) ONCE. An existing frozen set is returned untouched (hash verified) - never
    re-selected. ``force_new_version=True`` writes the NEXT file (``portfolios.v2.json`` ...) linked to the previous
    content hash; older versions are never modified or deleted."""
    versions = cfg.portfolios_versions()
    if versions and not force_new_version:
        return load_portfolios(cfg)
    prev = load_portfolios(cfg) if versions else None  # verifies the previous version before superseding it
    from bist_signal_bot.forward.placebo import NAME, all_families
    allf = all_families()
    fams = list(families) if families is not None else [f for f in allf if f != NAME]
    top = cfg.i("FORWARD_TOP_N", 8)
    manual = parse_portfolios_setting(_get(cfg.settings, "FORWARD_PORTFOLIOS", ""), top)
    if manual:
        unknown = [p["family"] for p in manual if p["family"] not in allf]
        if unknown:
            raise ValueError(f"FORWARD_PORTFOLIOS names unknown daily families: {unknown}")
        pf, source = manual, "settings:FORWARD_PORTFOLIOS"
    else:
        hs = [int(x) for x in cfg.s("FORWARD_HORIZONS", "5,10").split(",") if x.strip()]
        lp = cfg.resolve_ledger_path()
        if not lp.exists():
            raise FileNotFoundError(f"trial ledger not found: {lp} (cannot select portfolios)")
        pf = select_v2(lp, fams, hs, top, default_reports_dir(cfg), cfg.i("FORWARD_N_CONTROLS", 6),
                       cfg.i("FORWARD_PLACEBO_SEED", 20261010), _get(cfg.settings, "FORWARD_TIER_OVERRIDES", ""))
        source = f"ledger:{lp.name}+reports"
    if not pf:
        raise ValueError("no portfolios selected (ledger has no matching trials)")
    ids = [p["id"] for p in pf]
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate portfolio ids in the selection")
    version = (max(versions) + 1) if versions else 1
    path = cfg.portfolios_file(version)
    if path.exists():  # cannot happen (version = max+1) but never overwrite a frozen file
        raise FileExistsError(path)
    cfg.ensure()
    doc = {"schema_version": SCHEMA_VERSION, "freeze_version": version, "created_at": utcnow_iso(),
           "source": source, "selection_rule": SELECTION_RULE, "n_portfolios": len(pf),
           "n_candidates": sum(p["tier"] == TIER_CANDIDATE for p in pf),
           "n_watch": sum(p["tier"] == TIER_WATCH for p in pf), "portfolios": pf, "disclaimer": NO_ORDER}
    if prev is not None:
        doc["previous_version"], doc["previous_content_hash"] = prev["freeze_version"], prev["content_hash"]
    doc["content_hash"] = _content_hash(doc)
    path.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")
    return doc


def load_portfolios(cfg: ForwardConfig) -> dict:
    doc = json.loads(cfg.portfolios_path.read_text(encoding="utf-8"))
    if doc.get("content_hash") != _content_hash(doc):
        raise ValueError(f"{cfg.portfolios_path.name} content hash mismatch (frozen set was modified) - refusing to run")
    return doc


def portfolio_tier(p: dict) -> str:
    return p.get("tier") or TIER_CONTROL
