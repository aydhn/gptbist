from datetime import datetime
from bist_signal_bot.valuation.market_inputs import ValuationMarketInputBuilder

def test_builder_calculations():
    builder = ValuationMarketInputBuilder()
    assert builder.calculate_market_cap(10.0, 100.0) == 1000.0
    assert builder.calculate_net_debt(500.0, 100.0) == 400.0
    assert builder.calculate_enterprise_value(1000.0, 400.0) == 1400.0
