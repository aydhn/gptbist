import uuid
from datetime import datetime
from bist_signal_bot.breadth.models import (
    AdvanceDeclineSummary, BreadthDivergence, BreadthRegimeLabel, BreadthRegimeSnapshot,
    BreadthReport, BreadthStatus, ParticipationSummary, SectorBreadthSummary, VolumeBreadthSummary
)
from bist_signal_bot.config.settings import Settings

class BreadthRegimeClassifier:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def classify(self, report: BreadthReport) -> BreadthRegimeSnapshot:
        ad = report.advance_decline
        part = report.participation
        vol = report.volume_breadth
        divs = report.divergences
        sectors = report.sector_breadth

        label = self.label_from_components(ad, part, vol, divs)

        b_score = self.breadth_score(report)
        part_score = part.participation_score if part else None
        vol_score = vol.volume_breadth_score if vol else None

        max_div_score = max([d.divergence_score for d in divs if d.divergence_score is not None], default=None) if divs else None
        sec_score = self.sector_confirmation_score(sectors)

        status = self.status_from_label(label, b_score)

        return BreadthRegimeSnapshot(
            regime_id=str(uuid.uuid4()),
            as_of=report.generated_at,
            scope=report.scope,
            scope_name=report.scope_name,
            label=label,
            breadth_score=b_score,
            participation_score=part_score,
            volume_breadth_score=vol_score,
            divergence_score=max_div_score,
            sector_confirmation_score=sec_score,
            status=status
        )

    def label_from_components(self, advance_decline: AdvanceDeclineSummary | None, participation: ParticipationSummary | None, volume_breadth: VolumeBreadthSummary | None, divergences: list[BreadthDivergence]) -> BreadthRegimeLabel:
        if not advance_decline or not participation:
            return BreadthRegimeLabel.INSUFFICIENT_DATA

        if divergences:
            return BreadthRegimeLabel.DIVERGENCE_WARNING

        ad_ratio = advance_decline.advance_decline_ratio or 1.0
        part_score = participation.participation_score or 50.0

        if ad_ratio >= 1.5 and part_score >= 60.0:
            return BreadthRegimeLabel.BROAD_ADVANCE
        elif ad_ratio >= 1.0 and part_score < 40.0:
            return BreadthRegimeLabel.NARROW_ADVANCE
        elif ad_ratio <= 0.7 and part_score <= 40.0:
            return BreadthRegimeLabel.BROAD_DECLINE
        elif ad_ratio <= 1.0 and part_score > 60.0:
            return BreadthRegimeLabel.NARROW_DECLINE
        elif part_score < 30.0:
            return BreadthRegimeLabel.LOW_PARTICIPATION

        return BreadthRegimeLabel.MIXED

    def sector_confirmation_score(self, sector_breadth: list[SectorBreadthSummary]) -> float | None:
        if not sector_breadth:
            return None
        valid_scores = [s.sector_breadth_score for s in sector_breadth if s.sector_breadth_score is not None]
        if not valid_scores:
            return None
        return round(sum(valid_scores) / len(valid_scores), 2)

    def breadth_score(self, report: BreadthReport) -> float | None:
        # Avoid circular import, we'll implement a basic one here or use BreadthScorer later
        # We'll just do a simple average of AD, Part, and Vol here to get it working
        scores = []
        if report.advance_decline and report.advance_decline.advance_percent is not None:
            scores.append(report.advance_decline.advance_percent)
        if report.participation and report.participation.participation_score is not None:
            scores.append(report.participation.participation_score)
        if report.volume_breadth and report.volume_breadth.volume_breadth_score is not None:
            scores.append(report.volume_breadth.volume_breadth_score)

        if not scores:
            return None
        return round(sum(scores) / len(scores), 2)

    def status_from_label(self, label: BreadthRegimeLabel, score: float | None) -> BreadthStatus:
        if label == BreadthRegimeLabel.BROAD_ADVANCE:
            return BreadthStatus.STRONG
        elif label == BreadthRegimeLabel.NARROW_ADVANCE:
            return BreadthStatus.WATCH
        elif label == BreadthRegimeLabel.BROAD_DECLINE:
            return BreadthStatus.WEAK
        elif label == BreadthRegimeLabel.NARROW_DECLINE:
            return BreadthStatus.WATCH
        elif label == BreadthRegimeLabel.DIVERGENCE_WARNING:
            return BreadthStatus.DIVERGENT
        elif label == BreadthRegimeLabel.LOW_PARTICIPATION:
            return BreadthStatus.NEGATIVE
        elif label == BreadthRegimeLabel.INSUFFICIENT_DATA:
            return BreadthStatus.INSUFFICIENT_DATA
        return BreadthStatus.NEUTRAL
