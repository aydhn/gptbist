import pytest
from bist_signal_bot.config.settings import get_settings

def test_healthcheck_includes_disclosures():
    settings = get_settings()
    assert hasattr(settings, "ENABLE_DISCLOSURE_INTELLIGENCE")
    assert settings.ENABLE_DISCLOSURE_INTELLIGENCE is True
    assert getattr(settings, "DISCLOSURE_RESEARCH_ONLY", False) is True
