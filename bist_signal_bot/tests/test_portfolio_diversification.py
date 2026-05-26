import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.portfolio_construction.diversification import DiversificationScorer
from bist_signal_bot.portfolio_construction.models import PortfolioPositionResearch

def test_diversification_scorer():
    settings = Settings()
    scorer = DiversificationScorer(settings)

    # perfectly diversified weights
    eff_n = scorer.effective_number_of_positions({"A": 0.5, "B": 0.5})
    assert eff_n == 2.0

    # very concentrated
    eff_n = scorer.effective_number_of_positions({"A": 0.9, "B": 0.1})
    assert eff_n < 2.0

    p1 = PortfolioPositionResearch(position_id="1", symbol="A", sector="TECH", current_weight=0.0, target_weight=0.5, weight_delta=0.5)
    p2 = PortfolioPositionResearch(position_id="2", symbol="B", sector="BANK", current_weight=0.0, target_weight=0.5, weight_delta=0.5)

    score = scorer.score_diversification([p1, p2])
    assert score is not None
    assert score > 0
