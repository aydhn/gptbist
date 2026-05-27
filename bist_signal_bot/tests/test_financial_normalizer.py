import pytest
from datetime import datetime
from bist_signal_bot.financials.normalizer import FinancialStatementNormalizer
from bist_signal_bot.financials.models import FinancialStatementRecord, FinancialDataStatus

def test_normalizer_mapping():
    norm = FinancialStatementNormalizer()
    assert norm.map_item_name("Satış Gelirleri") == "revenue"
    assert norm.map_item_name("Net Dönem Karı") == "net_income"
    assert norm.map_item_name("Favök") == "ebitda"

def test_normalizer_numeric_coercion():
    norm = FinancialStatementNormalizer()
    assert norm.coerce_numeric("1,000.50") == 1000.5
    assert norm.coerce_numeric(100) == 100.0
    assert norm.coerce_numeric(None) is None
    assert norm.coerce_numeric("abc") is None

def test_normalizer_normalize():
    norm = FinancialStatementNormalizer()
    rec = FinancialStatementRecord(
        record_id="1",
        symbol="ASELS",
        period_end=datetime.now(),
        currency="TRY",
        values={"satış gelirleri": "100", "net dönem karı": "20"},
        source="csv",
        status=FinancialDataStatus.RAW_IMPORTED,
        warnings=[],
        metadata={},
        fiscal_year=2024,
        fiscal_period="Q4"
    )
    res = norm.normalize_records([rec])
    assert len(res) == 1
    stmt = res[0]
    assert stmt.revenue == 100.0
    assert stmt.net_income == 20.0
