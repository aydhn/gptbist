from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.portfolio_research.engine import PortfolioResearchEngine
from bist_signal_bot.portfolio_research.storage import PortfolioResearchStore
from bist_signal_bot.portfolio_research.allocation import ResearchAllocationEngine
from bist_signal_bot.portfolio_research.rebalance import RebalancePlanner
from bist_signal_bot.portfolio_research.constraints import PortfolioConstraintEngine
from bist_signal_bot.portfolio_research.exposure import PortfolioExposureAnalyzer
from bist_signal_bot.portfolio_research.correlation import PortfolioCorrelationAnalyzer
from bist_signal_bot.portfolio_research.simulation import BasketSimulator
from bist_signal_bot.storage.paths import get_portfolio_research_dir

def create_portfolio_research_store(settings: Settings | None = None, base_dir: Path | None = None) -> PortfolioResearchStore:
    if base_dir is None:
        base_dir = get_portfolio_research_dir(settings)
    return PortfolioResearchStore(base_dir)

def create_allocation_engine(settings: Settings | None = None) -> ResearchAllocationEngine:
    return ResearchAllocationEngine()

def create_rebalance_planner(settings: Settings | None = None) -> RebalancePlanner:
    return RebalancePlanner()

def create_portfolio_research_engine(settings: Settings | None = None, base_dir: Path | None = None, **kwargs) -> PortfolioResearchEngine:
    if settings is None:
        settings = Settings()

    store = create_portfolio_research_store(settings, base_dir)
    return PortfolioResearchEngine(
        store=store,
        allocation_engine=create_allocation_engine(settings),
        constraint_engine=PortfolioConstraintEngine(),
        exposure_analyzer=PortfolioExposureAnalyzer(),
        correlation_analyzer=PortfolioCorrelationAnalyzer(),
        rebalance_planner=create_rebalance_planner(settings),
        basket_simulator=BasketSimulator(),
        settings=settings,
        **kwargs
    )
