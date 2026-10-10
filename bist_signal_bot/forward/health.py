"""Forward health report, alerts (monitoring) and heartbeat. Simulation only; no real order is ever sent."""
from __future__ import annotations

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from bist_signal_bot.forward import NO_ORDER
from bist_signal_bot.forward.chain import HashChain
from bist_signal_bot.forward.config import PRIMARY, ForwardConfig, utcnow_iso


# ---------------- heartbeat (monitoring.heartbeat, file-backed store) ----------------
class ForwardHeartbeatStore:
    """Implements the append/load API HeartbeatManager expects, persisted to data/forward/heartbeats.jsonl."""

    def __init__(self, path: Path):
        self.path = Path(path)

    def append_heartbeat(self, record) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(record.model_dump_json() + "\n")
        return self.path

    def load_recent_heartbeats(self, limit: int = 100) -> list:
        from bist_signal_bot.monitoring.models import HeartbeatRecord
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()[-limit:]
        return [HeartbeatRecord.model_validate_json(x) for x in reversed(lines) if x.strip()]


def record_heartbeat(cfg: ForwardConfig, status: str, message: str, meta: dict) -> None:
    from bist_signal_bot.monitoring.heartbeat import HeartbeatManager
    from bist_signal_bot.monitoring.models import HealthLevel, MonitoringComponent
    lvl = {"OK": HealthLevel.HEALTHY, "KILL_SWITCH": HealthLevel.DEGRADED, "STALE": HealthLevel.DEGRADED,
           "FAILED": HealthLevel.UNHEALTHY}.get(status, HealthLevel.UNKNOWN)
    HeartbeatManager(storage=ForwardHeartbeatStore(cfg.heartbeat_path), settings=cfg.settings).record(
        MonitoringComponent.PAPER, lvl, message, metadata=meta)


# ---------------- alerts ----------------
def _existing_keys(cfg: ForwardConfig) -> set:
    keys = set()
    if cfg.alerts_path.exists():
        for ln in cfg.alerts_path.read_text(encoding="utf-8").splitlines():
            try:
                keys.add(json.loads(ln).get("metadata", {}).get("key"))
            except ValueError:
                pass
    return keys


def emit_alerts(cfg: ForwardConfig, alerts: list) -> list:
    """Append new (deduplicated by key) MonitoringAlert records to data/forward/alerts.jsonl; returns the new ones."""
    from bist_signal_bot.monitoring.models import (MonitoringAlert, MonitoringAlertType, MonitoringObjectType,
                                                   MonitoringStatus)
    seen, new = _existing_keys(cfg), []
    for a in alerts:
        if a["key"] in seen:
            continue
        seen.add(a["key"])
        m = MonitoringAlert(alert_id=f"fwd_{uuid.uuid4().hex[:10]}", alert_type=MonitoringAlertType.CUSTOM,
                            object_type=MonitoringObjectType.PORTFOLIO_RESEARCH, object_id=a.get("object", "forward"),
                            severity=a["severity"], status=MonitoringStatus.FAIL if a["severity"] == "HIGH"
                            else MonitoringStatus.WATCH, created_at=datetime.utcnow(), title=a["title"],
                            message=a["message"], routed_to=["reports"], metadata={"key": a["key"], "kind": a["kind"]})
        with open(cfg.alerts_path, "a", encoding="utf-8") as f:
            f.write(m.model_dump_json() + "\n")
        new.append(a)
    return new


def nav_summaries(cfg: ForwardConfig) -> dict:
    """Per portfolio: last NAV (primary scenario), peak, drawdown."""
    out = {}
    if not cfg.nav_dir.exists():
        return out
    for f in sorted(cfg.nav_dir.glob("*.csv")):
        try:
            df = pd.read_csv(f, index_col=0)
            s = df[f"nav_{PRIMARY}"].dropna()
            if len(s):
                out[f.stem] = {"nav": float(s.iloc[-1]), "peak": float(s.max()),
                               "drawdown": float(1.0 - s.iloc[-1] / s.max()), "days": int(len(s) - 1),
                               "last_date": str(df.index[-1])}
        except Exception:  # noqa: BLE001
            continue
    return out


def evaluate_alerts(cfg: ForwardConfig, res: dict, state_prev: dict) -> list:
    out = []
    fr = res.get("freshness") or {}
    exp = fr.get("expected_session", "?")
    if fr and fr.get("panel_lag_sessions", 0) > cfg.i("FORWARD_ALERT_STALE_SESSIONS", 1):
        out.append({"key": f"stale|{exp}", "kind": "STALE_DATA", "severity": "HIGH", "title": "Forward: stale daily data",
                    "message": f"panel last={fr.get('panel_last')} lag={fr.get('panel_lag_sessions')} sessions "
                               f"(expected {exp}). {NO_ORDER}"})
    if res.get("status") == "FAILED":
        out.append({"key": f"jobfail|{res.get('started_at')}", "kind": "JOB_FAILURE", "severity": "HIGH",
                    "title": "Forward: job failure", "message": "; ".join(res.get("errors", []))[:400] + f" {NO_ORDER}"})
    for name, p in (("decisions", cfg.decisions_path), ("outcomes", cfg.outcomes_path)):
        v = HashChain(p).verify()
        if not v["ok"]:
            out.append({"key": f"chain|{name}|{v['error']}|{v['line']}", "kind": "HASH_CHAIN_BREAK", "severity": "HIGH",
                        "title": f"Forward: hash chain break ({name})",
                        "message": f"{v['error']} at line {v['line']}. {NO_ORDER}"})
    levels = sorted(float(x) for x in cfg.s("FORWARD_DD_ALERT_LEVELS", "0.10,0.15,0.20").split(",") if x.strip())
    for pid, s in nav_summaries(cfg).items():
        for lv in levels:
            if s["drawdown"] >= lv:
                out.append({"key": f"dd|{pid}|{lv}", "kind": "DRAWDOWN", "severity": "HIGH" if lv >= 0.15 else "MEDIUM",
                            "object": pid, "title": f"Forward: drawdown >= {lv:.0%}",
                            "message": f"{pid} NAV drawdown {s['drawdown']:.1%} (shadow, simulated). {NO_ORDER}"})
    ks = (res.get("kill_switch") or {}).get("active")
    if ks is not None and state_prev.get("kill_switch_active") is not None and ks != state_prev["kill_switch_active"]:
        out.append({"key": f"ks|{ks}|{res.get('started_at')}", "kind": "KILL_SWITCH_TOGGLED", "severity": "HIGH",
                    "title": "Forward: kill switch toggled", "message": f"active={ks}. {NO_ORDER}"})
    return out


def after_run(cfg: ForwardConfig, res: dict, now: Optional[datetime] = None) -> None:
    from bist_signal_bot.forward.shadow import read_state, write_state
    prev = read_state(cfg)
    with open(cfg.runs_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({k: v for k, v in res.items() if k not in ("skipped",)}, sort_keys=True, default=str) + "\n")
    alerts = evaluate_alerts(cfg, res, prev)
    res["alerts_new"] = [a["kind"] for a in emit_alerts(cfg, alerts)]
    st = dict(prev)
    st.update(last_run_at=res.get("finished_at"), last_run_status=res["status"], last_as_of=res.get("as_of"),
              last_decisions_written=res.get("decisions_written", 0), last_errors=res.get("errors", [])[:5],
              kill_switch_active=(res.get("kill_switch") or {}).get("active", prev.get("kill_switch_active")))
    if res["status"] == "OK":
        st["last_ok_at"] = res.get("finished_at")
    write_state(cfg, st)
    record_heartbeat(cfg, res["status"], f"forward run {res['status']} as_of={res.get('as_of')} "
                     f"decisions={res.get('decisions_written', 0)}", {"errors": len(res.get("errors", []))})


# ---------------- health report ----------------
def dir_size(p: Path) -> int:
    return sum(f.stat().st_size for f in Path(p).rglob("*") if f.is_file()) if Path(p).exists() else 0


def build_health(cfg: ForwardConfig, now: Optional[datetime] = None, archive=None) -> dict:
    from bist_signal_bot.forward.shadow import (expected_session, kill_switch_state, read_state, series_freshness)
    from bist_signal_bot.intraday.archive import BarArchive
    own = archive is None
    if own:
        archive = BarArchive(path=cfg.archive_path, settings=cfg.settings)
    try:
        exp = expected_session(now, cfg.s("FORWARD_SESSION_READY_TIME", "18:30"))
        fr = series_freshness(archive, exp, cfg.f("FORWARD_MIN_COVERAGE", 0.8))
    finally:
        if own:
            archive.close()
    st = read_state(cfg)
    vd, vo = HashChain(cfg.decisions_path).verify(), HashChain(cfg.outcomes_path).verify()
    decs = [r for r in HashChain(cfg.decisions_path).records() if r.get("type") == "decision"]
    last_as_of = max((d["as_of"] for d in decs), default=None)
    errs = []
    if cfg.runs_path.exists():
        for ln in cfg.runs_path.read_text(encoding="utf-8").splitlines()[-30:]:
            try:
                errs += json.loads(ln).get("errors", [])
            except ValueError:
                pass
    du = shutil.disk_usage(cfg.forward_dir if cfg.forward_dir.exists() else cfg.forward_dir.parent)
    navs = nav_summaries(cfg)
    h = {"generated_at": utcnow_iso(), "disclaimer": NO_ORDER, "expected_session": str(exp), "freshness": fr,
         "last_run_at": st.get("last_run_at"), "last_run_status": st.get("last_run_status"),
         "last_ok_at": st.get("last_ok_at"), "decisions_total": len(decs),
         "decisions_last_as_of": last_as_of, "decisions_on_last_as_of": sum(1 for d in decs if d["as_of"] == last_as_of),
         "chain": {"decisions": vd, "outcomes": vo}, "chain_ok": bool(vd["ok"] and vo["ok"]),
         "kill_switch": kill_switch_state(cfg),
         "disk": {"forward_dir_bytes": dir_size(cfg.forward_dir),
                  "archive_bytes": Path(archive.path).stat().st_size if Path(str(archive.path)).exists() else None,
                  "disk_free_bytes": du.free},
         "recent_errors": errs[-5:], "portfolios": navs,
         "max_drawdown": max((s["drawdown"] for s in navs.values()), default=0.0)}
    bad = (not h["chain_ok"]) or h["kill_switch"]["active"] or fr["panel_lag_sessions"] > cfg.i("FORWARD_ALERT_STALE_SESSIONS", 1) \
        or st.get("last_run_status") in ("FAILED", None)
    h["overall"] = "ATTENTION" if bad else "OK"
    return h


def format_health(h: dict) -> str:
    fr = h["freshness"]
    lines = [f"FORWARD DAILY HEALTH [{h['overall']}] {h['generated_at']}",
             f"expected session {h['expected_session']} | panel last {fr.get('panel_last')} "
             f"(lag {fr.get('panel_lag_sessions')}, coverage {fr.get('coverage', 0):.0%}) | "
             f"XU100 {fr['XU100']['last']} (lag {fr['XU100']['lag_sessions']}) | "
             f"USDTRY {fr['USDTRY']['last']} (lag {fr['USDTRY']['lag_sessions']})",
             f"last run {h['last_run_at']} status {h['last_run_status']} | decisions total {h['decisions_total']} "
             f"(last as_of {h['decisions_last_as_of']}: {h['decisions_on_last_as_of']})",
             f"hash chain decisions={'OK' if h['chain']['decisions']['ok'] else 'BROKEN'} "
             f"outcomes={'OK' if h['chain']['outcomes']['ok'] else 'BROKEN'}",
             f"kill switch active={h['kill_switch']['active']} | max shadow drawdown {h['max_drawdown']:.1%}",
             f"disk forward={h['disk']['forward_dir_bytes'] / 1e6:.1f}MB free={h['disk']['disk_free_bytes'] / 1e9:.1f}GB"]
    if h["recent_errors"]:
        lines.append("errors: " + " | ".join(str(e)[:120] for e in h["recent_errors"]))
    lines.append(NO_ORDER)
    return "\n".join(lines)


def save_health(cfg: ForwardConfig, h: dict) -> Path:
    cfg.health_dir.mkdir(parents=True, exist_ok=True)
    day = h["generated_at"][:10].replace("-", "")
    p = cfg.health_dir / f"health_{day}.json"
    p.write_text(json.dumps(h, indent=2, sort_keys=True, default=str), encoding="utf-8")
    (cfg.health_dir / f"health_{day}.txt").write_text(format_health(h), encoding="utf-8")
    return p


def notify_telegram(cfg: ForwardConfig, h: dict, dry_run: bool = True) -> dict:
    """Format for the existing Telegram notifier. dry_run (or TELEGRAM_DRY_RUN / disabled) never sends; no secrets logged."""
    text = format_health(h)
    if dry_run:
        return {"sent": False, "dry_run": True, "text": text}
    from bist_signal_bot.notifications.models import NotificationLevel
    from bist_signal_bot.notifications.telegram_notifier import TelegramNotifier
    r = TelegramNotifier(cfg.settings).send_text("Forward shadow health", text,
                                                 NotificationLevel.WARNING if h["overall"] != "OK" else NotificationLevel.INFO)
    return {"sent": bool(getattr(r, "success", False)), "dry_run": False, "text": text}
