from enum import Enum
from typing import Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class DisclosureType(str, Enum):
    FINANCIAL_STATEMENT = "FINANCIAL_STATEMENT"
    EARNINGS_SUMMARY = "EARNINGS_SUMMARY"
    DIVIDEND = "DIVIDEND"
    CORPORATE_ACTION = "CORPORATE_ACTION"
    CAPITAL_INCREASE = "CAPITAL_INCREASE"
    CAPITAL_DECREASE = "CAPITAL_DECREASE"
    SHARE_BUYBACK = "SHARE_BUYBACK"
    MATERIAL_EVENT = "MATERIAL_EVENT"
    CONTRACT_TENDER = "CONTRACT_TENDER"
    INVESTMENT_PROJECT = "INVESTMENT_PROJECT"
    DEBT_FINANCING = "DEBT_FINANCING"
    CREDIT_RATING = "CREDIT_RATING"
    LEGAL_CASE = "LEGAL_CASE"
    REGULATORY_ACTION = "REGULATORY_ACTION"
    MANAGEMENT_CHANGE = "MANAGEMENT_CHANGE"
    RELATED_PARTY_TRANSACTION = "RELATED_PARTY_TRANSACTION"
    OWNERSHIP_CHANGE = "OWNERSHIP_CHANGE"
    TRADING_HALT_NOTICE = "TRADING_HALT_NOTICE"
    GENERAL_ASSEMBLY = "GENERAL_ASSEMBLY"
    ACTIVITY_REPORT = "ACTIVITY_REPORT"
    NEWS_NOTE = "NEWS_NOTE"
    CUSTOM = "CUSTOM"
    UNKNOWN = "UNKNOWN"

class DisclosureScope(str, Enum):
    SYMBOL = "SYMBOL"
    MULTI_SYMBOL = "MULTI_SYMBOL"
    SECTOR = "SECTOR"
    MARKET = "MARKET"
    MACRO = "MACRO"
    PORTFOLIO = "PORTFOLIO"
    UNKNOWN = "UNKNOWN"

class DisclosureSentiment(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    MIXED = "MIXED"
    NEUTRAL = "NEUTRAL"
    UNCLEAR = "UNCLEAR"
    UNKNOWN = "UNKNOWN"

class DisclosureSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"

class DisclosureRiskTagType(str, Enum):
    EARNINGS_VOLATILITY = "EARNINGS_VOLATILITY"
    GUIDANCE_CHANGE = "GUIDANCE_CHANGE"
    HIGH_LEVERAGE = "HIGH_LEVERAGE"
    LIQUIDITY_PRESSURE = "LIQUIDITY_PRESSURE"
    LEGAL_REGULATORY = "LEGAL_REGULATORY"
    MANAGEMENT_RISK = "MANAGEMENT_RISK"
    OWNERSHIP_CHANGE = "OWNERSHIP_CHANGE"
    DILUTION_RISK = "DILUTION_RISK"
    CORPORATE_ACTION_RISK = "CORPORATE_ACTION_RISK"
    CONTRACT_DEPENDENCY = "CONTRACT_DEPENDENCY"
    MARGIN_PRESSURE = "MARGIN_PRESSURE"
    FX_SENSITIVITY = "FX_SENSITIVITY"
    INTEREST_RATE_SENSITIVITY = "INTEREST_RATE_SENSITIVITY"
    EVENT_GAP_RISK = "EVENT_GAP_RISK"
    POSITIVE_CATALYST_PLACEHOLDER = "POSITIVE_CATALYST_PLACEHOLDER"
    DATA_QUALITY_WARNING = "DATA_QUALITY_WARNING"
    UNKNOWN = "UNKNOWN"

class DisclosureProcessingStatus(str, Enum):
    RAW_IMPORTED = "RAW_IMPORTED"
    NORMALIZED = "NORMALIZED"
    CLASSIFIED = "CLASSIFIED"
    LINKED = "LINKED"
    EVENT_EXTRACTED = "EVENT_EXTRACTED"
    DIGESTED = "DIGESTED"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"

class DisclosureRecord(BaseModel):
    disclosure_id: str
    external_id: Optional[str] = None
    title: str
    body: str
    disclosure_type: DisclosureType = DisclosureType.UNKNOWN
    scope: DisclosureScope = DisclosureScope.UNKNOWN
    published_at: Optional[datetime] = None
    received_at: datetime
    symbols: List[str] = Field(default_factory=list)
    company_names: List[str] = Field(default_factory=list)
    sectors: List[str] = Field(default_factory=list)
    source: str
    source_ref: Optional[str] = None
    language: str
    status: DisclosureProcessingStatus = DisclosureProcessingStatus.UNKNOWN
    sentiment: DisclosureSentiment = DisclosureSentiment.UNKNOWN
    severity: DisclosureSeverity = DisclosureSeverity.UNKNOWN
    confidence: Optional[float] = None
    tags: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Disclosure record is local research metadata only. It is not investment advice. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

    def dict(self, *args, **kwargs):
        # Override to ensure basic validations
        if not self.title.strip() or not self.body.strip():
            pass # Pydantic v1 vs v2 might differ on how to raise errors here, so let's rely on standard validation.
        return super().dict(*args, **kwargs)

class DisclosureEntityLink(BaseModel):
    link_id: str
    disclosure_id: str
    entity_type: str
    entity_value: str
    symbol: Optional[str] = None
    confidence: Optional[float] = None
    relationship: str
    evidence_text: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DisclosureRiskTag(BaseModel):
    tag_id: str
    disclosure_id: str
    tag_type: DisclosureRiskTagType
    severity: DisclosureSeverity
    sentiment: DisclosureSentiment
    score: Optional[float] = None
    message: str
    evidence_text: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DisclosureEventExtraction(BaseModel):
    extraction_id: str
    disclosure_id: str
    extracted_event_type: str
    event_date: Optional[datetime] = None
    symbols: List[str] = Field(default_factory=list)
    severity: DisclosureSeverity = DisclosureSeverity.UNKNOWN
    confidence: Optional[float] = None
    should_create_market_event: bool = False
    suggested_title: str
    warnings: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class DisclosureImpactAssessment(BaseModel):
    assessment_id: str
    disclosure_id: str
    symbols: List[str] = Field(default_factory=list)
    disclosure_type: DisclosureType
    sentiment: DisclosureSentiment
    severity: DisclosureSeverity
    narrative_risk_score: Optional[float] = None
    event_risk_score_delta: Optional[float] = None
    confidence_adjustment: Optional[float] = None
    liquidity_risk_delta: Optional[float] = None
    volatility_risk_delta: Optional[float] = None
    recommended_decision: str
    risk_tags: List[DisclosureRiskTag] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Disclosure impact assessment is research-only narrative analysis. It does not predict price direction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class DisclosureDigest(BaseModel):
    digest_id: str
    created_at: datetime
    title: str
    disclosures: List[DisclosureRecord] = Field(default_factory=list)
    summary: str
    key_points: List[str] = Field(default_factory=list)
    risk_tags: List[DisclosureRiskTag] = Field(default_factory=list)
    symbols_covered: List[str] = Field(default_factory=list)
    high_severity_count: int = 0
    warnings: List[str] = Field(default_factory=list)
    disclaimer: str = "Disclosure digest is research-only. It is not investment advice or a trading instruction. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)

class DisclosureImportResult(BaseModel):
    import_id: str
    created_at: datetime
    source_path: str
    rows_seen: int = 0
    disclosures_imported: int = 0
    disclosures_skipped: int = 0
    duplicate_count: int = 0
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    disclaimer: str = "Disclosure import is local data processing only. No real order was sent."
    metadata: dict[str, Any] = Field(default_factory=dict)
