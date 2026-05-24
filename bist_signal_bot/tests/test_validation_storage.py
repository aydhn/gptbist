import pytest
from pathlib import Path
from bist_signal_bot.validation.storage import ValidationStore
from bist_signal_bot.validation.models import StrategyValidationResult, StrategyValidationRequest

def test_validation_store_save_load(tmp_path):
    store = ValidationStore(tmp_path)
    req = StrategyValidationRequest(strategy_name="MA", symbols=["ASELS"])
    res = StrategyValidationResult(validation_id="123", request=req)

    paths = store.save_result(res)
    assert "main" in paths
    assert Path(paths["main"]).exists()

def test_validation_store_load_latest(tmp_path):
    store = ValidationStore(tmp_path)
    req1 = StrategyValidationRequest(strategy_name="MA", symbols=["ASELS"])
    res1 = StrategyValidationResult(validation_id="1", request=req1)

    store.save_result(res1)

    latest_ma = store.load_latest_result("MA")
    assert latest_ma is not None
    assert latest_ma.validation_id == "1"
