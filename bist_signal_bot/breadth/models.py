from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

class BreadthStatus(str, Enum):
    STRONG = "STRONG"
    HEALTHY = "HEALTHY"
    NEUTRAL = "NEUTRAL"
    WEAK = "WEAK"
    STRESSED = "STRESSED"
    UNKNOWN = "UNKNOWN"

class BreadthMetricType(str, Enum):
    ADVANCE_DECLINE = "ADVANCE_DECLINE"
    PERCENT_ABOVE_MA = "PERCENT_ABOVE_MA"
    NEW_HIGH_LOW = "NEW_HIGH_LOW"
    VOLUME_BREADTH = "VOLUME_BREADTH"
    MOMENTUM_BREADTH = "MOMENTUM_BREADTH"
    RELATIVE_STRENGTH = "RELATIVE_STRENGTH"
    SECTOR_ROTATION = "SECTOR_ROTATION"
    CROSS_SECTIONAL_RANK = "CROSS_SECTIONAL_RANK"
    COMPOSITE = "COMPOSITE"

class RelativeStrengthMode(str, Enum):
    VS_BENCHMARK = "VS_BENCHMARK"
    VS_SECTOR = "VS_SECTOR"
    VS_UNIVERSE = "VS_UNIVERSE"
    ABSOLUTE_MOMENTUM = "ABSOLUTE_MOMENTUM"
    COMPOSITE = "COMPOSITE"

class SectorRotationStatus(str, Enum):
    LEADING = "LEADING"
    IMPROVING = "IMPROVING"
    WEAKENING = "WEAKENING"
    LAGGING = "LAGGING"
    NEUTRAL = "NEUTRAL"
    UNKNOWN = "UNKNOWN"

class RankingDirection(str, Enum):
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    LOWER_IS_BETTER = "LOWER_IS_BETTER"

class BreadthMetric(BaseModel):
    metric_name: str
    metric_type: BreadthMetricType
    value: float | int | str | None = None
    status: BreadthStatus = BreadthStatus.UNKNOWN
    threshold: float | None = None
    sample_size: int = 0
    as_of_date: datetime
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class BreadthSnapshot(BaseModel):
    snapshot_id: str
    as_of_date: datetime
    universe_name: str
    symbols: list[str]
    benchmark_symbol: str | None = None
    metrics: list[BreadthMetric] = Field(default_factory=list)
    advance_count: int | None = None
    decline_count: int | None = None
    unchanged_count: int | None = None
    percent_above_ma: dict[str, float] = Field(default_factory=dict)
    new_high_count: dict[str, int] = Field(default_factory=dict)
    new_low_count: dict[str, int] = Field(default_factory=dict)
    volume_breadth_score: float | None = None
    momentum_breadth_score: float | None = None
    composite_score: float = 0.0
    status: BreadthStatus = BreadthStatus.UNKNOWN
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Breadth snapshot is research-only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "as_of_date": self.as_of_date.isoformat(),
            "universe_name": self.universe_name,
            "symbols_count": len(self.symbols),
            "benchmark_symbol": self.benchmark_symbol,
            "composite_score": self.composite_score,
            "status": self.status.value,
            "warnings_count": len(self.warnings),
        }

    def safe_public_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "as_of_date": self.as_of_date.isoformat(),
            "universe_name": self.universe_name,
            "symbols_count": len(self.symbols),
            "benchmark_symbol": self.benchmark_symbol,
            "composite_score": self.composite_score,
            "status": self.status.value,
            "advance_count": self.advance_count,
            "decline_count": self.decline_count,
            "percent_above_ma": self.percent_above_ma,
            "new_high_count": self.new_high_count,
            "new_low_count": self.new_low_count,
            "volume_breadth_score": self.volume_breadth_score,
            "disclaimer": self.disclaimer
        }

class RelativeStrengthScore(BaseModel):
    symbol: str
    benchmark_symbol: str | None = None
    sector: str | None = None
    as_of_date: datetime
    rs_20: float | None = None
    rs_50: float | None = None
    rs_100: float | None = None
    rs_200: float | None = None
    absolute_momentum_score: float | None = None
    relative_momentum_score: float | None = None
    percentile_rank: float | None = None
    composite_score: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class SectorRotationScore(BaseModel):
    sector: str
    as_of_date: datetime
    symbol_count: int = 0
    average_return_20: float | None = None
    average_return_50: float | None = None
    average_rs_score: float | None = None
    breadth_score: float | None = None
    fundamental_composite_avg: float | None = None
    momentum_score: float | None = None
    rotation_status: SectorRotationStatus = SectorRotationStatus.UNKNOWN
    rank: int | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class CrossSectionalRankItem(BaseModel):
    symbol: str
    as_of_date: datetime
    rank: int
    percentile: float
    composite_score: float
    components: dict[str, float | None] = Field(default_factory=dict)
    sector: str | None = None
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class BreadthRegime(BaseModel):
    as_of_date: datetime
    status: BreadthStatus
    composite_score: float
    risk_modifier: float
    signal_policy: str
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class BreadthAnalysisRequest(BaseModel):
    symbols: list[str]
    benchmark_symbol: str | None = None
    universe_name: str
    source: str
    timeframe: str
    as_of_date: datetime | None = None
    lookback_days: int = 260
    include_relative_strength: bool = True
    include_sector_rotation: bool = True
    include_fundamentals: bool = False
    save_snapshot: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

class BreadthAnalysisResult(BaseModel):
    request: BreadthAnalysisRequest
    snapshot: BreadthSnapshot
    relative_strength_scores: list[RelativeStrengthScore] = Field(default_factory=list)
    sector_rotation_scores: list[SectorRotationScore] = Field(default_factory=list)
    cross_sectional_ranking: list[CrossSectionalRankItem] = Field(default_factory=list)
    regime: BreadthRegime | None = None
    output_files: dict[str, str] = Field(default_factory=dict)
    elapsed_seconds: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    disclaimer: str = "Breadth analysis output only. Not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "request_universe": self.request.universe_name,
            "snapshot_id": self.snapshot.snapshot_id,
            "composite_score": self.snapshot.composite_score,
            "status": self.snapshot.status.value,
            "regime_status": self.regime.status.value if self.regime else None,
            "rs_count": len(self.relative_strength_scores),
            "sector_count": len(self.sector_rotation_scores),
            "rank_count": len(self.cross_sectional_ranking),
            "elapsed_seconds": self.elapsed_seconds,
            "warnings_count": len(self.warnings),
        }
