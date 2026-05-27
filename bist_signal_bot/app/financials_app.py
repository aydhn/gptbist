from pathlib import Path
from bist_signal_bot.financials.storage import FinancialStore
from bist_signal_bot.financials.importer import FinancialStatementImporter
from bist_signal_bot.financials.normalizer import FinancialStatementNormalizer
from bist_signal_bot.financials.periods import FinancialPeriodEngine
from bist_signal_bot.financials.statements import FinancialStatementService
from bist_signal_bot.financials.ratios import FinancialRatioCalculator
from bist_signal_bot.financials.trends import FinancialTrendAnalyzer
from bist_signal_bot.financials.quality import EarningsQualityAnalyzer
from bist_signal_bot.financials.sector_compare import SectorFinancialComparator
from bist_signal_bot.financials.linking import FinancialLinker

def create_financial_store(settings=None, base_dir: Path | None = None) -> FinancialStore:
    return FinancialStore(settings, base_dir)

def create_financial_statement_importer(settings=None, base_dir: Path | None = None) -> FinancialStatementImporter:
    return FinancialStatementImporter(settings, base_dir)

def create_financial_statement_normalizer(settings=None) -> FinancialStatementNormalizer:
    return FinancialStatementNormalizer(settings)

def create_financial_period_engine(settings=None) -> FinancialPeriodEngine:
    return FinancialPeriodEngine(settings)

def create_financial_statement_service(settings=None, base_dir: Path | None = None) -> FinancialStatementService:
    return FinancialStatementService(settings, base_dir)

def create_financial_ratio_calculator(settings=None) -> FinancialRatioCalculator:
    return FinancialRatioCalculator(settings)

def create_financial_trend_analyzer(settings=None) -> FinancialTrendAnalyzer:
    return FinancialTrendAnalyzer(settings)

def create_earnings_quality_analyzer(settings=None) -> EarningsQualityAnalyzer:
    return EarningsQualityAnalyzer(settings)

def create_sector_financial_comparator(settings=None, base_dir: Path | None = None) -> SectorFinancialComparator:
    return SectorFinancialComparator(settings, base_dir)

def create_financial_linker(settings=None, base_dir: Path | None = None) -> FinancialLinker:
    return FinancialLinker(settings, base_dir)
