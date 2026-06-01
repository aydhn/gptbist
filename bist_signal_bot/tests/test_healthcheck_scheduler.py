import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
def test_healthcheck_imports():
    from bist_signal_bot.scheduler.models import ScheduledJobType
    assert ScheduledJobType.HEALTHCHECK.value == "HEALTHCHECK"
