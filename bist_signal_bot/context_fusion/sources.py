from typing import Any, Dict, List
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.context_fusion.models import ContextLayer

class ContextSourceRegistry:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def supported_layers(self) -> List[ContextLayer]:
        return [
            ContextLayer.TECHNICAL_SIGNAL,
            ContextLayer.ML,
            ContextLayer.ENSEMBLE,
            ContextLayer.RISK,
            ContextLayer.EXECUTION,
            ContextLayer.CALIBRATION,
            ContextLayer.VALIDATION,
            ContextLayer.MONTE_CARLO,
            ContextLayer.STRATEGY_REGISTRY,
            ContextLayer.EVENT_RISK,
            ContextLayer.DISCLOSURE,
            ContextLayer.FINANCIALS,
            ContextLayer.VALUATION,
            ContextLayer.FACTORS,
            ContextLayer.BREADTH,
            ContextLayer.MACRO,
            ContextLayer.PORTFOLIO,
            ContextLayer.KNOWLEDGE
        ]

    def layer_definition(self, layer: ContextLayer) -> Dict[str, Any]:
        return {
            "layer": layer.value,
            "optional": self.is_layer_optional(layer),
            "stale_days": self.layer_staleness_limit_days(layer),
            "default_weight": self.default_layer_weights().get(layer, 0.0)
        }

    def default_layer_weights(self) -> Dict[ContextLayer, float]:
        return {
            ContextLayer.TECHNICAL_SIGNAL: getattr(self.settings, "CONTEXT_WEIGHT_TECHNICAL_SIGNAL", 0.15),
            ContextLayer.ML: getattr(self.settings, "CONTEXT_WEIGHT_ML", 0.08),
            ContextLayer.ENSEMBLE: getattr(self.settings, "CONTEXT_WEIGHT_ENSEMBLE", 0.10),
            ContextLayer.RISK: getattr(self.settings, "CONTEXT_WEIGHT_RISK", 0.10),
            ContextLayer.EXECUTION: getattr(self.settings, "CONTEXT_WEIGHT_EXECUTION", 0.05),
            ContextLayer.CALIBRATION: getattr(self.settings, "CONTEXT_WEIGHT_CALIBRATION", 0.10),
            ContextLayer.VALIDATION: getattr(self.settings, "CONTEXT_WEIGHT_VALIDATION", 0.08),
            ContextLayer.MONTE_CARLO: getattr(self.settings, "CONTEXT_WEIGHT_MONTE_CARLO", 0.06),
            ContextLayer.STRATEGY_REGISTRY: getattr(self.settings, "CONTEXT_WEIGHT_STRATEGY_REGISTRY", 0.08),
            ContextLayer.EVENT_RISK: getattr(self.settings, "CONTEXT_WEIGHT_EVENT_RISK", 0.05),
            ContextLayer.DISCLOSURE: getattr(self.settings, "CONTEXT_WEIGHT_DISCLOSURE", 0.04),
            ContextLayer.FINANCIALS: getattr(self.settings, "CONTEXT_WEIGHT_FINANCIALS", 0.04),
            ContextLayer.VALUATION: getattr(self.settings, "CONTEXT_WEIGHT_VALUATION", 0.04),
            ContextLayer.FACTORS: getattr(self.settings, "CONTEXT_WEIGHT_FACTORS", 0.04),
            ContextLayer.BREADTH: getattr(self.settings, "CONTEXT_WEIGHT_BREADTH", 0.04),
            ContextLayer.MACRO: getattr(self.settings, "CONTEXT_WEIGHT_MACRO", 0.04),
            ContextLayer.PORTFOLIO: getattr(self.settings, "CONTEXT_WEIGHT_PORTFOLIO", 0.05),
            ContextLayer.KNOWLEDGE: getattr(self.settings, "CONTEXT_WEIGHT_KNOWLEDGE", 0.02)
        }

    def layer_staleness_limit_days(self, layer: ContextLayer) -> int:
        mapping = {
            ContextLayer.TECHNICAL_SIGNAL: getattr(self.settings, "CONTEXT_STALE_TECHNICAL_DAYS", 3),
            ContextLayer.CALIBRATION: getattr(self.settings, "CONTEXT_STALE_CALIBRATION_DAYS", 30),
            ContextLayer.FINANCIALS: getattr(self.settings, "CONTEXT_STALE_FINANCIALS_DAYS", 120),
            ContextLayer.VALUATION: getattr(self.settings, "CONTEXT_STALE_VALUATION_DAYS", 30),
            ContextLayer.BREADTH: getattr(self.settings, "CONTEXT_STALE_BREADTH_DAYS", 5),
            ContextLayer.MACRO: getattr(self.settings, "CONTEXT_STALE_MACRO_DAYS", 10),
        }
        return mapping.get(layer, 7) # default 7 days for unspecified

    def is_layer_optional(self, layer: ContextLayer) -> bool:
        required = [ContextLayer.TECHNICAL_SIGNAL, ContextLayer.RISK]
        return layer not in required
