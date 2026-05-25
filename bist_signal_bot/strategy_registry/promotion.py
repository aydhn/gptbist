import uuid
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.strategy_registry.models import (
    StrategyDefinition,
    StrategyScorecard,
    StrategyPromotionRequest,
    StrategyPromotionResult,
    StrategyRegistryStatus,
    StrategyGateDecision
)
from bist_signal_bot.strategy_registry.storage import StrategyRegistryStore
from bist_signal_bot.strategy_registry.lifecycle import StrategyLifecycleManager
from bist_signal_bot.core.exceptions import StrategyPromotionError

class StrategyPromotionManager:
    def __init__(self, settings: Settings | None = None, base_dir: Any | None = None):
        self.settings = settings or Settings()
        self.store = StrategyRegistryStore(self.settings, base_dir)
        self.lifecycle = StrategyLifecycleManager(self.settings, base_dir)

    def promote(self, request: StrategyPromotionRequest) -> StrategyPromotionResult:
        if not request.confirm:
            raise StrategyPromotionError("Promotion requires explicit confirmation.")

        definition = self.store.get_definition(request.strategy_id)
        if not definition:
            raise StrategyPromotionError(f"Strategy {request.strategy_id} not found.")

        scorecard = self.store.load_latest_scorecard(request.strategy_id)

        errors = self.validate_promotion_requirements(definition, scorecard, request)
        if errors:
            result = StrategyPromotionResult(
                promotion_id=f"prom_{uuid.uuid4().hex[:8]}",
                request=request,
                decision=StrategyGateDecision.BLOCK,
                previous_status=definition.status,
                scorecard=scorecard,
                blocked_reasons=errors,
                warnings=["Promotion blocked due to unmet requirements."]
            )
            self.store.append_promotion_result(result)
            return result

        event = self.lifecycle.transition(
            strategy_id=definition.strategy_id,
            new_status=request.target_status,
            reason=request.reason,
            confirm=True
        )

        result = StrategyPromotionResult(
            promotion_id=f"prom_{uuid.uuid4().hex[:8]}",
            request=request,
            decision=StrategyGateDecision.ALLOW,
            previous_status=event.previous_status or StrategyRegistryStatus.UNKNOWN,
            new_status=event.new_status,
            scorecard=scorecard,
            event=event
        )

        self.store.append_promotion_result(result)
        return result

    def demote(self, strategy_id: str, reason: str, target_status: StrategyRegistryStatus = StrategyRegistryStatus.WATCH, confirm: bool = False) -> StrategyPromotionResult:
        request = StrategyPromotionRequest(strategy_id=strategy_id, target_status=target_status, reason=reason, confirm=confirm)
        if not confirm:
            raise StrategyPromotionError("Demotion requires explicit confirmation.")

        definition = self.store.get_definition(strategy_id)
        if not definition:
            raise StrategyPromotionError(f"Strategy {strategy_id} not found.")

        scorecard = self.store.load_latest_scorecard(strategy_id)

        event = self.lifecycle.transition(
            strategy_id=definition.strategy_id,
            new_status=target_status,
            reason=reason,
            confirm=True
        )

        result = StrategyPromotionResult(
            promotion_id=f"prom_{uuid.uuid4().hex[:8]}",
            request=request,
            decision=StrategyGateDecision.ALLOW,
            previous_status=event.previous_status or StrategyRegistryStatus.UNKNOWN,
            new_status=event.new_status,
            scorecard=scorecard,
            event=event
        )

        self.store.append_promotion_result(result)
        return result

    def block(self, strategy_id: str, reason: str, confirm: bool = False) -> StrategyPromotionResult:
        return self.demote(strategy_id, reason, StrategyRegistryStatus.BLOCKED, confirm)

    def unblock(self, strategy_id: str, reason: str, confirm: bool = False) -> StrategyPromotionResult:
        request = StrategyPromotionRequest(strategy_id=strategy_id, target_status=StrategyRegistryStatus.WATCH, reason=reason, confirm=confirm)
        if not confirm:
            raise StrategyPromotionError("Unblocking requires explicit confirmation.")

        definition = self.store.get_definition(strategy_id)
        if not definition:
            raise StrategyPromotionError(f"Strategy {strategy_id} not found.")

        scorecard = self.store.load_latest_scorecard(strategy_id)

        event = self.lifecycle.transition(
            strategy_id=definition.strategy_id,
            new_status=StrategyRegistryStatus.WATCH,
            reason=reason,
            confirm=True
        )

        result = StrategyPromotionResult(
            promotion_id=f"prom_{uuid.uuid4().hex[:8]}",
            request=request,
            decision=StrategyGateDecision.ALLOW,
            previous_status=event.previous_status or StrategyRegistryStatus.UNKNOWN,
            new_status=event.new_status,
            scorecard=scorecard,
            event=event
        )

        self.store.append_promotion_result(result)
        return result

    def validate_promotion_requirements(self, strategy: StrategyDefinition, scorecard: StrategyScorecard | None, request: StrategyPromotionRequest) -> list[str]:
        errors = []
        if request.require_scorecard and not scorecard:
            errors.append("Scorecard is required for promotion.")
            return errors

        if scorecard:
            min_validated = getattr(self.settings, "STRATEGY_SCORE_MIN_VALIDATED", 70.0)
            if scorecard.aggregate_score is not None and scorecard.aggregate_score < min_validated:
                errors.append(f"Aggregate score {scorecard.aggregate_score} is below minimum {min_validated}.")

            if request.require_governance_pass and scorecard.gate_decision == StrategyGateDecision.BLOCK:
                errors.append("Scorecard has blocked gate decision, likely due to governance finding.")

        return errors
