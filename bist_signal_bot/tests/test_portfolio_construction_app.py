from pathlib import Path

from bist_signal_bot.app.portfolio_construction_app import (
    create_portfolio_candidate_builder,
    create_correlation_analyzer,
    create_risk_budget_calculator,
    create_portfolio_constraint_engine,
    create_portfolio_weighting_engine,
    create_rebalance_simulator,
    create_diversification_scorer,
    create_portfolio_construction_scorer,
    create_portfolio_construction_store
)

class MockSettings:
    pass

def test_create_risk_budget_calculator():
    settings = MockSettings()
    calculator = create_risk_budget_calculator(settings=settings)
    assert calculator is not None
    assert type(calculator).__name__ == 'RiskBudgetCalculator'

def test_other_factories():
    settings = MockSettings()
    assert create_portfolio_candidate_builder(settings=settings) is not None
    assert create_correlation_analyzer(settings=settings) is not None
    assert create_portfolio_constraint_engine(settings=settings) is not None
    assert create_portfolio_weighting_engine(settings=settings) is not None
    assert create_rebalance_simulator(settings=settings) is not None
    assert create_diversification_scorer(settings=settings) is not None
    assert create_portfolio_construction_scorer(settings=settings) is not None
    assert create_portfolio_construction_store(settings=settings, base_dir=Path('.')) is not None

def test_create_portfolio_construction_scorer():
    settings = MockSettings()
    scorer = create_portfolio_construction_scorer(settings=settings)
    assert scorer is not None
    assert type(scorer).__name__ == 'PortfolioConstructionScorer'

def test_create_diversification_scorer():
    settings = MockSettings()
    scorer = create_diversification_scorer(settings=settings)
    assert scorer is not None
    assert type(scorer).__name__ == 'DiversificationScorer'
