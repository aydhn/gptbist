from pathlib import Path
from bist_signal_bot.portfolio_ledger.storage import PortfolioLedgerStore
from bist_signal_bot.portfolio_ledger.ledger import ResearchPortfolioLedger
from bist_signal_bot.portfolio_ledger.lifecycle import PortfolioLifecycleManager
from bist_signal_bot.portfolio_ledger.valuation import PortfolioValuationEngine
from bist_signal_bot.portfolio_ledger.attribution import PortfolioAttributionEngine
from bist_signal_bot.portfolio_ledger.outcomes import PortfolioOutcomeEvaluator
from bist_signal_bot.portfolio_ledger.rebalance_tracking import RebalanceTracker
from bist_signal_bot.portfolio_ledger.nav import PortfolioNavBuilder
from bist_signal_bot.storage.paths import get_portfolio_ledger_dir

def create_portfolio_ledger_store(settings=None, base_dir: Path | None = None) -> PortfolioLedgerStore:
    if base_dir is None:
        base_dir = get_portfolio_ledger_dir(settings)
    return PortfolioLedgerStore(base_dir=base_dir)

def create_research_portfolio_ledger(settings=None, base_dir: Path | None = None) -> ResearchPortfolioLedger:
    store = create_portfolio_ledger_store(settings, base_dir)
    return ResearchPortfolioLedger(store=store)

def create_portfolio_lifecycle_manager(settings=None, base_dir: Path | None = None) -> PortfolioLifecycleManager:
    store = create_portfolio_ledger_store(settings, base_dir)
    return PortfolioLifecycleManager(store=store)

def create_portfolio_valuation_engine(settings=None, base_dir: Path | None = None) -> PortfolioValuationEngine:
    # In a real app we'd inject data_service here
    return PortfolioValuationEngine(data_service=None)

def create_portfolio_attribution_engine(settings=None) -> PortfolioAttributionEngine:
    return PortfolioAttributionEngine()

def create_portfolio_outcome_evaluator(settings=None, base_dir: Path | None = None) -> PortfolioOutcomeEvaluator:
    return PortfolioOutcomeEvaluator(data_service=None)

def create_rebalance_tracker(settings=None) -> RebalanceTracker:
    return RebalanceTracker()

def create_portfolio_nav_builder(settings=None, base_dir: Path | None = None) -> PortfolioNavBuilder:
    store = create_portfolio_ledger_store(settings, base_dir)
    return PortfolioNavBuilder(store=store)
