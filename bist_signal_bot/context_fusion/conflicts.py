import uuid
from typing import Any, Dict, List, Optional
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.context_fusion.models import (
    ContextLayerSummary, ContextConflict, ConflictType, ContextLayer,
    ContextImportance, ContextDirection
)

class ContextConflictResolver:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def detect_conflicts(self, summaries: List[ContextLayerSummary]) -> List[ContextConflict]:
        conflicts = []
        c1 = self.high_score_high_risk(summaries)
        if c1: conflicts.append(c1)

        c2 = self.technical_vs_macro(summaries)
        if c2: conflicts.append(c2)

        c3 = self.technical_vs_breadth(summaries)
        if c3: conflicts.append(c3)

        c4 = self.technical_vs_event(summaries)
        if c4: conflicts.append(c4)

        c5 = self.ml_vs_strategy(summaries)
        if c5: conflicts.append(c5)

        c6 = self.calibration_mismatch(summaries)
        if c6: conflicts.append(c6)

        c7 = self.liquidity_cost_conflict(summaries)
        if c7: conflicts.append(c7)

        return conflicts

    def high_score_high_risk(self, summaries: List[ContextLayerSummary]) -> Optional[ContextConflict]:
        tech = next((s for s in summaries if s.layer == ContextLayer.TECHNICAL_SIGNAL), None)
        risk = next((s for s in summaries if s.layer == ContextLayer.RISK), None)

        if tech and risk and tech.dominant_direction == ContextDirection.SUPPORTIVE and risk.dominant_direction == ContextDirection.NEGATIVE:
            return ContextConflict(
                conflict_id=str(uuid.uuid4()),
                conflict_type=ConflictType.HIGH_SCORE_HIGH_RISK,
                symbol=tech.symbol,
                involved_layers=[ContextLayer.TECHNICAL_SIGNAL, ContextLayer.RISK],
                severity=ContextImportance.HIGH,
                score_impact=getattr(self.settings, "CONTEXT_CONFLICT_PENALTY_HIGH", 10.0),
                message="High technical score but high risk pressure detected.",
                suggested_review_reason="Check if risk overrides technical signal."
            )
        return None

    def technical_vs_macro(self, summaries: List[ContextLayerSummary]) -> Optional[ContextConflict]:
        tech = next((s for s in summaries if s.layer == ContextLayer.TECHNICAL_SIGNAL), None)
        macro = next((s for s in summaries if s.layer == ContextLayer.MACRO), None)

        if tech and macro and tech.dominant_direction == ContextDirection.SUPPORTIVE and macro.dominant_direction == ContextDirection.NEGATIVE:
            return ContextConflict(
                conflict_id=str(uuid.uuid4()),
                conflict_type=ConflictType.TECHNICAL_VS_MACRO,
                symbol=tech.symbol,
                involved_layers=[ContextLayer.TECHNICAL_SIGNAL, ContextLayer.MACRO],
                severity=ContextImportance.MEDIUM,
                score_impact=getattr(self.settings, "CONTEXT_CONFLICT_PENALTY_MEDIUM", 5.0),
                message="Technical signal is supportive but macro regime is negative.",
                suggested_review_reason="Evaluate macro headwinds."
            )
        return None

    def technical_vs_breadth(self, summaries: List[ContextLayerSummary]) -> Optional[ContextConflict]:
        tech = next((s for s in summaries if s.layer == ContextLayer.TECHNICAL_SIGNAL), None)
        breadth = next((s for s in summaries if s.layer == ContextLayer.BREADTH), None)

        if tech and breadth and tech.dominant_direction == ContextDirection.SUPPORTIVE and breadth.dominant_direction == ContextDirection.NEGATIVE:
            return ContextConflict(
                conflict_id=str(uuid.uuid4()),
                conflict_type=ConflictType.TECHNICAL_VS_BREADTH,
                symbol=tech.symbol,
                involved_layers=[ContextLayer.TECHNICAL_SIGNAL, ContextLayer.BREADTH],
                severity=ContextImportance.MEDIUM,
                score_impact=getattr(self.settings, "CONTEXT_CONFLICT_PENALTY_MEDIUM", 5.0),
                message="Technical signal is supportive but market breadth is negative.",
                suggested_review_reason="Check for broad market weakness."
            )
        return None

    def technical_vs_event(self, summaries: List[ContextLayerSummary]) -> Optional[ContextConflict]:
        tech = next((s for s in summaries if s.layer == ContextLayer.TECHNICAL_SIGNAL), None)
        event = next((s for s in summaries if s.layer == ContextLayer.EVENT_RISK), None)

        if tech and event and tech.dominant_direction == ContextDirection.SUPPORTIVE and event.dominant_direction == ContextDirection.NEGATIVE:
            return ContextConflict(
                conflict_id=str(uuid.uuid4()),
                conflict_type=ConflictType.TECHNICAL_VS_EVENT,
                symbol=tech.symbol,
                involved_layers=[ContextLayer.TECHNICAL_SIGNAL, ContextLayer.EVENT_RISK],
                severity=ContextImportance.HIGH,
                score_impact=getattr(self.settings, "CONTEXT_CONFLICT_PENALTY_HIGH", 10.0),
                message="Technical signal is supportive but critical event risk is present.",
                suggested_review_reason="Review upcoming events."
            )
        return None

    def ml_vs_strategy(self, summaries: List[ContextLayerSummary]) -> Optional[ContextConflict]:
        ml = next((s for s in summaries if s.layer == ContextLayer.ML), None)
        strat = next((s for s in summaries if s.layer == ContextLayer.STRATEGY_REGISTRY), None)

        if ml and strat and ml.dominant_direction != ContextDirection.UNKNOWN and strat.dominant_direction != ContextDirection.UNKNOWN and ml.dominant_direction != strat.dominant_direction:
            return ContextConflict(
                conflict_id=str(uuid.uuid4()),
                conflict_type=ConflictType.ML_VS_STRATEGY,
                symbol=ml.symbol or strat.symbol,
                involved_layers=[ContextLayer.ML, ContextLayer.STRATEGY_REGISTRY],
                severity=ContextImportance.MEDIUM,
                score_impact=getattr(self.settings, "CONTEXT_CONFLICT_PENALTY_MEDIUM", 5.0),
                message="ML prediction and Strategy scorecard are in disagreement.",
                suggested_review_reason="Check ML model alignment with strategy rules."
            )
        return None

    def calibration_mismatch(self, summaries: List[ContextLayerSummary]) -> Optional[ContextConflict]:
        tech = next((s for s in summaries if s.layer == ContextLayer.TECHNICAL_SIGNAL), None)
        cal = next((s for s in summaries if s.layer == ContextLayer.CALIBRATION), None)

        if tech and cal and tech.dominant_direction == ContextDirection.SUPPORTIVE and cal.dominant_direction == ContextDirection.NEGATIVE:
            return ContextConflict(
                conflict_id=str(uuid.uuid4()),
                conflict_type=ConflictType.CALIBRATION_MISMATCH,
                symbol=tech.symbol,
                involved_layers=[ContextLayer.TECHNICAL_SIGNAL, ContextLayer.CALIBRATION],
                severity=ContextImportance.MEDIUM,
                score_impact=getattr(self.settings, "CONTEXT_CONFLICT_PENALTY_MEDIUM", 5.0),
                message="Signal is supportive but historical calibration is weak.",
                suggested_review_reason="Check historical signal reliability."
            )
        return None

    def liquidity_cost_conflict(self, summaries: List[ContextLayerSummary]) -> Optional[ContextConflict]:
        tech = next((s for s in summaries if s.layer == ContextLayer.TECHNICAL_SIGNAL), None)
        exec_layer = next((s for s in summaries if s.layer == ContextLayer.EXECUTION), None)

        if tech and exec_layer and tech.dominant_direction == ContextDirection.SUPPORTIVE and exec_layer.dominant_direction == ContextDirection.NEGATIVE:
            return ContextConflict(
                conflict_id=str(uuid.uuid4()),
                conflict_type=ConflictType.LIQUIDITY_COST_CONFLICT,
                symbol=tech.symbol,
                involved_layers=[ContextLayer.TECHNICAL_SIGNAL, ContextLayer.EXECUTION],
                severity=ContextImportance.HIGH,
                score_impact=getattr(self.settings, "CONTEXT_CONFLICT_PENALTY_HIGH", 10.0),
                message="Supportive signal but execution cost/liquidity is poor.",
                suggested_review_reason="Review expected slippage and capacity."
            )
        return None

    def conflict_penalty(self, conflicts: List[ContextConflict]) -> float:
        return sum(c.score_impact or 0.0 for c in conflicts)
