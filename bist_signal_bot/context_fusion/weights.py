from typing import Dict, List
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.context_fusion.models import ContextLayer, ContextLayerSummary

class ContextWeightManager:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        from bist_signal_bot.context_fusion.sources import ContextSourceRegistry
        self.registry = ContextSourceRegistry(self.settings)

    def default_weights(self) -> Dict[ContextLayer, float]:
        return self.registry.default_layer_weights()

    def normalize_weights(self, weights: Dict[ContextLayer, float]) -> Dict[ContextLayer, float]:
        total = sum(v for v in weights.values() if v > 0)
        if total <= 0:
            return {k: 0.0 for k in weights}
        return {k: v / total for k, v in weights.items() if v > 0}

    def dynamic_weights(self, symbol: str | None, strategy_name: str | None, layer_summaries: List[ContextLayerSummary]) -> Dict[ContextLayer, float]:
        base_weights = self.default_weights()
        return self.adjust_for_missing_layers(base_weights, layer_summaries)

    def adjust_for_missing_layers(self, weights: Dict[ContextLayer, float], summaries: List[ContextLayerSummary]) -> Dict[ContextLayer, float]:
        present_layers = {s.layer for s in summaries if s.layer_score is not None}
        adjusted = {k: v for k, v in weights.items() if k in present_layers}
        return self.normalize_weights(adjusted)

    def validate_weights(self, weights: Dict[ContextLayer, float]) -> List[str]:
        warnings = []
        total = sum(weights.values())
        if abs(total - 1.0) > 0.001 and total > 0:
            warnings.append(f"Weights do not sum to 1.0 (sum={total}). They will be normalized.")
        for k, v in weights.items():
            if v < 0:
                warnings.append(f"Negative weight for layer {k.value}: {v}")
        return warnings
