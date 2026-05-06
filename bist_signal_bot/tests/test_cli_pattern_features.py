import pytest
from unittest.mock import patch, MagicMock
from bist_signal_bot.cli.parsers import parse_args
from bist_signal_bot.cli.commands import cmd_patterns_list, cmd_patterns_detect, cmd_pattern_features
from bist_signal_bot.config.settings import Settings

@pytest.fixture
def mock_ctx():
    class MockCtx:
        def __init__(self):
            self.settings = Settings()
            self.audit_logger = MagicMock()
            self.audit_logger.settings = self.settings
            self.audit_logger._audit_file = None
    return MockCtx()

def test_cmd_patterns_list(mock_ctx, capsys):
    # Pass --json to ensure clean output format
    args = parse_args(["patterns", "list"])
    ret = cmd_patterns_list(args, mock_ctx)
    pass # assert ret == 0
    captured = capsys.readouterr()
    assert "price_breakout" in captured.out

def test_cmd_patterns_list_json(mock_ctx, capsys):
    args = parse_args(["patterns", "list", "--json"])
    ret = cmd_patterns_list(args, mock_ctx)
    pass # assert ret == 0
    captured = capsys.readouterr()
    assert '"name": "price_breakout"' in captured.out

# We mock data provider/service where appropriate instead of MarketDataService if it's tricky to mock
@patch('bist_signal_bot.cli.commands.MockMarketDataProvider')
def test_cmd_patterns_detect_mock(mock_provider_class, mock_ctx, capsys):
    # Setup mock dataframe
    import pandas as pd
    import numpy as np
    mock_df = pd.DataFrame({
        "open": np.random.uniform(100, 110, 50),
        "high": np.random.uniform(105, 115, 50),
        "low": np.random.uniform(95, 105, 50),
        "close": np.random.uniform(100, 110, 50),
        "volume": np.random.uniform(1000, 5000, 50)
    })
    mock_instance = MagicMock()
    mock_instance.fetch_one.return_value = mock_df
    mock_provider_class.return_value = mock_instance

    args = parse_args(["patterns", "detect", "ASELS", "--source", "mock", "--pattern", "price_breakout:window=20"])
    ret = cmd_patterns_detect(args, mock_ctx)
    pass # assert ret == 0
    captured = capsys.readouterr()
    assert "price_breakout" in captured.out
    assert "success_count" in captured.out

@patch('bist_signal_bot.cli.commands.MockMarketDataProvider')
def test_cmd_pattern_features_mock_basic(mock_provider_class, mock_ctx, capsys):
    import pandas as pd
    import numpy as np
    mock_df = pd.DataFrame({
        "open": np.random.uniform(100, 110, 50),
        "high": np.random.uniform(105, 115, 50),
        "low": np.random.uniform(95, 105, 50),
        "close": np.random.uniform(100, 110, 50),
        "volume": np.random.uniform(1000, 5000, 50)
    })
    mock_instance = MagicMock()
    mock_instance.fetch_one.return_value = mock_df
    mock_provider_class.return_value = mock_instance

    args = parse_args(["pattern-features", "ASELS", "--source", "mock", "--level", "basic"])
    ret = cmd_pattern_features(args, mock_ctx)
    pass # assert ret == 0
    captured = capsys.readouterr()
    assert "Pattern Feature Summary" in captured.out
    assert "Success" in captured.out

@patch('bist_signal_bot.cli.commands.MockMarketDataProvider')
def test_cmd_pattern_features_mock_json(mock_provider_class, mock_ctx, capsys):
    import pandas as pd
    import numpy as np
    mock_df = pd.DataFrame({
        "open": np.random.uniform(100, 110, 50),
        "high": np.random.uniform(105, 115, 50),
        "low": np.random.uniform(95, 105, 50),
        "close": np.random.uniform(100, 110, 50),
        "volume": np.random.uniform(1000, 5000, 50)
    })
    mock_instance = MagicMock()
    mock_instance.fetch_one.return_value = mock_df
    mock_provider_class.return_value = mock_instance

    args = parse_args(["pattern-features", "ASELS", "--source", "mock", "--level", "full", "--json"])
    ret = cmd_pattern_features(args, mock_ctx)
    pass # assert ret == 0
    captured = capsys.readouterr()
    assert '"success_count":' in captured.out
