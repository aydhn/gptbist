from bist_signal_bot.app.model_registry_app import create_local_model_registry, create_model_governance_engine
import uuid
from datetime import datetime, UTC
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.strategy_registry.models import (
    StrategyEvidenceRef,
    StrategyEvidenceType
)
from bist_signal_bot.strategy_registry.storage import StrategyRegistryStore

class StrategyEvidenceCollector:
    def collect_model_evidence(self, model_id: str) -> dict[str, Any]:
        evidence = {}
        try:
            reg = create_local_model_registry(self.settings)
            gov = create_model_governance_engine(self.settings)

            model = reg.get_model(model_id)
            if model:
                evidence["model_status"] = model.status.value
                assessment = gov.assess_model(model_id)
                evidence["model_governance_status"] = assessment.status.value
                evidence["model_blocking_reasons"] = assessment.blocking_reasons
        except Exception as e:
            self.logger.warning(f"Failed to collect model evidence: {e}")
        return evidence

    def __init__(self, settings: Settings | None = None, base_dir: Any | None = None):
        self.settings = settings or Settings()
        self.store = StrategyRegistryStore(self.settings, base_dir)

    def collect_for_strategy(self, strategy_id_or_name: str) -> list[StrategyEvidenceRef]:
        definition = self.store.get_definition(strategy_id_or_name)
        if not definition:
            return []

        strategy_name = definition.strategy_name
        strategy_id = definition.strategy_id

        all_evidence = []
        all_evidence.extend(self.collect_backtest_evidence(strategy_name))
        all_evidence.extend(self.collect_validation_evidence(strategy_name))
        all_evidence.extend(self.collect_monte_carlo_evidence(strategy_name))
        all_evidence.extend(self.collect_execution_evidence(strategy_name))
        all_evidence.extend(self.collect_drift_evidence(strategy_name))
        all_evidence.extend(self.collect_performance_evidence(strategy_name))
        all_evidence.extend(self.collect_review_evidence(strategy_name))
        all_evidence.extend(self.collect_governance_evidence(strategy_name))

        # Ensure strategy_id is set
        for e in all_evidence:
            e.strategy_id = strategy_id
            if e.score is not None:
                e.score = max(0.0, min(100.0, e.score))

        # Also include previously saved evidence
        existing = self.store.load_evidence(strategy_id)

        # Deduplicate based on evidence_id
        seen = {e.evidence_id for e in existing}
        for e in all_evidence:
            if e.evidence_id not in seen:
                existing.append(e)

        return existing

    def collect_backtest_evidence(self, strategy_name: str) -> list[StrategyEvidenceRef]:
        # Mock logic to get latest backtest evidence
        return []

    def collect_validation_evidence(self, strategy_name: str) -> list[StrategyEvidenceRef]:
        # Mock logic
        return []

    def collect_monte_carlo_evidence(self, strategy_name: str) -> list[StrategyEvidenceRef]:
        # Mock logic
        return []

    def collect_execution_evidence(self, strategy_name: str) -> list[StrategyEvidenceRef]:
        # Mock logic
        return []

    def collect_drift_evidence(self, strategy_name: str) -> list[StrategyEvidenceRef]:
        # Mock logic
        return []

    def collect_performance_evidence(self, strategy_name: str) -> list[StrategyEvidenceRef]:
        # Mock logic
        return []

    def collect_review_evidence(self, strategy_name: str) -> list[StrategyEvidenceRef]:
        # Mock logic
        return []

    def collect_governance_evidence(self, strategy_name: str) -> list[StrategyEvidenceRef]:
        # Mock logic
        return []
