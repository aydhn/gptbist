import dataclasses
from datetime import datetime
from enum import Enum
from typing import Any


class FinancialStatementType(str, Enum):
    INCOME_STATEMENT = "INCOME_STATEMENT"
    BALANCE_SHEET = "BALANCE_SHEET"
    CASH_FLOW = "CASH_FLOW"
    COMPREHENSIVE_INCOME = "COMPREHENSIVE_INCOME"
    FOOTNOTE_SUMMARY = "FOOTNOTE_SUMMARY"
    DERIVED_METRICS = "DERIVED_METRICS"
    UNKNOWN = "UNKNOWN"


class FinancialPeriodType(str, Enum):
    QUARTERLY = "QUARTERLY"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    NINE_MONTHS = "NINE_MONTHS"
    ANNUAL = "ANNUAL"
    TRAILING_TWELVE_MONTHS = "TRAILING_TWELVE_MONTHS"
    CUSTOM = "CUSTOM"
    UNKNOWN = "UNKNOWN"


class FinancialDataStatus(str, Enum):
    RAW_IMPORTED = "RAW_IMPORTED"
    NORMALIZED = "NORMALIZED"
    VALIDATED = "VALIDATED"
    DERIVED = "DERIVED"
    WARNING = "WARNING"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


class FinancialMetricDirection(str, Enum):
    HIGHER_IS_BETTER = "HIGHER_IS_BETTER"
    LOWER_IS_BETTER = "LOWER_IS_BETTER"
    NEUTRAL = "NEUTRAL"
    CONTEXT_DEPENDENT = "CONTEXT_DEPENDENT"
    UNKNOWN = "UNKNOWN"


class FinancialQualityStatus(str, Enum):
    STRONG = "STRONG"
    WATCH = "WATCH"
    WEAK = "WEAK"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    ERROR = "ERROR"
    UNKNOWN = "UNKNOWN"


@dataclasses.dataclass
class FinancialStatementRecord:
    record_id: str
    symbol: str
    period_end: datetime
    currency: str
    values: dict[str, float | int | str | None]
    source: str
    status: FinancialDataStatus
    warnings: list[str]
    metadata: dict[str, Any]
    statement_type: FinancialStatementType = FinancialStatementType.UNKNOWN
    period_type: FinancialPeriodType = FinancialPeriodType.UNKNOWN
    fiscal_year: int = 0
    fiscal_period: str = ""
    company_name: str | None = None
    period_start: datetime | None = None
    reported_at: datetime | None = None
    source_ref: str | None = None
    disclaimer: str = (
        "Financial statement record is local research data only. It is not investment advice. No real order was sent."
    )

    def __post_init__(self) -> None:
        self._normalize_symbol()
        self._validate_fiscal_year()
        self._validate_values()
        self._validate_statement_type()

    def _normalize_symbol(self) -> None:
        self.symbol = self.symbol.upper() if self.symbol else ""

    def _validate_fiscal_year(self) -> None:
        warning_msg = "fiscal_year must be positive"
        if self.fiscal_year < 0 and warning_msg not in self.warnings:
            self.warnings.append(warning_msg)

    def _validate_values(self) -> None:
        warning_msg = "values dictionary is empty"
        if not self.values and warning_msg not in self.warnings:
            self.warnings.append(warning_msg)

    def _validate_statement_type(self) -> None:
        warning_msg = "statement_type is UNKNOWN"
        if self.statement_type == FinancialStatementType.UNKNOWN and warning_msg not in self.warnings:
            self.warnings.append(warning_msg)


@dataclasses.dataclass
class NormalizedFinancialStatement:
    normalized_id: str
    symbol: str
    fiscal_year: int
    fiscal_period: str
    period_type: FinancialPeriodType
    period_end: datetime
    currency: str
    source_records: list[str]
    warnings: list[str]
    metadata: dict[str, Any]
    reported_at: datetime | None = None
    revenue: float | None = None
    gross_profit: float | None = None
    operating_profit: float | None = None
    ebitda: float | None = None
    net_income: float | None = None
    total_assets: float | None = None
    total_equity: float | None = None
    total_debt: float | None = None
    cash_and_equivalents: float | None = None
    current_assets: float | None = None
    current_liabilities: float | None = None
    operating_cash_flow: float | None = None
    investing_cash_flow: float | None = None
    financing_cash_flow: float | None = None
    free_cash_flow: float | None = None
    capex: float | None = None
    shares_outstanding: float | None = None


@dataclasses.dataclass
class FinancialRatio:
    ratio_id: str
    symbol: str
    fiscal_year: int
    fiscal_period: str
    period_end: datetime
    name: str
    direction: FinancialMetricDirection
    status: FinancialQualityStatus
    warnings: list[str]
    metadata: dict[str, Any]
    value: float | None = None


@dataclasses.dataclass
class FinancialTrendMetric:
    trend_id: str
    symbol: str
    metric_name: str
    period_end: datetime
    status: FinancialQualityStatus
    warnings: list[str]
    metadata: dict[str, Any]
    current_value: float | None = None
    previous_value: float | None = None
    yoy_change_pct: float | None = None
    qoq_change_pct: float | None = None
    ttm_value: float | None = None
    trend_score: float | None = None


@dataclasses.dataclass
class EarningsQualityAssessment:
    assessment_id: str
    symbol: str
    fiscal_year: int
    fiscal_period: str
    period_end: datetime
    status: FinancialQualityStatus
    key_strengths: list[str]
    key_weaknesses: list[str]
    warnings: list[str]
    metadata: dict[str, Any]
    accrual_quality_score: float | None = None
    cash_conversion_score: float | None = None
    margin_quality_score: float | None = None
    debt_quality_score: float | None = None
    earnings_growth_quality_score: float | None = None
    overall_quality_score: float | None = None
    disclaimer: str = (
        "Earnings quality assessment is research-only. It does not predict future earnings or price direction. No real order was sent."
    )


@dataclasses.dataclass
class SectorFinancialComparison:
    comparison_id: str
    symbol: str
    period_end: datetime
    ratios: list[FinancialRatio]
    sector_medians: dict[str, float | None]
    percentile_ranks: dict[str, float | None]
    relative_strengths: list[str]
    relative_weaknesses: list[str]
    status: FinancialQualityStatus
    warnings: list[str]
    metadata: dict[str, Any]
    sector: str | None = None
    sector_score: float | None = None
    disclaimer: str = "Sector comparison is research-only. No real order was sent."


@dataclasses.dataclass
class FinancialImportResult:
    import_id: str
    created_at: datetime
    source_path: str
    rows_seen: int
    records_imported: int
    records_skipped: int
    duplicate_count: int
    warnings: list[str]
    errors: list[str]
    metadata: dict[str, Any]
    disclaimer: str = (
        "Financial import is local operational data processing only. No real order was sent."
    )


@dataclasses.dataclass
class FinancialAnalysisReport:
    report_id: str
    generated_at: datetime
    normalized_statements: list[NormalizedFinancialStatement]
    ratios: list[FinancialRatio]
    trends: list[FinancialTrendMetric]
    quality_assessments: list[EarningsQualityAssessment]
    sector_comparisons: list[SectorFinancialComparison]
    key_findings: list[str]
    warnings: list[str]
    metadata: dict[str, Any]
    symbol: str | None = None
    disclaimer: str = (
        "Financial analysis report is research-only. It is not investment advice. No real order was sent."
    )
