import pytest
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
