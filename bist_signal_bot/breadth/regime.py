from datetime import datetime

from bist_signal_bot.breadth.models import BreadthRegime, BreadthSnapshot, SectorRotationScore, BreadthStatus

class BreadthRegimeClassifier:
    def __init__(self, settings=None):
        self.settings = settings

        self.strong_threshold = getattr(settings, "BREADTH_STRONG_THRESHOLD", 75.0) if settings else 75.0
        self.healthy_threshold = getattr(settings, "BREADTH_HEALTHY_THRESHOLD", 60.0) if settings else 60.0
        self.neutral_threshold = getattr(settings, "BREADTH_NEUTRAL_THRESHOLD", 45.0) if settings else 45.0
        self.weak_threshold = getattr(settings, "BREADTH_WEAK_THRESHOLD", 30.0) if settings else 30.0

    def classify(self, snapshot: BreadthSnapshot, sector_scores: list[SectorRotationScore] | None = None) -> BreadthRegime:
        comp_score = snapshot.composite_score

        if comp_score >= self.strong_threshold:
            status = BreadthStatus.STRONG
            policy = "normal_research"
        elif comp_score >= self.healthy_threshold:
            status = BreadthStatus.HEALTHY
            policy = "normal_research"
        elif comp_score >= self.neutral_threshold:
            status = BreadthStatus.NEUTRAL
            policy = "selective_research"
        elif comp_score >= self.weak_threshold:
            status = BreadthStatus.WEAK
            policy = "cautious_research"
        else:
            status = BreadthStatus.STRESSED
            policy = "watch_only_research"

        regime = BreadthRegime(
            as_of_date=snapshot.as_of_date,
            status=status,
            composite_score=comp_score,
            risk_modifier=self.risk_modifier_for_status(status),
            signal_policy=policy,
            reasons=self.build_reasons(snapshot, sector_scores)
        )
        return regime

    def build_reasons(self, snapshot: BreadthSnapshot, sector_scores: list[SectorRotationScore] | None) -> list[str]:
        reasons = []
        reasons.append(f"Composite score is {snapshot.composite_score:.1f}")
        adv = snapshot.advance_count or 0
        dec = snapshot.decline_count or 0
        tot = adv + dec
        if tot > 0:
            reasons.append(f"Advance/Decline ratio is {adv/tot:.2f}")

        if sector_scores:
            leaders = [s.sector for s in sector_scores if s.rotation_status.value == "LEADING"]
            if leaders:
                reasons.append(f"Leading sectors: {', '.join(leaders[:3])}")
        return reasons

    def risk_modifier_for_status(self, status: BreadthStatus) -> float:
        mapping = {
            BreadthStatus.STRONG: 1.00,
            BreadthStatus.HEALTHY: 0.90,
            BreadthStatus.NEUTRAL: 0.75,
            BreadthStatus.WEAK: 0.50,
            BreadthStatus.STRESSED: 0.25,
            BreadthStatus.UNKNOWN: 0.50,
        }
        return mapping.get(status, 0.50)
