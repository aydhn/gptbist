from datetime import datetime
from typing import Any
from collections import defaultdict

from bist_signal_bot.breadth.models import SectorRotationScore, RelativeStrengthScore, SectorRotationStatus

class SectorRotationAnalyzer:
    def __init__(self, settings=None):
        self.settings = settings

    def calculate_sector_rotation(self, relative_scores: list[RelativeStrengthScore], sectors: dict[str, str], fundamentals: dict[str, Any] | None = None) -> list[SectorRotationScore]:
        sector_map = defaultdict(list)
        for score in relative_scores:
            s_name = sectors.get(score.symbol, "UNKNOWN")
            sector_map[s_name].append(score)

        results = []
        for s_name, s_scores in sector_map.items():
            valid_20 = [x.rs_20 for x in s_scores if x.rs_20 is not None]
            valid_50 = [x.rs_50 for x in s_scores if x.rs_50 is not None]
            valid_comp = [x.composite_score for x in s_scores if x.composite_score is not None]

            avg_20 = sum(valid_20) / len(valid_20) if valid_20 else None
            avg_50 = sum(valid_50) / len(valid_50) if valid_50 else None
            avg_rs = sum(valid_comp) / len(valid_comp) if valid_comp else None

            status = self.classify_rotation_status(avg_20, avg_50, avg_rs)

            as_of_date = s_scores[0].as_of_date if s_scores else datetime.now()

            res = SectorRotationScore(
                sector=s_name,
                as_of_date=as_of_date,
                symbol_count=len(s_scores),
                average_return_20=avg_20,
                average_return_50=avg_50,
                average_rs_score=avg_rs,
                rotation_status=status
            )
            results.append(res)

        return self.rank_sectors(results)

    def classify_rotation_status(self, momentum_score: float | None, breadth_score: float | None, rs_score: float | None) -> SectorRotationStatus:
        if rs_score is None:
            return SectorRotationStatus.UNKNOWN
        if rs_score >= 70:
            return SectorRotationStatus.LEADING
        if rs_score >= 50:
            return SectorRotationStatus.IMPROVING
        if rs_score >= 30:
            return SectorRotationStatus.WEAKENING
        return SectorRotationStatus.LAGGING

    def rank_sectors(self, scores: list[SectorRotationScore]) -> list[SectorRotationScore]:
        sorted_scores = sorted(scores, key=lambda x: (x.average_rs_score or 0.0, x.sector), reverse=True)
        for i, s in enumerate(sorted_scores):
            s.rank = i + 1
        return sorted_scores

    def sector_leaders(self, scores: list[SectorRotationScore], top_n: int = 5) -> list[SectorRotationScore]:
        ranked = self.rank_sectors(scores)
        return ranked[:top_n]

    def sector_laggards(self, scores: list[SectorRotationScore], top_n: int = 5) -> list[SectorRotationScore]:
        ranked = self.rank_sectors(scores)
        return ranked[-top_n:]
