import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.portfolio_construction.scoring import PortfolioConstructionScorer
from bist_signal_bot.portfolio_construction.models import PortfolioConstraintViolation, ConstraintSeverity, ConstraintType, PortfolioConstructionStatus

def test_portfolio_construction_scorer():
    settings = Settings()
    scorer = PortfolioConstructionScorer(settings)

    v = PortfolioConstraintViolation(
        violation_id="1", constraint_type=ConstraintType.MAX_SYMBOL_WEIGHT,
        severity=ConstraintSeverity.CRITICAL, message="Test"
    )

    c_score = scorer.score_constraints([v])
    assert c_score == 70.0 # 100 - 30 penalty

    status = scorer.derive_status(80.0, [v], [])
    assert status == PortfolioConstructionStatus.FAIL # critical violation forces FAIL
