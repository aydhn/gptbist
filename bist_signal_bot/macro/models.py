from enum import Enum
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field

class MacroSeriesType(str, Enum):
    FX = "FX"
    RATE = "RATE"
    CDS = "CDS"
    COMMODITY = "COMMODITY"
    INDEX = "INDEX"
    SECTOR_INDEX = "SECTOR_INDEX"
    GLOBAL_RISK = "GLOBAL_RISK"
    INFLATION = "INFLATION"
    POLICY_RATE = "POLICY_RATE"
    VOLUME_PROXY = "VOLUME_PROXY"
    CUSTOM = "CUSTOM"
    UNKNOWN = "UNKNOWN"

class MacroProxyName(str, Enum):
    USDTRY = "USDTRY"
    EURTRY = "EURTRY"
    EURUSD = "EURUSD"
    GOLD_TRY = "GOLD_TRY"
    GOLD_USD = "GOLD_USD"
    BRENT_OIL = "BRENT_OIL"
    WTI_OIL = "WTI_OIL"
    CDS_5Y = "CDS_5Y"
    POLICY_RATE = "POLICY_RATE"
    BIST100 = "BIST100"
    BIST30 = "BIST30"
    BANK_INDEX = "BANK_INDEX"
    INDUSTRIAL_INDEX = "INDUSTRIAL_INDEX"
    VIX_PROXY = "VIX_PROXY"
    GLOBAL_RISK_PROXY = "GLOBAL_RISK_PROXY"
    CUSTOM = "CUSTOM"

class MacroRegimeLabel(str, Enum):
    RISK_ON = "RISK_ON"
    RISK_OFF = "RISK_OFF"
    FX_STRESS = "FX_STRESS"
    RATE_STRESS = "RATE_STRESS"
    COMMODITY_STRESS = "COMMODITY_STRESS"
    DISINFLATION_SUPPORTIVE = "DISINFLATION_SUPPORTIVE"
    INFLATION_PRESSURE = "INFLATION_PRESSURE"
    MIXED = "MIXED"
    CALM = "CALM"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNKNOWN = "UNKNOWN"

class MacroStatus(str, Enum):
    STRONG_SUPPORT = "STRONG_SUPPORT"
    SUPPORTIVE = "SUPPORTIVE"
    NEUTRAL = "NEUTRAL"
    PRESSURE = "PRESSURE"
    HIGH_PRESSURE = "HIGH_PRESSURE"
    WATCH = "WATCH"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class MacroSensitivityType(str, Enum):
    FX_BETA = "FX_BETA"
    RATE_BETA = "RATE_BETA"
    OIL_BETA = "OIL_BETA"
    CDS_BETA = "CDS_BETA"
    GOLD_BETA = "GOLD_BETA"
    GLOBAL_RISK_BETA = "GLOBAL_RISK_BETA"
    INDEX_BETA = "INDEX_BETA"
    CUSTOM = "CUSTOM"

class IntermarketDivergenceType(str, Enum):
    INDEX_UP_FX_STRESS = "INDEX_UP_FX_STRESS"
    INDEX_UP_RATE_STRESS = "INDEX_UP_RATE_STRESS"
    INDEX_UP_CDS_STRESS = "INDEX_UP_CDS_STRESS"
    BANKS_DOWN_RATES_UP = "BANKS_DOWN_RATES_UP"
    INDUSTRIALS_DOWN_FX_UP = "INDUSTRIALS_DOWN_FX_UP"
    OIL_UP_AIRLINES_DOWN = "OIL_UP_AIRLINES_DOWN"
    RISK_PROXY_DIVERGENCE = "RISK_PROXY_DIVERGENCE"
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"

class MacroSeriesPoint(BaseModel):
    point_id: str
    series_id: str
    proxy_name: MacroProxyName
    series_type: MacroSeriesType
    timestamp: datetime
    value: Optional[float]
    source: str
    source_ref: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class MacroSeries(BaseModel):
    series_id: str
    proxy_name: MacroProxyName
    series_type: MacroSeriesType
    name: str
    currency: Optional[str] = None
    frequency: str
    points: List[MacroSeriesPoint]
    source: str
    source_ref: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Macro series is local research data only. It is not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class MacroReturn(BaseModel):
    return_id: str
    series_id: str
    proxy_name: MacroProxyName
    timestamp: datetime
    return_1d_pct: Optional[float] = None
    return_5d_pct: Optional[float] = None
    return_20d_pct: Optional[float] = None
    volatility_20d_pct: Optional[float] = None
    z_score_20d: Optional[float] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class MacroCorrelation(BaseModel):
    correlation_id: str
    subject_symbol: Optional[str] = None
    subject_series_id: Optional[str] = None
    proxy_name: MacroProxyName
    as_of: datetime
    lookback_days: int
    correlation: Optional[float] = None
    beta: Optional[float] = None
    r_squared: Optional[float] = None
    sample_count: int
    status: MacroStatus
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Macro correlation is research-only statistical metadata. It is not causal proof or investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class MacroSensitivityAssessment(BaseModel):
    assessment_id: str
    object_type: str
    object_id: str
    symbol: Optional[str] = None
    sector: Optional[str] = None
    as_of: datetime
    sensitivities: List[MacroCorrelation]
    dominant_sensitivities: List[str]
    macro_pressure_score: Optional[float] = None
    macro_support_score: Optional[float] = None
    status: MacroStatus
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Macro sensitivity assessment is research-only. It does not predict price direction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class MacroRegimeSnapshot(BaseModel):
    regime_id: str
    as_of: datetime
    label: MacroRegimeLabel
    fx_pressure_score: Optional[float] = None
    rate_pressure_score: Optional[float] = None
    cds_pressure_score: Optional[float] = None
    commodity_pressure_score: Optional[float] = None
    global_risk_score: Optional[float] = None
    equity_support_score: Optional[float] = None
    final_macro_score: Optional[float] = None
    status: MacroStatus
    active_stress_flags: List[str]
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Macro regime snapshot is research-only market context. It is not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class MacroStressAssessment(BaseModel):
    stress_id: str
    as_of: datetime
    stress_flags: List[str]
    stress_score: Optional[float] = None
    affected_symbols: List[str]
    affected_sectors: List[str]
    suggested_review_reasons: List[str]
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Macro stress assessment is research-only. It does not authorize or block real trades. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class IntermarketDivergence(BaseModel):
    divergence_id: str
    as_of: datetime
    divergence_type: IntermarketDivergenceType
    subject: str
    proxy_name: MacroProxyName
    subject_return_pct: Optional[float] = None
    proxy_return_pct: Optional[float] = None
    divergence_score: Optional[float] = None
    status: MacroStatus
    message: str
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Intermarket divergence is research-only. It does not predict future price direction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class MacroImportResult(BaseModel):
    import_id: str
    created_at: datetime
    source_path: str
    rows_seen: int
    points_imported: int
    points_skipped: int
    duplicate_count: int
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    disclaimer: str = "Macro import is local data processing only. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class MacroReport(BaseModel):
    report_id: str
    generated_at: datetime
    regime: Optional[MacroRegimeSnapshot] = None
    returns: List[MacroReturn]
    correlations: List[MacroCorrelation]
    sensitivities: List[MacroSensitivityAssessment]
    stress: Optional[MacroStressAssessment] = None
    divergences: List[IntermarketDivergence]
    key_findings: List[str]
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Macro report is research-only. It is not investment advice, portfolio advice, or an order instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
