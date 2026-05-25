from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.strategy_registry.models import (
    StrategyRegistryStatus,
    StrategyGateDecision
)
from bist_signal_bot.strategy_registry.storage import StrategyRegistryStore

class StrategyQualityGate:
    def __init__(self, settings: Settings | None = None, base_dir: Any | None = None):
        self.settings = settings or Settings()
        self.store = StrategyRegistryStore(self.settings, base_dir)

    def evaluate_strategy(self, strategy_id_or_name: str) -> StrategyGateDecision:
        definition = self.store.get_definition(strategy_id_or_name)
        if not definition:
            return StrategyGateDecision.UNKNOWN

        if definition.status in [StrategyRegistryStatus.BLOCKED, StrategyRegistryStatus.ARCHIVED, StrategyRegistryStatus.DEPRECATED]:
            return StrategyGateDecision.BLOCK

        if definition.status == StrategyRegistryStatus.DEGRADED:
            return StrategyGateDecision.WATCH

        if definition.status == StrategyRegistryStatus.VALIDATED_RESEARCH:
            return StrategyGateDecision.ALLOW

        # Candidates or Watch
        scorecard = self.store.load_latest_scorecard(definition.strategy_id)
        if scorecard and scorecard.gate_decision == StrategyGateDecision.BLOCK:
            return StrategyGateDecision.BLOCK

        return StrategyGateDecision.REQUIRE_MORE_EVIDENCE

    def scanner_gate(self, strategy_name: str) -> StrategyGateDecision:
        if not getattr(self.settings, "STRATEGY_GATE_BEFORE_SCANNER", True):
            return StrategyGateDecision.ALLOW

        definition = self.store.get_definition(strategy_name)
        if not definition:
            return StrategyGateDecision.UNKNOWN

        if definition.status in [StrategyRegistryStatus.BLOCKED, StrategyRegistryStatus.ARCHIVED, StrategyRegistryStatus.DEPRECATED]:
            return StrategyGateDecision.BLOCK

        if definition.status == StrategyRegistryStatus.CANDIDATE and not getattr(self.settings, "STRATEGY_ALLOW_CANDIDATE_IN_SCANNER", False):
            return StrategyGateDecision.BLOCK

        if definition.status == StrategyRegistryStatus.DEGRADED and not getattr(self.settings, "STRATEGY_ALLOW_DEGRADED_IN_SCANNER", False):
            return StrategyGateDecision.BLOCK

        return StrategyGateDecision.ALLOW

    def ensemble_gate(self, strategy_name: str) -> StrategyGateDecision:
        if not getattr(self.settings, "STRATEGY_GATE_BEFORE_ENSEMBLE", True):
            return StrategyGateDecision.ALLOW
        return self.scanner_gate(strategy_name)

    def adaptive_gate(self, strategy_name: str) -> StrategyGateDecision:
        if not getattr(self.settings, "STRATEGY_GATE_BEFORE_ADAPTIVE", True):
            return StrategyGateDecision.ALLOW
        return self.scanner_gate(strategy_name)

    def research_lab_gate(self, strategy_name: str) -> StrategyGateDecision:
        # Research lab is more permissive, allows candidates always
        definition = self.store.get_definition(strategy_name)
        if not definition:
            return StrategyGateDecision.UNKNOWN

        if definition.status in [StrategyRegistryStatus.BLOCKED, StrategyRegistryStatus.ARCHIVED, StrategyRegistryStatus.DEPRECATED]:
            return StrategyGateDecision.BLOCK

        return StrategyGateDecision.ALLOW

    def release_gate(self) -> dict[str, Any]:
        definitions = self.store.load_definitions()
        blocked = [d.strategy_name for d in definitions if d.status == StrategyRegistryStatus.BLOCKED]
        return {
            "decision": StrategyGateDecision.BLOCK if blocked else StrategyGateDecision.ALLOW,
            "blocked_count": len(blocked),
            "blocked_strategies": blocked,
            "total_strategies": len(definitions)
        }
