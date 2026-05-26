import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.portfolio_construction.candidates import PortfolioCandidateBuilder
from bist_signal_bot.portfolio_construction.models import PortfolioConstructionRequest, PortfolioWeightingMethod, PortfolioCandidate

def test_candidate_builder_mock_signal():
    settings = Settings()
    builder = PortfolioCandidateBuilder(settings)

    payload = {
        "symbol": "ASELS",
        "strategy_name": "trend",
        "calibrated_confidence": 75.0,
        "raw_confidence": 60.0
    }

    candidate = builder.candidate_from_signal(payload)
    assert candidate.symbol == "ASELS"
    assert candidate.calibrated_confidence == 75.0
    assert candidate.raw_confidence == 60.0

def test_candidate_builder_blocked_and_inactive_symbols():
    settings = Settings()
    builder = PortfolioCandidateBuilder(settings)

    c1 = PortfolioCandidate(candidate_id="1", symbol="ASELS", metadata={"is_blocked": True})
    c2 = PortfolioCandidate(candidate_id="2", symbol="THYAO", metadata={"is_inactive": True})
    c3 = PortfolioCandidate(candidate_id="3", symbol="GARAN")

    req = PortfolioConstructionRequest(
        request_id="test", symbols=["ASELS", "THYAO", "GARAN"], strategy_names=["auto"],
        weighting_method="EQUAL_WEIGHT", max_positions=10, portfolio_notional=10000.0, current_weights={}
    )

    filtered = builder.filter_candidates([c1, c2, c3], req)
    assert len(filtered) == 1
    assert filtered[0].symbol == "GARAN"
