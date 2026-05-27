import pytest
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
