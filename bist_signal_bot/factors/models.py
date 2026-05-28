
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, List

class FactorStatus(str, Enum):
    STRONG = "STRONG"
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    WEAK = "WEAK"
    WATCH = "WATCH"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class FactorType(str, Enum):
    MOMENTUM = "MOMENTUM"
    VALUE = "VALUE"
    QUALITY = "QUALITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    LIQUIDITY = "LIQUIDITY"
    SIZE = "SIZE"
    GROWTH = "GROWTH"
    PROFITABILITY = "PROFITABILITY"
    LEVERAGE = "LEVERAGE"
    DIVIDEND = "DIVIDEND"
    SENTIMENT_PLACEHOLDER = "SENTIMENT_PLACEHOLDER"
    TECHNICAL_TREND = "TECHNICAL_TREND"
    CUSTOM = "CUSTOM"

class FactorExposureDirection(str, Enum):
    LONG_EXPOSURE = "LONG_EXPOSURE"
    SHORT_EXPOSURE = "SHORT_EXPOSURE"
    NEUTRAL = "NEUTRAL"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"

class FactorContributionType(str, Enum):
    RETURN = "RETURN"
    RISK = "RISK"
    SCORE = "SCORE"
    CONFIDENCE = "CONFIDENCE"
    COST = "COST"
    TURNOVER = "TURNOVER"
    CUSTOM = "CUSTOM"

class SectorRotationStatus(str, Enum):
    LEADING = "LEADING"
    IMPROVING = "IMPROVING"
    NEUTRAL = "NEUTRAL"
    WEAKENING = "WEAKENING"
    LAGGING = "LAGGING"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"

class ThemeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    WATCH = "WATCH"
    INACTIVE = "INACTIVE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"

@dataclass
class FactorInputSnapshot:
    input_id: str
    symbol: str
    as_of: datetime
    sector: Optional[str] = None
    market_cap: Optional[float] = None
    price_return_20d_pct: Optional[float] = None
    price_return_60d_pct: Optional[float] = None
    price_return_120d_pct: Optional[float] = None
    volatility_60d_pct: Optional[float] = None
    avg_volume_20d: Optional[float] = None
    avg_turnover_20d: Optional[float] = None
    valuation_score: Optional[float] = None
    earnings_quality_score: Optional[float] = None
    revenue_growth_yoy_pct: Optional[float] = None
    net_income_growth_yoy_pct: Optional[float] = None
    debt_to_equity: Optional[float] = None
    roe: Optional[float] = None
    dividend_yield: Optional[float] = None
    warnings: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.symbol:
            self.symbol = self.symbol.upper()
        if self.valuation_score is not None:
            self.valuation_score = max(0.0, min(100.0, self.valuation_score))
        if self.earnings_quality_score is not None:
            self.earnings_quality_score = max(0.0, min(100.0, self.earnings_quality_score))
        if self.price_return_20d_pct is None and "Missing core price momentum input" not in self.warnings:
            self.warnings.append("Missing core price momentum input")

@dataclass
class FactorScore:
    score_id: str
    symbol: str
    factor_type: FactorType
    as_of: datetime
    raw_value: Optional[float] = None
    percentile_rank: Optional[float] = None
    z_score: Optional[float] = None
    score: Optional[float] = None
    status: FactorStatus = FactorStatus.UNKNOWN
    direction: FactorExposureDirection = FactorExposureDirection.UNKNOWN
    warnings: List[str] = field(default_factory=list)
    disclaimer: str = "Factor score is research-only. It is not investment advice and does not predict future price direction. No real order was sent."
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.score is not None:
            self.score = max(0.0, min(100.0, self.score))

@dataclass
class FactorExposure:
    exposure_id: str
    object_type: str
    object_id: str
    symbol: Optional[str] = None
    strategy_name: Optional[str] = None
    as_of: datetime = field(default_factory=datetime.now)
    factor_scores: List[FactorScore] = field(default_factory=list)
    aggregate_factor_score: Optional[float] = None
    dominant_factors: List[str] = field(default_factory=list)
    weak_factors: List[str] = field(default_factory=list)
    factor_concentration_score: Optional[float] = None
    status: FactorStatus = FactorStatus.UNKNOWN
    warnings: List[str] = field(default_factory=list)
    disclaimer: str = "Factor exposure is research metadata only. It is not investment advice or an order instruction. No real order was sent."
    metadata: dict = field(default_factory=dict)

@dataclass
class SectorRotationScore:
    rotation_id: str
    sector: str
    as_of: datetime
    momentum_score: Optional[float] = None
    relative_strength_score: Optional[float] = None
    breadth_score: Optional[float] = None
    volatility_score: Optional[float] = None
    valuation_context_score: Optional[float] = None
    final_rotation_score: Optional[float] = None
    status: SectorRotationStatus = SectorRotationStatus.UNKNOWN
    leading_symbols: List[str] = field(default_factory=list)
    lagging_symbols: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    disclaimer: str = "Sector rotation score is research-only. It does not predict future sector performance. No real order was sent."
    metadata: dict = field(default_factory=dict)

@dataclass
class ThemeDefinition:
    theme_id: str
    name: str
    description: str
    symbols: List[str] = field(default_factory=list)
    sectors: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    status: ThemeStatus = ThemeStatus.UNKNOWN
    warnings: List[str] = field(default_factory=list)
    disclaimer: str = "Theme definition is local research metadata only. It is not investment advice. No real order was sent."
    metadata: dict = field(default_factory=dict)

@dataclass
class ThemeExposure:
    exposure_id: str
    theme_id: str
    theme_name: str
    object_type: str
    object_id: str
    matched_symbols: List[str] = field(default_factory=list)
    matched_sectors: List[str] = field(default_factory=list)
    exposure_weight_pct: Optional[float] = None
    theme_score: Optional[float] = None
    status: ThemeStatus = ThemeStatus.UNKNOWN
    warnings: List[str] = field(default_factory=list)
    disclaimer: str = "Theme exposure is local research metadata only. It is not investment advice. No real order was sent."
    metadata: dict = field(default_factory=dict)

@dataclass
class FactorCrowdingAssessment:
    assessment_id: str
    object_type: str
    object_id: str
    as_of: datetime
    dominant_factor: Optional[str] = None
    dominant_factor_weight_pct: Optional[float] = None
    concentration_score: Optional[float] = None
    crowding_risk_level: str = "LOW"
    warnings: List[str] = field(default_factory=list)
    disclaimer: str = "Factor crowding assessment is research-only. It is not a trading restriction or investment advice. No real order was sent."
    metadata: dict = field(default_factory=dict)

@dataclass
class FactorAttributionItem:
    attribution_id: str
    object_type: str
    object_id: str
    factor_type: FactorType
    contribution_type: FactorContributionType
    contribution_value: Optional[float] = None
    contribution_pct: Optional[float] = None
    message: str = ""
    warnings: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

@dataclass
class FactorReport:
    report_id: str
    symbol: Optional[str] = None
    generated_at: datetime = field(default_factory=datetime.now)
    inputs: List[FactorInputSnapshot] = field(default_factory=list)
    factor_scores: List[FactorScore] = field(default_factory=list)
    exposures: List[FactorExposure] = field(default_factory=list)
    sector_rotation: List[SectorRotationScore] = field(default_factory=list)
    theme_exposures: List[ThemeExposure] = field(default_factory=list)
    crowding: List[FactorCrowdingAssessment] = field(default_factory=list)
    attributions: List[FactorAttributionItem] = field(default_factory=list)
    key_findings: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    disclaimer: str = "Factor report is research-only. It is not investment advice, portfolio advice, or an order instruction. No real order was sent."
    metadata: dict = field(default_factory=dict)
