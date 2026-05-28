import uuid
from collections import defaultdict
from datetime import datetime
from bist_signal_bot.breadth.models import BreadthInputRow, BreadthStatus, SectorBreadthSummary
from bist_signal_bot.config.settings import Settings

class SectorBreadthAnalyzer:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def analyze_by_sector(self, inputs: list[BreadthInputRow]) -> list[SectorBreadthSummary]:
        if not inputs:
            return []

        sector_groups = defaultdict(list)
        for row in inputs:
            sector = row.sector if row.sector else "UNKNOWN"
            sector_groups[sector].append(row)

        summaries = []
        for sector, sector_inputs in sector_groups.items():
            summaries.append(self.sector_summary(sector, sector_inputs))

        return summaries

    def sector_summary(self, sector: str, inputs: list[BreadthInputRow]) -> SectorBreadthSummary:
        as_of = inputs[0].as_of if inputs else datetime.now()
        count = len(inputs)
        warnings = []

        if count < self.settings.BREADTH_SECTOR_MIN_SYMBOLS:
            warnings.append(f"Sector {sector} has too few symbols ({count} < {self.settings.BREADTH_SECTOR_MIN_SYMBOLS})")

        advances = 0
        total_ad = 0
        above_50 = 0
        total_50 = 0
        above_200 = 0
        total_200 = 0
        up_vol = 0.0
        total_vol = 0.0

        for row in inputs:
            if row.close is not None and row.previous_close is not None:
                total_ad += 1
                if row.close > row.previous_close:
                    advances += 1

            if row.close is not None and row.ma_50 is not None:
                total_50 += 1
                if row.close > row.ma_50:
                    above_50 += 1

            if row.close is not None and row.ma_200 is not None:
                total_200 += 1
                if row.close > row.ma_200:
                    above_200 += 1

            if row.volume is not None and row.close is not None and row.previous_close is not None:
                total_vol += row.volume
                if row.close > row.previous_close:
                    up_vol += row.volume

        lead_lag = self.leading_lagging_symbols(inputs)

        summary = SectorBreadthSummary(
            sector_breadth_id=str(uuid.uuid4()),
            sector=sector,
            as_of=as_of,
            symbols_count=count,
            advance_percent=round((advances/total_ad)*100.0, 2) if total_ad > 0 else None,
            above_ma_50_pct=round((above_50/total_50)*100.0, 2) if total_50 > 0 else None,
            above_ma_200_pct=round((above_200/total_200)*100.0, 2) if total_200 > 0 else None,
            up_volume_ratio=round((up_vol/total_vol)*100.0, 2) if total_vol > 0 else None,
            leading_symbols=lead_lag["leading"],
            lagging_symbols=lead_lag["lagging"],
            warnings=warnings
        )

        summary.sector_breadth_score = self.sector_breadth_score(summary)
        summary.status = self.classify_sector(summary.sector_breadth_score)
        if count < self.settings.BREADTH_SECTOR_MIN_SYMBOLS:
            summary.status = BreadthStatus.INSUFFICIENT_DATA

        return summary

    def leading_lagging_symbols(self, inputs: list[BreadthInputRow], top_n: int = 5) -> dict[str, list[str]]:
        valid_inputs = [row for row in inputs if row.return_1d_pct is not None]
        sorted_inputs = sorted(valid_inputs, key=lambda x: x.return_1d_pct, reverse=True)

        leading = [row.symbol for row in sorted_inputs[:top_n]]
        lagging = [row.symbol for row in sorted_inputs[-top_n:]]
        lagging.reverse() # Most negative first

        return {"leading": leading, "lagging": lagging}

    def sector_breadth_score(self, summary: SectorBreadthSummary) -> float | None:
        scores = []
        if summary.advance_percent is not None: scores.append(summary.advance_percent)
        if summary.above_ma_50_pct is not None: scores.append(summary.above_ma_50_pct)
        if summary.up_volume_ratio is not None: scores.append(summary.up_volume_ratio)

        if not scores:
            return None
        return round(sum(scores) / len(scores), 2)

    def classify_sector(self, score: float | None) -> BreadthStatus:
        if score is None:
            return BreadthStatus.UNKNOWN
        if score >= self.settings.BREADTH_SECTOR_LEADING_THRESHOLD:
            return BreadthStatus.STRONG
        elif score >= 50.0:
            return BreadthStatus.POSITIVE
        elif score <= self.settings.BREADTH_SECTOR_LAGGING_THRESHOLD:
            return BreadthStatus.WEAK
        elif score <= 45.0:
            return BreadthStatus.NEGATIVE
        return BreadthStatus.NEUTRAL
