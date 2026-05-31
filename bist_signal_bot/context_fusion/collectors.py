import uuid
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.context_fusion.models import (
    ContextSignal, ContextLayer, ContextDirection, ContextStatus, ContextImportance
)

logger = logging.getLogger(__name__)

class ContextCollector:
    def collect_model_context(self, model_id: str) -> dict[str, Any]:
        context = {"source": "MODEL_REGISTRY"}
        try:
            from bist_signal_bot.app.model_registry_app import create_model_governance_engine
            gov = create_model_governance_engine(self.settings)
            assessment = gov.assess_model(model_id)
            context["model_governance_status"] = assessment.status.value
            context["validation_status"] = assessment.validation_status.value if assessment.validation_status else "UNKNOWN"
            context["calibration_status"] = assessment.calibration_status.value if assessment.calibration_status else "UNKNOWN"
        except Exception as e:
            self.logger.warning(f"Failed to collect model context: {e}")
        return context

    def __init__(self, settings: Settings | None = None, base_dir: Any | None = None):
        self.settings = settings or Settings()
        self.base_dir = base_dir

    def collect_for_signal(self, signal_payload: Dict[str, Any]) -> List[ContextSignal]:
        symbol = signal_payload.get("symbol")
        strategy_name = signal_payload.get("strategy_name")
        signal_id = signal_payload.get("signal_id")

        signals = []
        signals.extend(self.collect_technical_context(signal_payload))
        signals.extend(self.collect_for_symbol(symbol, strategy_name, signal_id))
        return signals

    def collect_for_symbol(self, symbol: str, strategy_name: Optional[str] = None, signal_id: Optional[str] = None) -> List[ContextSignal]:
        signals = []
        try:
            if getattr(self.settings, "CONTEXT_FUSION_COLLECT_ML", True):
                signals.extend(self.collect_ml_context(symbol, strategy_name, signal_id))
        except Exception as e:
            logger.warning(f"Failed to collect ML context: {e}")

        try:
            if getattr(self.settings, "CONTEXT_FUSION_COLLECT_ENSEMBLE", True):
                signals.extend(self.collect_ensemble_context(symbol, strategy_name, signal_id))
        except Exception as e:
            logger.warning(f"Failed to collect ENSEMBLE context: {e}")

        try:
            if getattr(self.settings, "CONTEXT_FUSION_COLLECT_RISK", True):
                signals.extend(self.collect_risk_context(symbol, strategy_name, signal_id))
        except Exception as e:
            logger.warning(f"Failed to collect RISK context: {e}")

        try:
            if getattr(self.settings, "CONTEXT_FUSION_COLLECT_EXECUTION", True):
                signals.extend(self.collect_execution_context(symbol, strategy_name, signal_id))
        except Exception as e:
            logger.warning(f"Failed to collect EXECUTION context: {e}")

        try:
            if getattr(self.settings, "CONTEXT_FUSION_COLLECT_CALIBRATION", True):
                signals.extend(self.collect_calibration_context(symbol, strategy_name, signal_id))
        except Exception as e:
            logger.warning(f"Failed to collect CALIBRATION context: {e}")

        try:
            if getattr(self.settings, "CONTEXT_FUSION_COLLECT_VALIDATION", True):
                signals.extend(self.collect_validation_context(symbol, strategy_name, signal_id))
        except Exception as e:
            logger.warning(f"Failed to collect VALIDATION context: {e}")

        try:
            if getattr(self.settings, "CONTEXT_FUSION_COLLECT_EVENTS", True):
                signals.extend(self.collect_event_context(symbol, strategy_name, signal_id))
        except Exception as e:
            logger.warning(f"Failed to collect EVENT context: {e}")

        try:
            if getattr(self.settings, "CONTEXT_FUSION_COLLECT_DISCLOSURES", True):
                signals.extend(self.collect_disclosure_context(symbol, strategy_name, signal_id))
        except Exception as e:
            logger.warning(f"Failed to collect DISCLOSURE context: {e}")

        try:
            if getattr(self.settings, "CONTEXT_FUSION_COLLECT_FINANCIALS", True):
                signals.extend(self.collect_financial_context(symbol, strategy_name, signal_id))
        except Exception as e:
            logger.warning(f"Failed to collect FINANCIAL context: {e}")

        try:
            if getattr(self.settings, "CONTEXT_FUSION_COLLECT_VALUATION", True):
                signals.extend(self.collect_valuation_context(symbol, strategy_name, signal_id))
        except Exception as e:
            logger.warning(f"Failed to collect VALUATION context: {e}")

        try:
            if getattr(self.settings, "CONTEXT_FUSION_COLLECT_FACTORS", True):
                signals.extend(self.collect_factor_context(symbol, strategy_name, signal_id))
        except Exception as e:
            logger.warning(f"Failed to collect FACTOR context: {e}")

        try:
            if getattr(self.settings, "CONTEXT_FUSION_COLLECT_BREADTH", True):
                signals.extend(self.collect_breadth_context(symbol, strategy_name, signal_id))
        except Exception as e:
            logger.warning(f"Failed to collect BREADTH context: {e}")

        try:
            if getattr(self.settings, "CONTEXT_FUSION_COLLECT_MACRO", True):
                signals.extend(self.collect_macro_context(symbol, strategy_name, signal_id))
        except Exception as e:
            logger.warning(f"Failed to collect MACRO context: {e}")

        try:
            if getattr(self.settings, "CONTEXT_FUSION_COLLECT_PORTFOLIO", True):
                signals.extend(self.collect_portfolio_context(symbol, strategy_name, signal_id))
        except Exception as e:
            logger.warning(f"Failed to collect PORTFOLIO context: {e}")

        try:
            if getattr(self.settings, "CONTEXT_FUSION_COLLECT_KNOWLEDGE", True):
                signals.extend(self.collect_knowledge_context(symbol, strategy_name, signal_id))
        except Exception as e:
            logger.warning(f"Failed to collect KNOWLEDGE context: {e}")

        return signals

    def collect_technical_context(self, payload: Dict[str, Any]) -> List[ContextSignal]:
        score = payload.get("score")
        direction = ContextDirection.SUPPORTIVE if payload.get("direction") == "LONG" else ContextDirection.NEGATIVE if payload.get("direction") == "SHORT" else ContextDirection.NEUTRAL

        sig = ContextSignal(
            context_id=str(uuid.uuid4()),
            layer=ContextLayer.TECHNICAL_SIGNAL,
            symbol=payload.get("symbol"),
            strategy_name=payload.get("strategy_name"),
            signal_id=payload.get("signal_id"),
            as_of=datetime.now(timezone.utc),
            title="Technical Signal",
            value=payload.get("direction"),
            score=score,
            direction=direction,
            status=ContextStatus.UNKNOWN,
            importance=ContextImportance.HIGH,
            message="Technical signal collected from payload.",
            metadata=payload
        )
        return [sig]

    def collect_ml_context(self, symbol: str, strategy_name: Optional[str] = None, signal_id: Optional[str] = None) -> List[ContextSignal]:
        return []

    def collect_ensemble_context(self, symbol: str, strategy_name: Optional[str] = None, signal_id: Optional[str] = None) -> List[ContextSignal]:
        return []

    def collect_risk_context(self, symbol: str, strategy_name: Optional[str] = None, signal_id: Optional[str] = None) -> List[ContextSignal]:
        return []

    def collect_execution_context(self, symbol: str, strategy_name: Optional[str] = None, signal_id: Optional[str] = None) -> List[ContextSignal]:
        return []

    def collect_calibration_context(self, symbol: str, strategy_name: Optional[str] = None, signal_id: Optional[str] = None) -> List[ContextSignal]:
        return []

    def collect_validation_context(self, symbol: str, strategy_name: Optional[str] = None, signal_id: Optional[str] = None) -> List[ContextSignal]:
        return []

    def collect_strategy_registry_context(self, symbol: str, strategy_name: Optional[str] = None, signal_id: Optional[str] = None) -> List[ContextSignal]:
        return []

    def collect_event_context(self, symbol: str, strategy_name: Optional[str] = None, signal_id: Optional[str] = None) -> List[ContextSignal]:
        return []

    def collect_disclosure_context(self, symbol: str, strategy_name: Optional[str] = None, signal_id: Optional[str] = None) -> List[ContextSignal]:
        return []

    def collect_financial_context(self, symbol: str, strategy_name: Optional[str] = None, signal_id: Optional[str] = None) -> List[ContextSignal]:
        return []

    def collect_valuation_context(self, symbol: str, strategy_name: Optional[str] = None, signal_id: Optional[str] = None) -> List[ContextSignal]:
        return []

    def collect_factor_context(self, symbol: str, strategy_name: Optional[str] = None, signal_id: Optional[str] = None) -> List[ContextSignal]:
        return []

    def collect_breadth_context(self, symbol: str, strategy_name: Optional[str] = None, signal_id: Optional[str] = None) -> List[ContextSignal]:
        return []

    def collect_macro_context(self, symbol: str, strategy_name: Optional[str] = None, signal_id: Optional[str] = None) -> List[ContextSignal]:
        return []

    def collect_portfolio_context(self, symbol: str, strategy_name: Optional[str] = None, signal_id: Optional[str] = None) -> List[ContextSignal]:
        return []

    def collect_knowledge_context(self, symbol: str, strategy_name: Optional[str] = None, signal_id: Optional[str] = None) -> List[ContextSignal]:
        return []
