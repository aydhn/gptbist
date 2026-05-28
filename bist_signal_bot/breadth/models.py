from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class BreadthStatus(Enum):
    STRONG = "STRONG"
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    WEAK = "WEAK"
    DIVERGENT = "DIVERGENT"
    WATCH = "WATCH"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class BreadthScope(Enum):
    MARKET = "MARKET"
    INDEX = "INDEX"
    SECTOR = "SECTOR"
    UNIVERSE = "UNIVERSE"
    PORTFOLIO = "PORTFOLIO"
    CUSTOM = "CUSTOM"
    UNKNOWN = "UNKNOWN"


class BreadthMetricType(Enum):
    ADVANCE_DECLINE_RATIO = "ADVANCE_DECLINE_RATIO"
    NET_ADVANCES = "NET_ADVANCES"
    ADVANCE_PERCENT = "ADVANCE_PERCENT"
    ABOVE_MA_20 = "ABOVE_MA_20"
    ABOVE_MA_50 = "ABOVE_MA_50"
    ABOVE_MA_200 = "ABOVE_MA_200"
    NEW_HIGH_20D = "NEW_HIGH_20D"
    NEW_LOW_20D = "NEW_LOW_20D"
    NEW_HIGH_52W = "NEW_HIGH_52W"
    NEW_LOW_52W = "NEW_LOW_52W"
    UP_VOLUME_RATIO = "UP_VOLUME_RATIO"
    DOWN_VOLUME_RATIO = "DOWN_VOLUME_RATIO"
    VOLUME_BREADTH = "VOLUME_BREADTH"
    PARTICIPATION_SCORE = "PARTICIPATION_SCORE"
    BREADTH_THRUST = "BREADTH_THRUST"
    DIVERGENCE_SCORE = "DIVERGENCE_SCORE"
    SECTOR_BREADTH_SCORE = "SECTOR_BREADTH_SCORE"
    CUSTOM = "CUSTOM"


class BreadthRegimeLabel(Enum):
    BROAD_ADVANCE = "BROAD_ADVANCE"
    NARROW_ADVANCE = "NARROW_ADVANCE"
    BROAD_DECLINE = "BROAD_DECLINE"
    NARROW_DECLINE = "NARROW_DECLINE"
    MIXED = "MIXED"
    DIVERGENCE_WARNING = "DIVERGENCE_WARNING"
    LOW_PARTICIPATION = "LOW_PARTICIPATION"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"


class BreadthDivergenceType(Enum):
    INDEX_UP_BREADTH_DOWN = "INDEX_UP_BREADTH_DOWN"
    INDEX_DOWN_BREADTH_UP = "INDEX_DOWN_BREADTH_UP"
    PRICE_NEW_HIGH_BREADTH_NOT_CONFIRMING = "PRICE_NEW_HIGH_BREADTH_NOT_CONFIRMING"
    PRICE_NEW_LOW_BREADTH_NOT_CONFIRMING = "PRICE_NEW_LOW_BREADTH_NOT_CONFIRMING"
    SECTOR_DIVERGENCE = "SECTOR_DIVERGENCE"
    VOLUME_DIVERGENCE = "VOLUME_DIVERGENCE"
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"


@dataclass
class BreadthUniverseSnapshot:
    universe_id: str
    name: str
    as_of: datetime
    scope: BreadthScope
    symbols: list[str]
    sectors: dict[str, str]
    active_count: int
    excluded_symbols: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.symbols = [s.upper() for s in self.symbols]
        self.active_count = max(0, self.active_count)
        if self.active_count == 0 and "Empty universe" not in self.warnings:
            self.warnings.append("Empty universe")


@dataclass
class BreadthInputRow:
    row_id: str
    symbol: str
    as_of: datetime
    sector: str | None = None
    close: float | None = None
    previous_close: float | None = None
    volume: float | None = None
    turnover: float | None = None
    ma_20: float | None = None
    ma_50: float | None = None
    ma_200: float | None = None
    high_20d: float | None = None
    low_20d: float | None = None
    high_252d: float | None = None
    low_252d: float | None = None
    return_1d_pct: float | None = None
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.symbol = self.symbol.upper()
        if self.close is not None and self.close < 0:
            self.warnings.append(f"Negative close price for {self.symbol}")
        if self.volume is not None and self.volume < 0:
            self.warnings.append(f"Negative volume for {self.symbol}")


@dataclass
class BreadthMetric:
    metric_id: str
    metric_type: BreadthMetricType
    scope: BreadthScope
    scope_name: str
    as_of: datetime
    value: float | None = None
    numerator: float | None = None
    denominator: float | None = None
    status: BreadthStatus = BreadthStatus.UNKNOWN
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AdvanceDeclineSummary:
    summary_id: str
    scope: BreadthScope
    scope_name: str
    as_of: datetime
    advances: int
    declines: int
    unchanged: int
    net_advances: int
    advance_decline_ratio: float | None = None
    advance_percent: float | None = None
    status: BreadthStatus = BreadthStatus.UNKNOWN
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Advance/decline summary is research-only market breadth metadata. It is not investment advice. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParticipationSummary:
    participation_id: str
    scope: BreadthScope
    scope_name: str
    as_of: datetime
    above_ma_20_pct: float | None = None
    above_ma_50_pct: float | None = None
    above_ma_200_pct: float | None = None
    positive_return_pct: float | None = None
    participation_score: float | None = None
    breadth_thrust_score: float | None = None
    status: BreadthStatus = BreadthStatus.UNKNOWN
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Participation summary is research-only market breadth metadata. It is not investment advice. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HighLowBreadthSummary:
    highlow_id: str
    scope: BreadthScope
    scope_name: str
    as_of: datetime
    new_high_20d_count: int
    new_low_20d_count: int
    new_high_52w_count: int
    new_low_52w_count: int
    high_low_spread: int
    high_low_score: float | None = None
    status: BreadthStatus = BreadthStatus.UNKNOWN
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class VolumeBreadthSummary:
    volume_breadth_id: str
    scope: BreadthScope
    scope_name: str
    as_of: datetime
    up_volume: float | None = None
    down_volume: float | None = None
    unchanged_volume: float | None = None
    up_volume_ratio: float | None = None
    down_volume_ratio: float | None = None
    volume_breadth_score: float | None = None
    status: BreadthStatus = BreadthStatus.UNKNOWN
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SectorBreadthSummary:
    sector_breadth_id: str
    sector: str
    as_of: datetime
    symbols_count: int
    advance_percent: float | None = None
    above_ma_50_pct: float | None = None
    above_ma_200_pct: float | None = None
    up_volume_ratio: float | None = None
    sector_breadth_score: float | None = None
    status: BreadthStatus = BreadthStatus.UNKNOWN
    leading_symbols: list[str] = field(default_factory=list)
    lagging_symbols: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Sector breadth summary is research-only metadata. It is not investment advice. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BreadthDivergence:
    divergence_id: str
    as_of: datetime
    scope: BreadthScope
    scope_name: str
    divergence_type: BreadthDivergenceType
    index_return_pct: float | None = None
    breadth_change_pct: float | None = None
    participation_change_pct: float | None = None
    divergence_score: float | None = None
    status: BreadthStatus = BreadthStatus.UNKNOWN
    message: str = ""
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Breadth divergence is research-only. It does not predict price direction. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BreadthRegimeSnapshot:
    regime_id: str
    as_of: datetime
    scope: BreadthScope
    scope_name: str
    label: BreadthRegimeLabel
    breadth_score: float | None = None
    participation_score: float | None = None
    volume_breadth_score: float | None = None
    divergence_score: float | None = None
    sector_confirmation_score: float | None = None
    status: BreadthStatus = BreadthStatus.UNKNOWN
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Breadth regime snapshot is research-only market context. It is not investment advice. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BreadthReport:
    report_id: str
    generated_at: datetime
    scope: BreadthScope
    scope_name: str
    universe: BreadthUniverseSnapshot | None = None
    advance_decline: AdvanceDeclineSummary | None = None
    participation: ParticipationSummary | None = None
    high_low: HighLowBreadthSummary | None = None
    volume_breadth: VolumeBreadthSummary | None = None
    sector_breadth: list[SectorBreadthSummary] = field(default_factory=list)
    divergences: list[BreadthDivergence] = field(default_factory=list)
    regime: BreadthRegimeSnapshot | None = None
    metrics: list[BreadthMetric] = field(default_factory=list)
    key_findings: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = "Breadth report is research-only. It is not investment advice, portfolio advice, or an order instruction. No real order was sent."
    metadata: dict[str, Any] = field(default_factory=dict)

