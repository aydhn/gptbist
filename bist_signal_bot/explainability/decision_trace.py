import uuid
from datetime import datetime
from typing import Any
from bist_signal_bot.explainability.models import DecisionTrace

class DecisionTraceBuilder:
    def __init__(self, settings: Any = None):
        self.settings = settings

    def build_trace(self, signal_payload: dict[str, Any], stage_payloads: dict[str, Any] | None = None) -> DecisionTrace:
        stages = []
        if stage_payloads:
            for name, payload in stage_payloads.items():
                stages.append(self.add_stage(name, payload.get("status", "UNKNOWN"), payload.get("message", ""), {}))

        dec, blocked, reasons = self.final_decision_from_stages(stages)

        return DecisionTrace(
            trace_id=str(uuid.uuid4()),
            symbol=signal_payload.get("symbol", "UNKNOWN"),
            strategy_name=signal_payload.get("strategy_name"),
            signal_id=signal_payload.get("id"),
            created_at=datetime.utcnow(),
            stages=stages,
            final_decision=dec,
            blocked=blocked,
            blocked_reasons=reasons
        )

    def add_stage(self, name: str, status: str, message: str, metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": name,
            "status": status,
            "message": message,
            "metadata": metadata,
            "timestamp": datetime.utcnow().isoformat()
        }

    def final_decision_from_stages(self, stages: list[dict[str, Any]]) -> tuple[str, bool, list[str]]:
        blocked = False
        reasons = []
        for s in stages:
            if s.get("status") == "FAIL":
                blocked = True
                reasons.append(s.get("message", "Stage failed."))
        decision = "BLOCKED" if blocked else "PROCEED"
        return decision, blocked, reasons
