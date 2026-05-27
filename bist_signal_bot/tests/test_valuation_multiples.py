import pytest
from datetime import datetime
from bist_signal_bot.valuation.multiples import ValuationMultipleCalculator
from bist_signal_bot.valuation.models import ValuationMarketInput

class MockStatement:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

def test_multiple_calculator_pe():
    calc = ValuationMultipleCalculator()
    inp = ValuationMarketInput(input_id="1", symbol="TEST", as_of=datetime.utcnow(), market_cap=1000.0)
    stmt = MockStatement(net_income=100.0)

    multiple = calc.calculate_pe(inp, stmt)
    assert multiple.value == 10.0

def test_multiple_calculator_zero_denominator():
    calc = ValuationMultipleCalculator()
    inp = ValuationMarketInput(input_id="1", symbol="TEST", as_of=datetime.utcnow(), market_cap=1000.0)
    stmt = MockStatement(net_income=0.0)

    multiple = calc.calculate_pe(inp, stmt)
    assert multiple.value is None
    assert any("zero" in w.lower() for w in multiple.warnings)

def test_multiple_calculator_negative_watch():
    calc = ValuationMultipleCalculator()
    inp = ValuationMarketInput(input_id="1", symbol="TEST", as_of=datetime.utcnow(), market_cap=1000.0)
    stmt = MockStatement(net_income=-100.0)

    multiple = calc.calculate_pe(inp, stmt)
    assert multiple.value == -10.0
    assert multiple.status.value == "WATCH"
