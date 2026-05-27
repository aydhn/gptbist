import os
from pathlib import Path

base_dir = Path("bist_signal_bot")

# 17. app/financials_app.py
with open(base_dir / "app" / "financials_app.py", "w") as f:
    f.write('''from pathlib import Path
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
''')

# 18. core/audit.py update
audit_path = base_dir / "core" / "audit.py"
if audit_path.exists():
    content = audit_path.read_text()
    if "FINANCIALS_IMPORTED" not in content:
        import re
        content = re.sub(
            r'(class AuditEventType\(str, Enum\):)',
            r'''\1
    FINANCIALS_IMPORTED = "FINANCIALS_IMPORTED"
    FINANCIALS_NORMALIZED = "FINANCIALS_NORMALIZED"
    FINANCIAL_RATIOS_CALCULATED = "FINANCIAL_RATIOS_CALCULATED"
    FINANCIAL_TRENDS_ANALYZED = "FINANCIAL_TRENDS_ANALYZED"
    EARNINGS_QUALITY_ASSESSED = "EARNINGS_QUALITY_ASSESSED"
    SECTOR_FINANCIAL_COMPARE_COMPLETED = "SECTOR_FINANCIAL_COMPARE_COMPLETED"
    FINANCIAL_LINKS_CREATED = "FINANCIAL_LINKS_CREATED"
    FINANCIAL_REPORT_CREATED = "FINANCIAL_REPORT_CREATED"''',
            content
        )
        audit_path.write_text(content)

# 19. notifications/formatter.py update
notif_path = base_dir / "notifications" / "formatter.py"
if notif_path.exists():
    content = notif_path.read_text()
    if "format_financial_statement" not in content:
        content += '''
def format_financial_statement(statement) -> str:
    return f"Statement: {statement.symbol} {statement.fiscal_year} {statement.fiscal_period}"

def format_financial_ratios(ratios) -> str:
    return f"Ratios for {len(ratios)} metrics"

def format_earnings_quality(assessment) -> str:
    return f"""
BIST Bot Finansal Özet

Sembol: {assessment.symbol}
Dönem: {assessment.fiscal_year}{assessment.fiscal_period}
Earnings Quality Score: {assessment.overall_quality_score}
Status: {assessment.status.value}

Bu çıktı araştırma amaçlı finansal tablo özetidir.
Yatırım tavsiyesi değildir.
Gerçek emir gönderilmedi.
"""

def format_financial_analysis_report(report) -> str:
    return f"Report for {report.symbol}"
'''
        notif_path.write_text(content)
