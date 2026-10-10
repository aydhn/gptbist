"""Model lifecycle: drift -> challenger -> comparison -> confirmed promotion / rollback.

Research/paper only. No real order is ever sent. Promotion is a registry status
change of a local research model, always gated by security preflight, kill
switch, an explicit ``confirm=True`` and an audit event.

Registry conventions (on ``model_registry.models.ModelRecord``):
  * champion   : status ACTIVE_RESEARCH
  * challenger : tag "challenger"; status CANDIDATE (gate CANDIDATE),
                 FAILED_VALIDATION (REJECTED) or WATCH (INSUFFICIENT_DATA)
  * baseline   : model_kind BASELINE (never auto-promoted)
  * OOS metrics / gate verdict live in ``record.metadata``.

The comparison is done here on OOS net Sharpe (+ Brier / log-loss no-worse
checks) instead of ``monitoring.champion_challenger.ChampionChallengerEngine``,
whose ``decision_score`` is a dummy constant.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

import pandas as pd

from bist_signal_bot.core.audit import AuditEvent, AuditEventType
from bist_signal_bot.model_loop.drift_monitor import DriftDecision, DriftMonitor
from bist_signal_bot.model_registry.models import ModelKind, ModelRecord, ModelRegistryStatus
from bist_signal_bot.security.models import KillSwitchScope

NO_ORDER_MSG = "No real order sent."
TAG_CHALLENGER = "challenger"
logger = logging.getLogger(__name__)


def _setting(settings: Any, key: str, default: Any) -> Any:
    try:
        v = getattr(settings, key, default)
    except Exception:
        return default
    return default if v is None else v


def _to_dt(as_of: Any) -> datetime:
    ts = pd.Timestamp(as_of)
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    return ts.to_pydatetime()


@dataclass
class LifecycleReport:
    as_of: str
    champion_id: Optional[str] = None
    challenger_id: Optional[str] = None
    drift: Optional[DriftDecision] = None
    trained: bool = False
    skipped_reason: str = ""
    comparison: dict = field(default_factory=dict)
    promotion_recommended: bool = False
    actions: list = field(default_factory=list)
    no_real_order_sent: bool = True
    message: str = NO_ORDER_MSG


@dataclass
class PromotionResult:
    model_id: str
    status: str            # PROMOTED | DRY_RUN | BLOCKED | NOT_FOUND
    dry_run: bool
    reasons: list = field(default_factory=list)
    previous_champion_id: Optional[str] = None
    no_real_order_sent: bool = True
    message: str = NO_ORDER_MSG


class ModelLifecycle:
    def __init__(self, registry, trainer, drift_monitor: DriftMonitor | None, audit, preflight,
                 kill_switch, settings, data_provider: Callable[[datetime], dict] | None = None):
        self.registry = registry
        self.trainer = trainer
        self.drift_monitor = drift_monitor or DriftMonitor(settings)
        self.audit = audit
        self.preflight = preflight
        self.kill_switch = kill_switch
        self.settings = settings
        self.data_provider = data_provider

    # ---------------------------------------------------------------- helpers
    def _audit(self, etype: AuditEventType, message: str, level: str = "INFO", **meta) -> None:
        meta.setdefault("no_real_order_sent", True)
        meta.setdefault("disclaimer", NO_ORDER_MSG)
        try:
            if self.audit is not None:
                self.audit.log_event(AuditEvent(event_type=etype, message=message, level=level, metadata=meta))
        except Exception as exc:  # audit must never break the loop
            logger.warning("audit failure: %s", exc)

    def _kill_switch_active(self) -> bool:
        if self.kill_switch is None:
            return False
        try:
            return bool(self.kill_switch.is_active(KillSwitchScope.ML))
        except Exception:
            return True  # fail safe

    def _preflight_ok(self, name: str) -> tuple[bool, str]:
        if self.preflight is None:
            return True, ""
        try:
            res = self.preflight.run_cli_preflight(name)
        except Exception as exc:
            return False, f"preflight failed: {exc}"
        for attr in ("passed", "overall_pass"):
            if getattr(res, attr, True) is False:
                return False, "preflight reported failure"
        return True, ""

    def champion(self) -> Optional[ModelRecord]:
        recs = [r for r in self.registry.list_models(status=ModelRegistryStatus.ACTIVE_RESEARCH)]
        return recs[0] if recs else None  # list_models sorts newest first

    def _challengers(self) -> list[ModelRecord]:
        return [r for r in self.registry.list_models() if TAG_CHALLENGER in (r.tags or [])]

    def _save(self, rec: ModelRecord) -> None:
        rec.updated_at = datetime.now(timezone.utc)
        self.registry.register_model(rec, confirm=True)

    def _last_retrain(self) -> Optional[datetime]:
        stamps = []
        for r in self._challengers():
            s = (r.metadata or {}).get("loop_as_of")
            if s:
                stamps.append(_to_dt(s))
        return max(stamps) if stamps else None

    def _metrics(self, rec: ModelRecord) -> dict:
        m = dict((rec.metadata or {}).get("oos_metrics") or {})
        if m.get("net_sharpe") is None:
            alt = m.get("oos_net_sharpe_annual", (rec.metadata or {}).get("oos_net_sharpe_annual"))
            if alt is not None:
                m["net_sharpe"] = alt
        if m.get("net_sharpe") is None:
            try:
                v = self.trainer.latest_oos_net_sharpe(rec.model_id)
            except Exception:
                v = None
            if v is not None:
                m["net_sharpe"] = v
        return m

    # ------------------------------------------------------------- comparison
    def compare(self, champion: Optional[ModelRecord], challenger: ModelRecord) -> dict:
        verdict = (challenger.metadata or {}).get("gate_verdict")
        min_imp = float(_setting(self.settings, "MODEL_LOOP_MIN_CHALLENGER_IMPROVEMENT", 0.0))
        out: dict = {"gate_verdict": verdict, "better": False, "reasons": [], "min_improvement": min_imp}
        if verdict != "CANDIDATE":
            out["reasons"].append(f"gate_verdict={verdict}: not eligible for promotion")
            return out
        cm = self._metrics(challenger)
        out["challenger_metrics"] = cm
        if champion is None:
            out["reasons"].append("no champion: first champion needs explicit confirmed promotion")
            out["better"] = cm.get("net_sharpe") is not None
            out["no_champion"] = True
            return out
        om = self._metrics(champion)
        out["champion_metrics"] = om
        cs, os_ = cm.get("net_sharpe"), om.get("net_sharpe")
        if cs is None or os_ is None:
            out["reasons"].append("net Sharpe unavailable for comparison")
            return out
        ok = cs > os_ + min_imp
        if not ok:
            out["reasons"].append(f"net_sharpe {cs:.3f} not > champion {os_:.3f} + {min_imp}")
        for k in ("brier", "log_loss"):
            if cm.get(k) is not None and om.get(k) is not None and cm[k] > om[k]:
                ok = False
                out["reasons"].append(f"{k} worse: {cm[k]:.4f} > {om[k]:.4f}")
        out["better"] = ok
        return out

    # --------------------------------------------------------------- evaluate
    def evaluate(self, as_of, ref_df=None, cur_df=None, perf_stream=None, force: bool = False) -> LifecycleReport:
        dt = _to_dt(as_of)
        champ = self.champion()
        rep = LifecycleReport(as_of=dt.isoformat(), champion_id=champ.model_id if champ else None)

        if self.data_provider is not None and ref_df is None and perf_stream is None:
            try:
                d = self.data_provider(dt) or {}
                ref_df, cur_df, perf_stream = d.get("ref_df"), d.get("cur_df"), d.get("perf_stream")
            except Exception as exc:
                rep.actions.append(f"data_provider_failed: {exc}")

        parts = []
        if ref_df is not None and cur_df is not None:
            parts.append(self.drift_monitor.check_features(ref_df, cur_df))
        if perf_stream is not None:
            parts.append(self.drift_monitor.check_performance(perf_stream))
        decision = DriftMonitor.combine(*parts) if parts else DriftDecision(False, ["no drift inputs"])
        if force:
            decision.retrain = True
            decision.reasons.append("forced")
        rep.drift = decision
        if decision.severity != "none" or force:
            self._audit(AuditEventType.MODEL_LOOP_DRIFT_DETECTED, "Model-loop drift detected",
                        level="WARNING", severity=decision.severity, reasons=decision.reasons,
                        retrain=decision.retrain, as_of=rep.as_of)
            rep.actions.append("drift_detected")

        if not decision.retrain:
            rep.skipped_reason = "no retrain warranted"
            return rep
        if self._kill_switch_active():
            rep.skipped_reason = "kill_switch_active"
            self._audit(AuditEventType.MODEL_LOOP_CHALLENGER_REJECTED, "Retrain blocked by kill switch",
                        level="WARNING", as_of=rep.as_of)
            return rep
        min_days = float(_setting(self.settings, "MODEL_LOOP_MIN_DAYS_BETWEEN_RETRAIN", 5))
        last = self._last_retrain()
        if last is not None and (dt - last).total_seconds() < min_days * 86400:
            rep.skipped_reason = f"min_days_between_retrain={min_days} not elapsed since {last.isoformat()}"
            return rep

        info = self.trainer.train(as_of)
        rec = self._record_challenger(info, dt)
        rep.trained, rep.challenger_id = True, rec.model_id
        rep.actions.append("challenger_trained")
        self._audit(AuditEventType.MODEL_LOOP_CHALLENGER_TRAINED, "Challenger trained (never auto-champion)",
                    model_id=rec.model_id, gate_verdict=info.gate_verdict, as_of=rep.as_of)

        cmp_ = self.compare(champ, rec)
        rep.comparison = cmp_
        rep.promotion_recommended = bool(cmp_["better"]) and not cmp_.get("no_champion", False)
        if cmp_["gate_verdict"] != "CANDIDATE" or (champ is not None and not cmp_["better"]):
            rep.actions.append("challenger_recorded_not_promoted")
            self._audit(AuditEventType.MODEL_LOOP_CHALLENGER_REJECTED, "Challenger not eligible/better; recorded only",
                        model_id=rec.model_id, reasons=cmp_["reasons"], as_of=rep.as_of)
        else:
            rep.actions.append("promotion_recommended" if rep.promotion_recommended else "awaiting_manual_first_champion")
        return rep

    def _record_challenger(self, info, dt: datetime) -> ModelRecord:
        verdict = info.gate_verdict
        status = {"CANDIDATE": ModelRegistryStatus.CANDIDATE,
                  "REJECTED": ModelRegistryStatus.FAILED_VALIDATION}.get(verdict, ModelRegistryStatus.WATCH)
        now = datetime.now(timezone.utc)
        rec = self.registry.get_model(info.model_id)
        if rec is None:
            rec = ModelRecord(model_id=info.model_id, model_name=info.model_id, model_kind=ModelKind.CLASSIFIER,
                              version=str(info.trained_through or "1"), created_at=now, status=status)
        rec.status = status  # never a champion status, whatever the trainer registered
        if TAG_CHALLENGER not in rec.tags:
            rec.tags.append(TAG_CHALLENGER)
        rec.metadata = dict(rec.metadata or {})
        rec.metadata.update({"gate_verdict": verdict, "oos_metrics": dict(info.oos_metrics or {}),
                             "loop_as_of": dt.isoformat(), "trained_through": info.trained_through,
                             "n_events": info.n_events, "artifact_path": info.artifact_path,
                             "loop_kind": info.kind, "interval": info.interval})
        self._save(rec)
        return rec

    # ---------------------------------------------------------------- promote
    def promote(self, challenger_id: str, confirm: bool = False) -> PromotionResult:
        rec = self.registry.get_model(challenger_id)
        if rec is None:
            return PromotionResult(challenger_id, "NOT_FOUND", not confirm, ["model not found"])
        champ = self.champion()
        prev_id = champ.model_id if champ else None
        reasons: list[str] = []
        if rec.status == ModelRegistryStatus.ACTIVE_RESEARCH:
            reasons.append("already champion")
        if TAG_CHALLENGER not in (rec.tags or []):
            reasons.append("model is not a registered challenger")
        cmp_ = self.compare(champ, rec)
        if cmp_["gate_verdict"] != "CANDIDATE":
            reasons.append(f"gate_verdict={cmp_['gate_verdict']} (CANDIDATE required)")
        elif champ is not None and not cmp_["better"]:
            reasons.extend(cmp_["reasons"] or ["challenger not better than champion"])
        elif champ is None and not cmp_["better"]:
            reasons.append("net Sharpe unavailable for first champion")
        if self._kill_switch_active():
            reasons.append("kill switch active")
        ok, why = self._preflight_ok("model-loop promote")
        if not ok:
            reasons.append(why)

        if reasons:
            self._audit(AuditEventType.MODEL_LOOP_CHALLENGER_REJECTED, "Promotion blocked", level="WARNING",
                        model_id=challenger_id, reasons=reasons, confirm=confirm)
            return PromotionResult(challenger_id, "BLOCKED", not confirm, reasons, prev_id)
        if not confirm:
            return PromotionResult(challenger_id, "DRY_RUN", True, ["confirm=True required to apply"], prev_id)

        if champ is not None:
            champ.status = ModelRegistryStatus.ARCHIVED
            champ.metadata = dict(champ.metadata or {})
            champ.metadata["superseded_by"] = rec.model_id
            self._save(champ)
        rec.status = ModelRegistryStatus.ACTIVE_RESEARCH
        rec.metadata = dict(rec.metadata or {})
        rec.metadata["previous_champion_id"] = prev_id
        rec.metadata["promoted_at"] = datetime.now(timezone.utc).isoformat()
        self._save(rec)
        self._audit(AuditEventType.MODEL_LOOP_PROMOTED, "Challenger promoted to research champion (paper only)",
                    model_id=rec.model_id, previous_champion_id=prev_id, comparison=cmp_)
        return PromotionResult(rec.model_id, "PROMOTED", False, [], prev_id)

    # --------------------------------------------------------------- rollback
    def rollback(self, confirm: bool = False) -> PromotionResult:
        champ = self.champion()
        if champ is None:
            return PromotionResult("", "BLOCKED", not confirm, ["no champion"])
        prev_id = (champ.metadata or {}).get("previous_champion_id")
        prev = self.registry.get_model(prev_id) if prev_id else None
        reasons: list[str] = []
        if prev is None:
            reasons.append("no previous champion to roll back to")
        if self._kill_switch_active():
            reasons.append("kill switch active")
        ok, why = self._preflight_ok("model-loop rollback")
        if not ok:
            reasons.append(why)
        if reasons:
            self._audit(AuditEventType.MODEL_LOOP_ROLLED_BACK, "Rollback blocked", level="WARNING",
                        reasons=reasons, confirm=confirm)
            return PromotionResult(champ.model_id, "BLOCKED", not confirm, reasons, prev_id)
        if not confirm:
            return PromotionResult(prev.model_id, "DRY_RUN", True, ["confirm=True required to apply"], champ.model_id)
        champ.status = ModelRegistryStatus.ARCHIVED
        champ.metadata = dict(champ.metadata or {})
        champ.metadata["rolled_back"] = True
        self._save(champ)
        prev.status = ModelRegistryStatus.ACTIVE_RESEARCH
        self._save(prev)
        self._audit(AuditEventType.MODEL_LOOP_ROLLED_BACK, "Rolled back to previous champion",
                    from_model_id=champ.model_id, to_model_id=prev.model_id)
        return PromotionResult(prev.model_id, "PROMOTED", False, ["rolled back"], champ.model_id)

    def status(self) -> dict:
        champ = self.champion()
        return {"champion_id": champ.model_id if champ else None,
                "challengers": [(r.model_id, r.status.value) for r in self._challengers()],
                "last_retrain": (self._last_retrain().isoformat() if self._last_retrain() else None),
                "kill_switch_active": self._kill_switch_active(),
                "no_real_order_sent": True, "message": NO_ORDER_MSG}
