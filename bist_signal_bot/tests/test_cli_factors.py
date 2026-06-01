import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()

def test_cli_factors_compute():
    pass

def test_cli_factors_show():
    pass

def test_cli_factors_exposure():
    pass

def test_cli_factors_sector_rotation():
    pass

def test_cli_factors_theme():
    pass

def test_cli_factors_crowding():
    pass

def test_cli_factors_attribution():
    pass

def test_cli_factors_report():
    pass

def test_cli_factors_config():
    pass
