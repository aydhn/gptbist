from typing import List, Optional, Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.context_fusion.models import (
    ContextSignal, ContextLayer, ContextDirection, ContextStatus, ContextLayerSummary
)

class ContextNormalizer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def normalize_signals(self, signals: List[ContextSignal]) -> List[ContextSignal]:
        normalized = []
        for signal in signals:
            norm_sig = signal.model_copy(deep=True)
            norm_sig.normalized_score = self.normalize_score(signal.score, signal.layer, signal.direction)
            norm_sig.direction = self.direction_from_score(norm_sig.normalized_score, signal.layer) if signal.direction == ContextDirection.UNKNOWN else signal.direction
            norm_sig.status = self.status_from_score(norm_sig.normalized_score, norm_sig.direction)
            normalized.append(norm_sig)
        return normalized

    def normalize_score(self, value: Optional[float], layer: ContextLayer, direction: Optional[ContextDirection] = None) -> Optional[float]:
        if value is None:
            return None

        clamped = max(0.0, min(100.0, float(value)))

        # Invert scores for layers where higher score is worse unless specified by direction
        inverted_layers = [ContextLayer.RISK, ContextLayer.EVENT_RISK, ContextLayer.MACRO]
        if layer in inverted_layers and direction != ContextDirection.SUPPORTIVE:
            return 100.0 - clamped

        return clamped

    def direction_from_score(self, score: Optional[float], layer: ContextLayer) -> ContextDirection:
        if score is None:
            return ContextDirection.UNKNOWN

        strong_threshold = getattr(self.settings, "CONTEXT_STRONG_SUPPORT_THRESHOLD", 75.0)
        pressure_threshold = getattr(self.settings, "CONTEXT_PRESSURE_THRESHOLD", 40.0)

        if score >= strong_threshold:
            return ContextDirection.SUPPORTIVE
        elif score <= pressure_threshold:
            return ContextDirection.NEGATIVE
        else:
            return ContextDirection.NEUTRAL

    def status_from_score(self, score: Optional[float], direction: ContextDirection) -> ContextStatus:
        if score is None:
            if direction in [ContextDirection.UNKNOWN, ContextDirection.NEUTRAL]:
                return ContextStatus.INSUFFICIENT_DATA
            elif direction == ContextDirection.BLOCKING_RESEARCH:
                return ContextStatus.HIGH_PRESSURE
            return ContextStatus.UNKNOWN

        strong_threshold = getattr(self.settings, "CONTEXT_STRONG_SUPPORT_THRESHOLD", 75.0)
        pressure_threshold = getattr(self.settings, "CONTEXT_PRESSURE_THRESHOLD", 40.0)

        if score >= strong_threshold:
            return ContextStatus.STRONG_SUPPORT
        elif score > 50.0:
            return ContextStatus.SUPPORT
        elif score >= pressure_threshold:
            return ContextStatus.NEUTRAL
        elif score > 20.0:
            return ContextStatus.PRESSURE
        else:
            return ContextStatus.HIGH_PRESSURE

    def normalize_layer_summary(self, signals: List[ContextSignal], layer: ContextLayer) -> ContextLayerSummary:
        from datetime import datetime, timezone
        import uuid

        if not signals:
            return ContextLayerSummary(
                summary_id=str(uuid.uuid4()),
                layer=layer,
                as_of=datetime.now(timezone.utc),
                signals=[],
                layer_status=ContextStatus.INSUFFICIENT_DATA,
                dominant_direction=ContextDirection.UNKNOWN
            )

        norm_signals = self.normalize_signals(signals)
        scores = [s.normalized_score for s in norm_signals if s.normalized_score is not None]
        avg_score = sum(scores) / len(scores) if scores else None

        symbol = norm_signals[0].symbol if norm_signals else None
        strategy_name = norm_signals[0].strategy_name if norm_signals else None
        as_of = max([s.as_of for s in norm_signals]) if norm_signals else datetime.now(timezone.utc)

        dominant_dir = self.direction_from_score(avg_score, layer)
        status = self.status_from_score(avg_score, dominant_dir)

        # Extract key points & warnings
        key_points = [s.title for s in norm_signals if s.status in [ContextStatus.STRONG_SUPPORT, ContextStatus.HIGH_PRESSURE]]
        warnings = [w for s in norm_signals for w in s.warnings]

        return ContextLayerSummary(
            summary_id=str(uuid.uuid4()),
            layer=layer,
            symbol=symbol,
            strategy_name=strategy_name,
            as_of=as_of,
            signals=norm_signals,
            layer_score=avg_score,
            layer_status=status,
            dominant_direction=dominant_dir,
            key_points=key_points,
            warnings=list(set(warnings))
        )
