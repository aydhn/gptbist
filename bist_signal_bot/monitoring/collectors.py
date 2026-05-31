from typing import Any, List, Optional
from datetime import datetime
from bist_signal_bot.monitoring.models import MonitoringMetric, MonitoringObjectType

class MonitoringDataCollector:
    def collect_strategy_outcomes(self, strategy_name: str, limit: int = 1000) -> List[Any]:
        return []

    def collect_model_outcomes(self, model_id: str, limit: int = 1000) -> List[Any]:
        return []

    def collect_feature_set_quality(self, feature_set_id: str) -> List[Any]:
        return []

    def collect_calibration_outcomes(self, policy_id: Optional[str] = None, limit: int = 1000) -> List[Any]:
        return []

    def collect_portfolio_research_outcomes(self, portfolio_id: Optional[str] = None, limit: int = 1000) -> List[Any]:
        return []

    def collect_context_layer_outcomes(self, layer_name: str, limit: int = 1000) -> List[Any]:
        return []

    def collect_baseline_metrics(self, object_type: MonitoringObjectType, object_id: str) -> List[MonitoringMetric]:
        return []
