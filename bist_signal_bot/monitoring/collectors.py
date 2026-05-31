import logging
from typing import Any
from bist_signal_bot.monitoring.models import MonitoringMetric, MonitoringObjectType

logger = logging.getLogger(__name__)

class MonitoringDataCollector:
    def collect_strategy_outcomes(self, strategy_name: str, limit: int = 1000) -> list[Any]:
        logger.warning(f"Mocking collect_strategy_outcomes for {strategy_name}")
        # Normally this would query Strategy Registry / Outcome dataset
        return []

    def collect_model_outcomes(self, model_id: str, limit: int = 1000) -> list[Any]:
        logger.warning(f"Mocking collect_model_outcomes for {model_id}")
        return []

    def collect_feature_set_quality(self, feature_set_id: str) -> list[Any]:
        logger.warning(f"Mocking collect_feature_set_quality for {feature_set_id}")
        return []

    def collect_calibration_outcomes(self, policy_id: str | None = None, limit: int = 1000) -> list[Any]:
        logger.warning(f"Mocking collect_calibration_outcomes for {policy_id}")
        return []

    def collect_portfolio_research_outcomes(self, portfolio_id: str | None = None, limit: int = 1000) -> list[Any]:
        logger.warning(f"Mocking collect_portfolio_research_outcomes for {portfolio_id}")
        return []

    def collect_context_layer_outcomes(self, layer_name: str, limit: int = 1000) -> list[Any]:
        logger.warning(f"Mocking collect_context_layer_outcomes for {layer_name}")
        return []

    def collect_baseline_metrics(self, object_type: MonitoringObjectType, object_id: str) -> list[MonitoringMetric]:
        logger.warning(f"Mocking collect_baseline_metrics for {object_type.value}:{object_id}")
        return []
