import pytest
import pandas as pd
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.portfolio_construction.weighting import PortfolioWeightingEngine
from bist_signal_bot.portfolio_construction.models import PortfolioCandidate

def test_weighting_engine_methods():
    settings = Settings()
    engine = PortfolioWeightingEngine(settings)

    c1 = PortfolioCandidate(candidate_id="1", symbol="A", raw_confidence=80, final_candidate_score=90)
    c2 = PortfolioCandidate(candidate_id="2", symbol="B", raw_confidence=20, final_candidate_score=10)

    # Equal weight
    weights = engine.equal_weight([c1, c2], max_positions=10)
    assert weights["A"] == 0.5
    assert weights["B"] == 0.5

    # Confidence weighted
    weights = engine.confidence_weighted([c1, c2], max_positions=10)
    assert weights["A"] == 0.8
    assert weights["B"] == 0.2

    # Score weighted
    weights = engine.score_weighted([c1, c2], max_positions=10)
    assert weights["A"] == 0.9
    assert weights["B"] == 0.1

    # Normalize
    weights = engine.normalize_weights({"A": 2.0, "B": 2.0})
    assert weights["A"] == 0.5
    assert weights["B"] == 0.5

def test_weighting_engine_missing_score_fallback():
    settings = Settings()
    engine = PortfolioWeightingEngine(settings)
    c1 = PortfolioCandidate(candidate_id="1", symbol="A", final_candidate_score=0.0)
    c2 = PortfolioCandidate(candidate_id="2", symbol="B", final_candidate_score=0.0)

    # Score weighted should fallback to equal weight if total score is 0
    weights = engine.score_weighted([c1, c2], max_positions=10)
    assert weights["A"] == 0.5
    assert weights["B"] == 0.5
