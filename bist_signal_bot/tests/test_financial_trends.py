import pytest
from datetime import datetime
from bist_signal_bot.financials.trends import FinancialTrendAnalyzer
from bist_signal_bot.financials.models import NormalizedFinancialStatement, FinancialPeriodType

def test_yoy_qoq_calculation():
    analyzer = FinancialTrendAnalyzer()

    assert analyzer.yoy_change(120.0, 100.0) == 0.2
    assert analyzer.qoq_change(110.0, 100.0) == 0.1
    assert analyzer.yoy_change(100.0, 0.0) is None
