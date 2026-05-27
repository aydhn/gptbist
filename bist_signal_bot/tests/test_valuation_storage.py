import pytest
from pathlib import Path
from datetime import datetime
from bist_signal_bot.valuation.storage import ValuationStore
from bist_signal_bot.valuation.models import ValuationMarketInput
from bist_signal_bot.config.settings import Settings

def test_valuation_storage_append_load(tmp_path):
    settings = Settings(VALUATION_DIR_NAME=str(tmp_path.name))
    store = ValuationStore(settings=settings, base_dir=tmp_path)

    inp = ValuationMarketInput(
        input_id="123", symbol="TEST", as_of=datetime.utcnow(), price=10.0
    )

    store.append_market_input(inp)

    loaded = store.load_market_inputs("TEST")
    assert len(loaded) == 1
    assert loaded[0].price == 10.0
    assert loaded[0].symbol == "TEST"
