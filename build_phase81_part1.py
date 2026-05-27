import os
from pathlib import Path

base_dir = Path("bist_signal_bot")

# 1. exceptions.py
exc_path = base_dir / "core" / "exceptions.py"
if exc_path.exists():
    content = exc_path.read_text()
    if "class FinancialsError" not in content:
        content += """

class FinancialsError(BistSignalBotError):
    pass

class FinancialImportError(FinancialsError):
    pass

class FinancialValidationError(FinancialsError):
    pass

class FinancialNormalizationError(FinancialsError):
    pass

class FinancialPeriodError(FinancialsError):
    pass

class FinancialRatioError(FinancialsError):
    pass

class FinancialTrendError(FinancialsError):
    pass

class EarningsQualityError(FinancialsError):
    pass

class FinancialSectorCompareError(FinancialsError):
    pass

class FinancialStorageError(FinancialsError):
    pass
"""
        exc_path.write_text(content)

# 2. settings.py
settings_path = base_dir / "config" / "settings.py"
if settings_path.exists():
    content = settings_path.read_text()
    if "ENABLE_FINANCIALS" not in content:
        # We need to insert before the last class line, or just add attributes to Settings
        # Since it's a Pydantic model, we can append to the class body
        import re
        content = re.sub(r'class Settings\(BaseSettings\):',
                         r'''class Settings(BaseSettings):
    # Financial Statement Intelligence
    ENABLE_FINANCIALS: bool = True
    FINANCIALS_DIR_NAME: str = "financials"
    FINANCIAL_IMPORT_REQUIRES_CONFIRM: bool = True
    FINANCIALS_RESEARCH_ONLY: bool = True
    FINANCIALS_SAVE_DERIVED_METRICS: bool = True

    FINANCIAL_AUTO_NORMALIZE_ON_IMPORT: bool = True
    FINANCIAL_AUTO_CALCULATE_RATIOS_ON_IMPORT: bool = True
    FINANCIAL_AUTO_ANALYZE_TRENDS_ON_IMPORT: bool = True
    FINANCIAL_AUTO_ASSESS_QUALITY_ON_IMPORT: bool = True
    FINANCIAL_AUTO_SECTOR_COMPARE_ON_IMPORT: bool = True

    FINANCIAL_RATIO_MIN_DENOMINATOR_ABS: float = 1e-9
    FINANCIAL_BANKING_SECTOR_RATIO_WARNING: bool = True

    FINANCIAL_QUALITY_STRONG_SCORE: float = 70.0
    FINANCIAL_QUALITY_WEAK_SCORE: float = 40.0
    FINANCIAL_HIGH_DEBT_TO_EQUITY_WARN: float = 2.0
    FINANCIAL_NEGATIVE_FCF_WARN: bool = True
    FINANCIAL_OCF_NET_INCOME_QUALITY_WARN: float = 0.7

    SCANNER_INCLUDE_FINANCIAL_CONTEXT: bool = True
    SCANNER_FINANCIAL_METADATA_ONLY: bool = True

    PORTFOLIO_USE_FINANCIAL_QUALITY_SCORE: bool = True
    PORTFOLIO_FINANCIAL_QUALITY_WEIGHT: float = 0.10

    RUNTIME_FINANCIAL_CONTEXT_ENABLED: bool = True
    SCHEDULER_ENABLE_FINANCIAL_COVERAGE_WEEKLY: bool = False

    REPORT_INCLUDE_FINANCIALS: bool = True
    RESEARCH_AUTO_LOG_FINANCIALS: bool = False
''', content)
        settings_path.write_text(content)

# 3. paths.py
paths_path = base_dir / "storage" / "paths.py"
if paths_path.exists():
    content = paths_path.read_text()
    if "get_financials_dir" not in content:
        content += """

def get_financials_dir(settings=None) -> Path:
    from bist_signal_bot.config.settings import get_settings
    if settings is None:
        settings = get_settings()
    data_dir = get_data_dir(settings)
    fin_dir = data_dir / settings.FINANCIALS_DIR_NAME
    fin_dir.mkdir(parents=True, exist_ok=True)
    return fin_dir
"""
        paths_path.write_text(content)

# 4. financials/__init__.py
os.makedirs(base_dir / "financials", exist_ok=True)
(base_dir / "financials" / "__init__.py").write_text("")

# 5. financials/models.py
with open(base_dir / "financials" / "models.py", "w") as f:
    f.write('''import dataclasses
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
    disclaimer: str = "Financial statement record is local research data only. It is not investment advice. No real order was sent."

    def __post_init__(self):
        self.symbol = self.symbol.upper() if self.symbol else ""
        if self.fiscal_year < 0:
            self.warnings.append("fiscal_year must be positive")
        if not self.values:
            self.warnings.append("values dictionary is empty")
        if self.statement_type == FinancialStatementType.UNKNOWN:
            self.warnings.append("statement_type is UNKNOWN")

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
    disclaimer: str = "Earnings quality assessment is research-only. It does not predict future earnings or price direction. No real order was sent."

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
    disclaimer: str = "Financial import is local operational data processing only. No real order was sent."

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
    disclaimer: str = "Financial analysis report is research-only. It is not investment advice. No real order was sent."
''')
