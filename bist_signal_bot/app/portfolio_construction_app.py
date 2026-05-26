from pathlib import Path
from typing import Optional

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.portfolio_construction.candidates import PortfolioCandidateBuilder
from bist_signal_bot.portfolio_construction.correlation import CorrelationAnalyzer
from bist_signal_bot.portfolio_construction.risk_budget import RiskBudgetCalculator
from bist_signal_bot.portfolio_construction.constraints import PortfolioConstraintEngine
from bist_signal_bot.portfolio_construction.weighting import PortfolioWeightingEngine
from bist_signal_bot.portfolio_construction.rebalance import RebalanceSimulator
from bist_signal_bot.portfolio_construction.diversification import DiversificationScorer
from bist_signal_bot.portfolio_construction.scoring import PortfolioConstructionScorer
from bist_signal_bot.portfolio_construction.engine import PortfolioConstructionEngine
from bist_signal_bot.portfolio_construction.storage import PortfolioConstructionStore

def create_portfolio_candidate_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> PortfolioCandidateBuilder:
    return PortfolioCandidateBuilder(settings=settings or get_settings())

def create_correlation_analyzer(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> CorrelationAnalyzer:
    return CorrelationAnalyzer()

def create_risk_budget_calculator(settings: Optional[Settings] = None) -> RiskBudgetCalculator:
    return RiskBudgetCalculator()

def create_portfolio_constraint_engine(settings: Optional[Settings] = None) -> PortfolioConstraintEngine:
    return PortfolioConstraintEngine(settings=settings or get_settings())

def create_portfolio_weighting_engine(settings: Optional[Settings] = None) -> PortfolioWeightingEngine:
    return PortfolioWeightingEngine(settings=settings or get_settings())

def create_rebalance_simulator(settings: Optional[Settings] = None) -> RebalanceSimulator:
    return RebalanceSimulator(settings=settings or get_settings())

def create_diversification_scorer(settings: Optional[Settings] = None) -> DiversificationScorer:
    return DiversificationScorer(settings=settings or get_settings())

def create_portfolio_construction_scorer(settings: Optional[Settings] = None) -> PortfolioConstructionScorer:
    return PortfolioConstructionScorer(settings=settings or get_settings())

def create_portfolio_construction_store(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> PortfolioConstructionStore:
    return PortfolioConstructionStore(settings=settings or get_settings(), base_dir=base_dir)

def create_portfolio_construction_engine(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> PortfolioConstructionEngine:
    s = settings or get_settings()
    return PortfolioConstructionEngine(
        candidate_builder=create_portfolio_candidate_builder(s, base_dir),
        correlation_analyzer=create_correlation_analyzer(s, base_dir),
        risk_budget_calculator=create_risk_budget_calculator(s),
        constraint_engine=create_portfolio_constraint_engine(s),
        weighting_engine=create_portfolio_weighting_engine(s),
        rebalance_simulator=create_rebalance_simulator(s),
        diversification_scorer=create_diversification_scorer(s),
        portfolio_scorer=create_portfolio_construction_scorer(s),
        store=create_portfolio_construction_store(s, base_dir),
        settings=s
    )
