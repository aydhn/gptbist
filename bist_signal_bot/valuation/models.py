from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional, List
from pydantic import BaseModel, Field, field_validator

class ValuationStatus(str, Enum):
    CHEAP = "CHEAP"
    FAIR = "FAIR"
    EXPENSIVE = "EXPENSIVE"
    EXTREME_CHEAP = "EXTREME_CHEAP"
    EXTREME_EXPENSIVE = "EXTREME_EXPENSIVE"
    WATCH = "WATCH"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class ValuationMetricType(str, Enum):
    MARKET_CAP = "MARKET_CAP"
    ENTERPRISE_VALUE = "ENTERPRISE_VALUE"
    NET_DEBT = "NET_DEBT"
    PE = "PE"
    PB = "PB"
    EV_EBITDA = "EV_EBITDA"
    EV_SALES = "EV_SALES"
    PRICE_SALES = "PRICE_SALES"
    FCF_YIELD = "FCF_YIELD"
    EARNINGS_YIELD = "EARNINGS_YIELD"
    DIVIDEND_YIELD = "DIVIDEND_YIELD"
    PEG_LITE = "PEG_LITE"
    CUSTOM = "CUSTOM"

class ValuationComparisonScope(str, Enum):
    HISTORICAL_SELF = "HISTORICAL_SELF"
    SECTOR_PEERS = "SECTOR_PEERS"
    MARKET = "MARKET"
    CUSTOM = "CUSTOM"
    UNKNOWN = "UNKNOWN"

class ValuationRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EXTREME = "EXTREME"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"

class ValuationMarketInput(BaseModel):
    input_id: str
    symbol: str
    as_of: datetime
    price: Optional[float] = None
    shares_outstanding: Optional[float] = None
    free_float_ratio: Optional[float] = None
    market_cap: Optional[float] = None
    net_debt: Optional[float] = None
    enterprise_value: Optional[float] = None
    currency: str = "TRY"
    price_source: Optional[str] = None
    shares_source: Optional[str] = None
    financial_statement_ref: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbol", mode="before")
    def _normalize_symbol(cls, v):
        if v: return v.upper()
        return v

    @field_validator("price", "shares_outstanding")
    def _check_non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("Value cannot be negative")
        return v

class ValuationMultiple(BaseModel):
    multiple_id: str
    symbol: str
    metric_type: ValuationMetricType
    as_of: datetime
    fiscal_year: Optional[int] = None
    fiscal_period: Optional[str] = None
    numerator: Optional[float] = None
    denominator: Optional[float] = None
    value: Optional[float] = None
    status: ValuationStatus
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Valuation multiple is research-only. It is not investment advice or a target price. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ValuationBand(BaseModel):
    band_id: str
    symbol: str
    metric_type: ValuationMetricType
    scope: ValuationComparisonScope
    as_of: datetime
    current_value: Optional[float] = None
    historical_min: Optional[float] = None
    historical_p25: Optional[float] = None
    historical_median: Optional[float] = None
    historical_p75: Optional[float] = None
    historical_max: Optional[float] = None
    percentile_rank: Optional[float] = None
    z_score: Optional[float] = None
    status: ValuationStatus
    warnings: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class PeerValuationComparison(BaseModel):
    comparison_id: str
    symbol: str
    sector: Optional[str] = None
    as_of: datetime
    metric_type: ValuationMetricType
    subject_value: Optional[float] = None
    peer_median: Optional[float] = None
    peer_average: Optional[float] = None
    peer_percentile_rank: Optional[float] = None
    peer_count: int
    relative_discount_premium_pct: Optional[float] = None
    status: ValuationStatus
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Valuation multiple is research-only. It is not investment advice or a target price. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ValuationRiskAssessment(BaseModel):
    assessment_id: str
    symbol: str
    as_of: datetime
    valuation_score: Optional[float] = None
    valuation_risk_level: ValuationRiskLevel
    expensive_metrics: List[str] = Field(default_factory=list)
    cheap_metrics: List[str] = Field(default_factory=list)
    data_quality_warnings: List[str] = Field(default_factory=list)
    earnings_quality_context: dict[str, Any] = Field(default_factory=dict)
    sector_relative_context: dict[str, Any] = Field(default_factory=dict)
    recommended_decision: str
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Valuation risk assessment is research-only. It does not predict price direction and is not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class ValuationReport(BaseModel):
    report_id: str
    symbol: Optional[str] = None
    generated_at: datetime
    market_inputs: List[ValuationMarketInput] = Field(default_factory=list)
    multiples: List[ValuationMultiple] = Field(default_factory=list)
    bands: List[ValuationBand] = Field(default_factory=list)
    peer_comparisons: List[PeerValuationComparison] = Field(default_factory=list)
    risk_assessments: List[ValuationRiskAssessment] = Field(default_factory=list)
    key_findings: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Valuation report is research-only. It is not investment advice, target price, or an order instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
