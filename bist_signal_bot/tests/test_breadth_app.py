from bist_signal_bot.app.breadth_app import create_breadth_scorer
from bist_signal_bot.breadth.scoring import BreadthScorer
from bist_signal_bot.config.settings import Settings

class MockSettings:
    pass

def test_create_breadth_scorer():
    scorer = create_breadth_scorer()
    assert isinstance(scorer, BreadthScorer)
    # BreadthScorer defaults to initializing a new Settings if none provided
    assert isinstance(scorer.settings, Settings)

def test_create_breadth_scorer_with_settings():
    settings = MockSettings()
    scorer = create_breadth_scorer(settings=settings)
    assert isinstance(scorer, BreadthScorer)
    assert scorer.settings is settings
