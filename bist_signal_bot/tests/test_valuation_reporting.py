import pandas as pd
from datetime import datetime
from bist_signal_bot.valuation.reporting import format_market_input_text, multiples_to_dataframe
from bist_signal_bot.valuation.models import ValuationMarketInput

def test_reporting_formatting():
    inp = ValuationMarketInput(
        input_id="123", symbol="TEST", as_of=datetime.utcnow(), price=10.0,
        warnings=["Some warning"]
    )

    text = format_market_input_text(inp)
    assert "TEST" in text
    assert "10.0 TRY" in text
    assert "Some warning" in text

def test_dataframe_conversion():
    # If empty
    df = multiples_to_dataframe([])
    assert isinstance(df, pd.DataFrame)
    assert df.empty
