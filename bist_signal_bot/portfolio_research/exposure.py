from typing import Any
from collections import defaultdict
from bist_signal_bot.portfolio_research.models import (
    ResearchPortfolioItem,
    PortfolioResearchRequest,
    ExposureGroup,
    PortfolioExposureBucket,
    PortfolioConstraintStatus
)

class PortfolioExposureAnalyzer:

    def calculate_exposures(self, items: list[ResearchPortfolioItem]) -> list[PortfolioExposureBucket]:
        exposures = []
        for group in ExposureGroup:
            buckets = self.bucket_by_group(items, group)
            exposures.extend(buckets)
        return exposures

    def bucket_by_group(self, items: list[ResearchPortfolioItem], group: ExposureGroup) -> list[PortfolioExposureBucket]:
        mapping = defaultdict(lambda: {"weight": 0.0, "symbols": []})

        for item in items:
            if item.final_weight <= 0:
                continue

            key = "UNKNOWN"
            if group == ExposureGroup.SYMBOL:
                key = item.symbol
            elif group == ExposureGroup.SECTOR:
                key = item.sector or "UNKNOWN"
            elif group == ExposureGroup.INDUSTRY:
                key = item.industry or "UNKNOWN"
            elif group == ExposureGroup.STRATEGY:
                key = item.strategy_name or "UNKNOWN"
            elif group == ExposureGroup.SIGNAL_SOURCE:
                key = item.source_type or "UNKNOWN"
            # Add other groups as needed

            mapping[key]["weight"] += item.final_weight
            mapping[key]["symbols"].append(item.symbol)

        buckets = []
        for key, data in mapping.items():
            buckets.append(PortfolioExposureBucket(
                group=group,
                key=key,
                weight=data["weight"],
                item_count=len(data["symbols"]),
                symbols=data["symbols"]
            ))

        return buckets

    def exposure_warnings(self, exposures: list[PortfolioExposureBucket], request: PortfolioResearchRequest) -> list[str]:
        warnings = []
        for b in exposures:
            if b.group == ExposureGroup.SECTOR and b.weight > request.max_sector_weight:
                warnings.append(f"Sector {b.key} exposure ({b.weight:.2f}) exceeds limit ({request.max_sector_weight})")
            elif b.group == ExposureGroup.STRATEGY and b.weight > request.max_strategy_weight:
                warnings.append(f"Strategy {b.key} exposure ({b.weight:.2f}) exceeds limit ({request.max_strategy_weight})")
        return warnings

    def top_exposures(self, exposures: list[PortfolioExposureBucket], group: ExposureGroup, top_n: int = 10) -> list[PortfolioExposureBucket]:
        filtered = [b for b in exposures if b.group == group]
        filtered.sort(key=lambda x: x.weight, reverse=True)
        return filtered[:top_n]
