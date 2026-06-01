import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.app.healthcheck_scenarios import check_scenarios
from bist_signal_bot.config.settings import Settings

def test_check_scenarios():
    settings = Settings(
        ENABLE_SCENARIO_RUNNER=True,
        SCENARIO_DEFAULT_SYMBOLS="TEST"
    )
    res = check_scenarios(settings)
    assert res["enabled"] is True
    assert res["default_symbols"] == "TEST"
    assert res["registry_scenario_count"] > 0
    assert res["smoke_scenario_build_capable"] is True
    assert res["scenario_runner_instantiable"] is True
    assert res["validator_capable"] is True
    assert res["golden_manager_capable"] is True
    assert "error" not in res
