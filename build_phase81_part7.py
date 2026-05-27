import os
from pathlib import Path

base_dir = Path("bist_signal_bot")

# 24. tests/test_financial_trends.py
with open(base_dir / "tests" / "test_financial_trends.py", "w") as f:
    f.write('''import pytest
from datetime import datetime
from bist_signal_bot.financials.trends import FinancialTrendAnalyzer
from bist_signal_bot.financials.models import NormalizedFinancialStatement, FinancialPeriodType

def test_yoy_qoq_calculation():
    analyzer = FinancialTrendAnalyzer()

    assert analyzer.yoy_change(120.0, 100.0) == 0.2
    assert analyzer.qoq_change(110.0, 100.0) == 0.1
    assert analyzer.yoy_change(100.0, 0.0) is None
''')

# 25. tests/test_earnings_quality.py
with open(base_dir / "tests" / "test_earnings_quality.py", "w") as f:
    f.write('''import pytest
from datetime import datetime
from bist_signal_bot.financials.quality import EarningsQualityAnalyzer
from bist_signal_bot.financials.models import NormalizedFinancialStatement, FinancialPeriodType, FinancialQualityStatus

def test_cash_conversion_quality():
    analyzer = EarningsQualityAnalyzer()
    stmt = NormalizedFinancialStatement(
        normalized_id="1", symbol="ASELS", fiscal_year=2024, fiscal_period="Q4",
        period_type=FinancialPeriodType.QUARTERLY, period_end=datetime.now(), currency="TRY",
        source_records=[], warnings=[], metadata={},
        operating_cash_flow=80.0, net_income=100.0
    )
    score = analyzer.cash_conversion_quality(stmt)
    assert score == 80.0

def test_high_debt_weakness():
    analyzer = EarningsQualityAnalyzer()
    stmt = NormalizedFinancialStatement(
        normalized_id="1", symbol="ASELS", fiscal_year=2024, fiscal_period="Q4",
        period_type=FinancialPeriodType.QUARTERLY, period_end=datetime.now(), currency="TRY",
        source_records=[], warnings=[], metadata={},
        total_debt=300.0, total_equity=100.0
    )
    score = analyzer.debt_quality(stmt)
    assert score == 20.0
''')

# 26. tests/test_sector_fundamental_compare.py
with open(base_dir / "tests" / "test_sector_fundamental_compare.py", "w") as f:
    f.write('''import pytest
from bist_signal_bot.financials.sector_compare import SectorFinancialComparator

def test_medians_and_percentiles():
    comp = SectorFinancialComparator()
    peers = [10.0, 20.0, 30.0, 40.0, 50.0]

    rank = comp.percentile_rank(30.0, peers)
    assert rank == 40.0 # 2 items < 30.0 -> 2/5 = 40%
''')

# 27. tests/test_financial_linking.py
with open(base_dir / "tests" / "test_financial_linking.py", "w") as f:
    f.write('''import pytest
from bist_signal_bot.financials.linking import FinancialLinker

def test_financial_linking():
    linker = FinancialLinker()
    assert linker.relationship_message("disclosure", "ASELS") == "Linked disclosure for ASELS"
''')

# 28. tests/test_financial_storage.py
with open(base_dir / "tests" / "test_financial_storage.py", "w") as f:
    f.write('''import pytest
from bist_signal_bot.financials.storage import FinancialStore

def test_storage_init(tmp_path):
    store = FinancialStore(base_dir=tmp_path)
    assert store.base_dir == tmp_path
''')

# 29. tests/test_financial_models.py
with open(base_dir / "tests" / "test_financial_models.py", "w") as f:
    f.write('''import pytest
from datetime import datetime
from bist_signal_bot.financials.models import FinancialStatementRecord, FinancialDataStatus

def test_record_validation():
    rec = FinancialStatementRecord(
        record_id="1",
        symbol="asels",
        period_end=datetime.now(),
        currency="TRY",
        values={},
        source="csv",
        status=FinancialDataStatus.RAW_IMPORTED,
        warnings=[],
        metadata={},
        fiscal_year=-1
    )
    assert rec.symbol == "ASELS"
    assert "values dictionary is empty" in rec.warnings
    assert "fiscal_year must be positive" in rec.warnings
''')

# 30. tests/test_financial_reporting.py
with open(base_dir / "tests" / "test_financial_reporting.py", "w") as f:
    f.write('''import pytest
from datetime import datetime
from bist_signal_bot.financials.reporting import format_financial_analysis_report_markdown
from bist_signal_bot.financials.models import FinancialAnalysisReport

def test_report_formatting():
    rep = FinancialAnalysisReport(
        report_id="1",
        symbol="ASELS",
        generated_at=datetime.now(),
        normalized_statements=[],
        ratios=[],
        trends=[],
        quality_assessments=[],
        sector_comparisons=[],
        key_findings=["Finding 1"],
        warnings=[],
        metadata={}
    )
    md = format_financial_analysis_report_markdown(rep)
    assert "Financial Analysis Report" in md
    assert "Finding 1" in md
    assert "research-only. It is not investment advice" in md
''')
