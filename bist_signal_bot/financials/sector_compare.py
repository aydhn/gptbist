import uuid
from datetime import datetime
import statistics
from bist_signal_bot.financials.models import (
    NormalizedFinancialStatement,
    FinancialRatio,
    SectorFinancialComparison,
    FinancialQualityStatus
)

class SectorFinancialComparator:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def compare_symbol(self, symbol: str, statements: list[NormalizedFinancialStatement], ratios_by_symbol: dict[str, list[FinancialRatio]]) -> SectorFinancialComparison:
        # Mock sector for now
        sector = "MOCK_SECTOR"

        symbol_ratios = ratios_by_symbol.get(symbol, [])
        medians = self.sector_medians(sector, ratios_by_symbol)

        ranks = {}
        for r in symbol_ratios:
            peers = []
            for sym, s_ratios in ratios_by_symbol.items():
                for sr in s_ratios:
                    if sr.name == r.name and sr.value is not None:
                        peers.append(sr.value)
            ranks[r.name] = self.percentile_rank(r.value, peers)

        sw = self.relative_strengths_weaknesses(symbol_ratios, medians)
        score = self.sector_score(ranks)

        return SectorFinancialComparison(
            comparison_id=str(uuid.uuid4()),
            symbol=symbol,
            period_end=datetime.now(),
            ratios=symbol_ratios,
            sector_medians=medians,
            percentile_ranks=ranks,
            relative_strengths=sw.get("strengths", []),
            relative_weaknesses=sw.get("weaknesses", []),
            status=FinancialQualityStatus.UNKNOWN,
            warnings=[],
            metadata={},
            sector=sector,
            sector_score=score
        )

    def sector_medians(self, sector: str, ratios_by_symbol: dict[str, list[FinancialRatio]]) -> dict[str, float | None]:
        medians = {}
        # Aggregate by name
        values_by_name = {}
        for sym, ratios in ratios_by_symbol.items():
            for r in ratios:
                if r.value is not None:
                    if r.name not in values_by_name:
                        values_by_name[r.name] = []
                    values_by_name[r.name].append(r.value)

        for name, vals in values_by_name.items():
            if vals:
                medians[name] = statistics.median(vals)
        return medians

    def percentile_rank(self, value: float | None, peers: list[float]) -> float | None:
        if value is None or not peers:
            return None
        less_than = sum(1 for p in peers if p < value)
        return (less_than / len(peers)) * 100

    def relative_strengths_weaknesses(self, symbol_ratios: list[FinancialRatio], medians: dict[str, float | None]) -> dict[str, list[str]]:
        strengths = []
        weaknesses = []

        for r in symbol_ratios:
            med = medians.get(r.name)
            if r.value is not None and med is not None:
                # Basic mock logic
                if r.value > med * 1.2:
                    strengths.append(f"{r.name} above sector median")
                elif r.value < med * 0.8:
                    weaknesses.append(f"{r.name} below sector median")

        return {"strengths": strengths, "weaknesses": weaknesses}

    def sector_score(self, percentile_ranks: dict[str, float | None]) -> float | None:
        valid = [v for v in percentile_ranks.values() if v is not None]
        if not valid:
            return None
        return sum(valid) / len(valid)
