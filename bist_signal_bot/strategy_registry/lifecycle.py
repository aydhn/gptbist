import uuid
from datetime import datetime, UTC
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.strategy_registry.models import (
    StrategyLifecycleEvent,
    StrategyLifecycleEventType,
    StrategyRegistryStatus
)
from bist_signal_bot.strategy_registry.storage import StrategyRegistryStore

class StrategyLifecycleManager:
    def __init__(self, settings: Settings | None = None, base_dir: Any | None = None):
        self.settings = settings or Settings()
        self.store = StrategyRegistryStore(self.settings, base_dir)

    def add_event(self, event: StrategyLifecycleEvent) -> StrategyLifecycleEvent:
        self.store.append_lifecycle_event(event)
        return event

    def events_for_strategy(self, strategy_id_or_name: str, limit: int = 100) -> list[StrategyLifecycleEvent]:
        return self.store.load_lifecycle_events(strategy_id_or_name, limit)

    def current_status(self, strategy_id_or_name: str) -> StrategyRegistryStatus:
        definition = self.store.get_definition(strategy_id_or_name)
        return definition.status if definition else StrategyRegistryStatus.UNKNOWN

    def transition(self, strategy_id: str, new_status: StrategyRegistryStatus, reason: str, actor: str | None = None, evidence_refs: list[str] | None = None, confirm: bool = False) -> StrategyLifecycleEvent:
        if not confirm and getattr(self.settings, "STRATEGY_REGISTRY_REQUIRE_CONFIRM_FOR_STATUS_CHANGE", True):
            raise ValueError(f"Transition to {new_status.value} requires confirmation.")

        definition = self.store.get_definition(strategy_id)
        if not definition:
            raise ValueError(f"Strategy {strategy_id} not found.")

        previous_status = definition.status
        definition.status = new_status
        definition.updated_at = datetime.now(UTC)

        self.store.append_definition(definition)

        event = StrategyLifecycleEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            strategy_id=definition.strategy_id,
            strategy_name=definition.strategy_name,
            event_type=self._status_to_event_type(new_status, previous_status),
            previous_status=previous_status,
            new_status=new_status,
            reason=reason,
            actor=actor,
            evidence_refs=evidence_refs or []
        )

        self.add_event(event)

        from bist_signal_bot.core.audit import AuditLogger, AuditEvent, AuditEventType
        logger = AuditLogger(self.settings)

        audit_type = getattr(AuditEventType, 'STRATEGY_UPDATED', AuditEventType.CLI_COMMAND)
        if new_status == StrategyRegistryStatus.VALIDATED_RESEARCH:
            audit_type = getattr(AuditEventType, 'STRATEGY_PROMOTION_COMPLETED', AuditEventType.CLI_COMMAND)
        elif new_status in [StrategyRegistryStatus.WATCH, StrategyRegistryStatus.DEGRADED]:
            audit_type = getattr(AuditEventType, 'STRATEGY_DEMOTION_COMPLETED', AuditEventType.CLI_COMMAND)
        elif new_status == StrategyRegistryStatus.BLOCKED:
            audit_type = getattr(AuditEventType, 'STRATEGY_BLOCKED', AuditEventType.CLI_COMMAND)

        logger.log_event(AuditEvent(
            event_type=audit_type,
            message=f"Strategy {definition.strategy_name} transitioned to {new_status.value}",
            metadata={
                "strategy_id": definition.strategy_id,
                "strategy_name": definition.strategy_name,
                "previous_status": previous_status.value,
                "new_status": new_status.value,
                "reason": reason,
                "no_real_order_sent": True
            }
        ))

        return event

    def _status_to_event_type(self, new_status: StrategyRegistryStatus, old_status: StrategyRegistryStatus) -> StrategyLifecycleEventType:
        if new_status == StrategyRegistryStatus.VALIDATED_RESEARCH and old_status in [StrategyRegistryStatus.CANDIDATE, StrategyRegistryStatus.WATCH]:
            return StrategyLifecycleEventType.PROMOTED
        elif new_status in [StrategyRegistryStatus.WATCH, StrategyRegistryStatus.DEGRADED] and old_status == StrategyRegistryStatus.VALIDATED_RESEARCH:
            return StrategyLifecycleEventType.DEMOTED
        elif new_status == StrategyRegistryStatus.BLOCKED:
            return StrategyLifecycleEventType.BLOCKED
        elif old_status == StrategyRegistryStatus.BLOCKED and new_status != StrategyRegistryStatus.BLOCKED:
            return StrategyLifecycleEventType.UNBLOCKED
        elif new_status == StrategyRegistryStatus.DEPRECATED:
            return StrategyLifecycleEventType.DEPRECATED
        elif new_status == StrategyRegistryStatus.ARCHIVED:
            return StrategyLifecycleEventType.ARCHIVED
        return StrategyLifecycleEventType.UPDATED
