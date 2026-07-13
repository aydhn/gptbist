from bist_signal_bot.app.factors_app import create_factor_scorer
from bist_signal_bot.factors.scoring import FactorScorer

class MockSettings:
    pass

def test_create_factor_scorer():
    scorer = create_factor_scorer()
    assert isinstance(scorer, FactorScorer)
    assert scorer.settings is None

def test_create_factor_scorer_with_settings():
    settings = MockSettings()
    scorer = create_factor_scorer(settings=settings)
    assert isinstance(scorer, FactorScorer)
    assert scorer.settings is settings
