import pytest
from pathlib import Path
from bist_signal_bot.app.context_fusion_app import create_composite_research_scorer
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.context_fusion.scoring import CompositeResearchScorer

def test_create_composite_research_scorer_with_settings():
    """Test that create_composite_research_scorer correctly passes the provided settings."""
    custom_settings = Settings(CONTEXT_STRONG_SUPPORT_THRESHOLD=85.0)
    scorer = create_composite_research_scorer(settings=custom_settings)

    assert type(scorer).__name__ == "CompositeResearchScorer"
    assert scorer.settings is custom_settings
    assert getattr(scorer.settings, "CONTEXT_STRONG_SUPPORT_THRESHOLD", None) == 85.0

def test_create_composite_research_scorer_no_settings():
    """Test that create_composite_research_scorer creates default settings if none are provided."""
    scorer = create_composite_research_scorer(settings=None)

    assert type(scorer).__name__ == "CompositeResearchScorer"
    assert getattr(scorer, "settings", None) is not None
    assert isinstance(scorer.settings, Settings)
