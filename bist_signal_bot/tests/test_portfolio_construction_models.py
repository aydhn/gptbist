import pytest
from bist_signal_bot.portfolio_construction.models import PortfolioCandidate, PortfolioConstructionRequest

def test_portfolio_candidate_validation_clamp():
    # Final candidate score should be clamped to 0-100
    candidate = PortfolioCandidate(
        candidate_id="test1",
        symbol="asels",
        final_candidate_score=150.0
    )
    assert candidate.symbol == "ASELS"
    assert candidate.final_candidate_score == 100.0

    candidate2 = PortfolioCandidate(
        candidate_id="test2",
        symbol="thyao",
        final_candidate_score=-10.0
    )
    assert candidate2.final_candidate_score == 0.0

def test_portfolio_construction_request_validation():
    with pytest.raises(ValueError, match="max_positions must be positive"):
        PortfolioConstructionRequest(
            request_id="test",
            symbols=["ASELS"],
            strategy_names=["auto"],
            weighting_method="EQUAL_WEIGHT",
            max_positions=-1,
            portfolio_notional=10000.0,
            current_weights={}
        )

    with pytest.raises(ValueError, match="portfolio_notional must be positive"):
        PortfolioConstructionRequest(
            request_id="test",
            symbols=["ASELS"],
            strategy_names=["auto"],
            weighting_method="EQUAL_WEIGHT",
            max_positions=10,
            portfolio_notional=0.0,
            current_weights={}
        )

    with pytest.raises(ValueError, match="weights cannot be negative"):
        PortfolioConstructionRequest(
            request_id="test",
            symbols=["ASELS"],
            strategy_names=["auto"],
            weighting_method="EQUAL_WEIGHT",
            max_positions=10,
            portfolio_notional=10000.0,
            current_weights={"ASELS": -0.5}
        )
