import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()

def test_cli_whatif():
    # Placeholder for CLI what-if tests
    pass
