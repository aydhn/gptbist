import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from bist_signal_bot.config.settings import Settings

def test_healthcheck_leaderboard_fields():
    s = Settings()
    health = {
        "leaderboard_enabled": s.ENABLE_RESEARCH_LEADERBOARD,
        "policies_loaded": True,
        "latest_leaderboard_status": "PASS",
        "ranking_engine_capable": True,
        "selection_engine_capable": True
    }
    assert health["leaderboard_enabled"] is True
