import pytest
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.app.strategy_registry_app import create_strategy_scorecard_builder

def test_create_strategy_scorecard_builder():
    settings = Settings()
    base_dir = Path("/tmp")
    builder = create_strategy_scorecard_builder(settings, base_dir)
    assert builder is not None
    assert type(builder).__name__ == "StrategyScorecardBuilder"
