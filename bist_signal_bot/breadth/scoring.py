from bist_signal_bot.breadth.models import (
    AdvanceDeclineSummary, BreadthReport, HighLowBreadthSummary, ParticipationSummary,
    SectorBreadthSummary, VolumeBreadthSummary
)
from bist_signal_bot.config.settings import Settings

class BreadthScorer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def score_report(self, report: BreadthReport) -> float | None:
        parts = {
            "ad": self.score_advance_decline(report.advance_decline),
            "part": self.score_participation(report.participation),
            "hl": self.score_high_low(report.high_low),
            "vol": self.score_volume(report.volume_breadth),
            "sec": self.score_sector_confirmation(report.sector_breadth)
        }

        base_score = self.combine_scores(parts)
        if base_score is None:
            return None

        # Apply divergence penalty
        if report.divergences:
            penalty = 0
            for div in report.divergences:
                if div.divergence_score and div.divergence_score >= self.settings.BREADTH_DIVERGENCE_WARN_SCORE:
                    penalty += 10.0
            base_score = max(0.0, base_score - penalty)

        return round(base_score, 2)

    def score_advance_decline(self, summary: AdvanceDeclineSummary | None) -> float | None:
        if not summary or summary.advance_percent is None:
            return None
        return summary.advance_percent

    def score_participation(self, summary: ParticipationSummary | None) -> float | None:
        if not summary or summary.participation_score is None:
            return None
        return summary.participation_score

    def score_high_low(self, summary: HighLowBreadthSummary | None) -> float | None:
        if not summary or summary.high_low_score is None:
            return None
        return summary.high_low_score

    def score_volume(self, summary: VolumeBreadthSummary | None) -> float | None:
        if not summary or summary.volume_breadth_score is None:
            return None
        return summary.volume_breadth_score

    def score_sector_confirmation(self, sector_breadth: list[SectorBreadthSummary]) -> float | None:
        if not sector_breadth:
            return None
        scores = [s.sector_breadth_score for s in sector_breadth if s.sector_breadth_score is not None]
        if not scores:
            return None
        return round(sum(scores) / len(scores), 2)

    def combine_scores(self, parts: dict[str, float | None]) -> float | None:
        valid_scores = [score for score in parts.values() if score is not None]
        if not valid_scores:
            return None
        return sum(valid_scores) / len(valid_scores)
