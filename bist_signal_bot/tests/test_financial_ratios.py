import pytest
from datetime import datetime
from bist_signal_bot.financials.ratios import FinancialRatioCalculator
from bist_signal_bot.financials.models import NormalizedFinancialStatement, FinancialPeriodType

def test_gross_margin():
    calc = FinancialRatioCalculator()
    stmt = NormalizedFinancialStatement(
        normalized_id="1", symbol="ASELS", fiscal_year=2024, fiscal_period="Q4",
        period_type=FinancialPeriodType.QUARTERLY, period_end=datetime.now(), currency="TRY",
        source_records=[], warnings=[], metadata={},
        revenue=100.0, gross_profit=40.0, net_income=20.0, total_assets=200.0, total_equity=100.0
    )
    ratios = calc.calculate_ratios(stmt)
    gm = next((r for r in ratios if r.name == "gross_margin"), None)
    assert gm is not None
    assert gm.value == 0.4

def test_debt_to_equity():
    calc = FinancialRatioCalculator()
    stmt = NormalizedFinancialStatement(
        normalized_id="1", symbol="ASELS", fiscal_year=2024, fiscal_period="Q4",
        period_type=FinancialPeriodType.QUARTERLY, period_end=datetime.now(), currency="TRY",
        source_records=[], warnings=[], metadata={},
        total_debt=50.0, total_equity=100.0
    )
    ratios = calc.calculate_ratios(stmt)
    de = next((r for r in ratios if r.name == "debt_to_equity"), None)
    assert de is not None
    assert de.value == 0.5

def test_zero_denominator():
    calc = FinancialRatioCalculator()
    stmt = NormalizedFinancialStatement(
        normalized_id="1", symbol="ASELS", fiscal_year=2024, fiscal_period="Q4",
        period_type=FinancialPeriodType.QUARTERLY, period_end=datetime.now(), currency="TRY",
        source_records=[], warnings=[], metadata={},
        revenue=0.0, gross_profit=40.0
    )
    ratios = calc.calculate_ratios(stmt)
    gm = next((r for r in ratios if r.name == "gross_margin"), None)
    assert gm is None
