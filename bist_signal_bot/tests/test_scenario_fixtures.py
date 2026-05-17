import pytest
import pandas as pd
from bist_signal_bot.scenarios.fixtures import ScenarioFixtureBuilder
from bist_signal_bot.scenarios.models import ScenarioFixtureType

def test_mock_ohlcv():
    builder = ScenarioFixtureBuilder()
    data = builder.build_mock_ohlcv(["ASELS", "THYAO"], rows=50)

    assert "ASELS" in data
    assert "THYAO" in data
    assert len(data["ASELS"]) == 50
    assert "Close" in data["ASELS"].columns

    # Determinism
    data2 = builder.build_mock_ohlcv(["ASELS", "THYAO"], rows=50)
    pd.testing.assert_frame_equal(data["ASELS"], data2["ASELS"])

def test_write_fixtures_to_sandbox(tmp_path):
    builder = ScenarioFixtureBuilder()
    fix = builder.build_mock_symbol_universe(["ASELS"])

    paths = builder.write_fixtures_to_sandbox([fix], tmp_path)

    assert fix.fixture_id in paths
    assert paths[fix.fixture_id].exists()
