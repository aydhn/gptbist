import pytest
from datetime import datetime
from bist_signal_bot.valuation.models import ValuationMarketInput

def test_valuation_market_input_normalization():
    v = ValuationMarketInput(
        input_id="123",
        symbol="asels",
        as_of=datetime.utcnow()
    )
    assert v.symbol == "ASELS"

def test_valuation_market_input_validation():
    with pytest.raises(ValueError):
        ValuationMarketInput(
            input_id="123",
            symbol="ASELS",
            as_of=datetime.utcnow(),
            price=-10.0
        )
