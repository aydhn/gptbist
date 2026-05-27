import uuid
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.valuation.models import (
    ValuationRiskAssessment, ValuationRiskLevel, ValuationStatus,
    ValuationMultiple, ValuationBand, PeerValuationComparison
)
from bist_signal_bot.valuation.scoring import ValuationScorer

class ValuationRiskEngine:
    def __init__(self, settings: Optional[Settings] = None, scorer: Optional[ValuationScorer] = None):
        self.settings = settings or Settings()
        self.scorer = scorer or ValuationScorer(self.settings)
        self.expensive_threshold = getattr(self.settings, "VALUATION_EXPENSIVE_RISK_THRESHOLD", 75.0)
        self.value_trap_threshold = getattr(self.settings, "VALUATION_VALUE_TRAP_QUALITY_THRESHOLD", 40.0)

    def expensive_metric_flags(self, bands: List[ValuationBand], peers: List[PeerValuationComparison]) -> List[str]:
        flags = []
        for b in bands:
            if b.status in [ValuationStatus.EXPENSIVE, ValuationStatus.EXTREME_EXPENSIVE]:
                flags.append(f"{b.metric_type.value} is historically {b.status.value.lower()}")
        for p in peers:
            if p.status in [ValuationStatus.EXPENSIVE, ValuationStatus.EXTREME_EXPENSIVE]:
                flags.append(f"{p.metric_type.value} is {p.status.value.lower()} relative to peers")
        return flags

    def cheap_metric_flags(self, bands: List[ValuationBand], peers: List[PeerValuationComparison]) -> List[str]:
        flags = []
        for b in bands:
            if b.status in [ValuationStatus.CHEAP, ValuationStatus.EXTREME_CHEAP]:
                flags.append(f"{b.metric_type.value} is historically {b.status.value.lower()}")
        for p in peers:
            if p.status in [ValuationStatus.CHEAP, ValuationStatus.EXTREME_CHEAP]:
                flags.append(f"{p.metric_type.value} is {p.status.value.lower()} relative to peers")
        return flags

    def data_quality_warnings(self, multiples: List[ValuationMultiple], bands: List[ValuationBand], peers: List[PeerValuationComparison]) -> List[str]:
        warnings = []
        for item_list in [multiples, bands, peers]:
            for item in item_list:
                if item.warnings:
                    warnings.extend(item.warnings)
                if item.status == ValuationStatus.WATCH:
                    warnings.append(f"WATCH status flagged for {item.metric_type.value}")
        return list(set(warnings))

    def risk_level(self, score: Optional[float], warnings: List[str], earnings_quality: Optional[Dict] = None) -> ValuationRiskLevel:
        if score is None:
            return ValuationRiskLevel.INSUFFICIENT_DATA

        if score >= self.expensive_threshold:
            if any("EXTREME_EXPENSIVE" in w for w in warnings):
                return ValuationRiskLevel.EXTREME
            return ValuationRiskLevel.HIGH

        if score <= 25.0: # Cheap territory
            eq_score = earnings_quality.get("score", 50.0) if earnings_quality else 50.0
            if eq_score < self.value_trap_threshold:
                # Value Trap Risk
                return ValuationRiskLevel.HIGH
            return ValuationRiskLevel.LOW

        return ValuationRiskLevel.MEDIUM

    def assess(self, symbol: str, multiples: List[ValuationMultiple], bands: List[ValuationBand],
               peers: List[PeerValuationComparison], earnings_quality: Optional[Dict] = None) -> ValuationRiskAssessment:

        score = self.scorer.score_valuation(multiples, bands, peers, earnings_quality)
        expensive_flags = self.expensive_metric_flags(bands, peers)
        cheap_flags = self.cheap_metric_flags(bands, peers)
        data_warnings = self.data_quality_warnings(multiples, bands, peers)

        level = self.risk_level(score, expensive_flags + cheap_flags, earnings_quality)

        decision = "HOLD/NEUTRAL"
        if level == ValuationRiskLevel.EXTREME:
             decision = "REDUCE EXPOSURE (Extreme Valuation Risk)"
        elif level == ValuationRiskLevel.HIGH and score is not None and score <= 25.0:
             decision = "CAUTION (Value Trap Risk - Cheap but Weak Quality)"
        elif level == ValuationRiskLevel.LOW:
             decision = "MONITOR (Favorable Valuation)"

        warnings = []
        if not multiples:
            warnings.append("No multiples available for risk assessment.")
            level = ValuationRiskLevel.INSUFFICIENT_DATA
            decision = "INSUFFICIENT_DATA"

        return ValuationRiskAssessment(
            assessment_id=str(uuid.uuid4()),
            symbol=symbol,
            as_of=datetime.utcnow(),
            valuation_score=score,
            valuation_risk_level=level,
            expensive_metrics=expensive_flags,
            cheap_metrics=cheap_flags,
            data_quality_warnings=data_warnings,
            earnings_quality_context=earnings_quality or {},
            recommended_decision=decision,
            warnings=warnings
        )
