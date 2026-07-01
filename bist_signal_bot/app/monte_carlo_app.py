import logging
from pathlib import Path

from bist_signal_bot.config.settings import Settings

from bist_signal_bot.monte_carlo.randomness import MonteCarloRandomState
from bist_signal_bot.monte_carlo.resampling import ResamplingEngine
from bist_signal_bot.monte_carlo.bootstrap import BootstrapEngine
from bist_signal_bot.monte_carlo.path_simulation import PathSimulator
from bist_signal_bot.monte_carlo.trade_simulation import TradeSimulationAdapter
from bist_signal_bot.monte_carlo.cost_randomization import CostRandomizer
from bist_signal_bot.monte_carlo.distributions import DistributionAnalyzer
from bist_signal_bot.monte_carlo.reality_check import RealityCheckEngine
from bist_signal_bot.monte_carlo.risk_metrics import MonteCarloRiskAnalyzer
from bist_signal_bot.monte_carlo.scoring import MonteCarloRobustnessScorer
from bist_signal_bot.monte_carlo.storage import MonteCarloStore
from bist_signal_bot.monte_carlo.engine import MonteCarloEngine, MonteCarloComponents

def create_monte_carlo_random_state(settings: Settings | None = None) -> MonteCarloRandomState:
    return MonteCarloRandomState()

def create_resampling_engine(settings: Settings | None = None) -> ResamplingEngine:
    rs = create_monte_carlo_random_state(settings)
    return ResamplingEngine(random_state=rs)

def create_bootstrap_engine(settings: Settings | None = None) -> BootstrapEngine:
    re = create_resampling_engine(settings)
    return BootstrapEngine(resampling_engine=re)

def create_path_simulator(settings: Settings | None = None) -> PathSimulator:
    return PathSimulator()

def create_trade_simulation_adapter(settings: Settings | None = None) -> TradeSimulationAdapter:
    logger = logging.getLogger("bist_signal_bot.monte_carlo.trade_simulation")
    return TradeSimulationAdapter(logger=logger)

def create_cost_randomizer(settings: Settings | None = None) -> CostRandomizer:
    rs = create_monte_carlo_random_state(settings)
    return CostRandomizer(random_state=rs)

def create_distribution_analyzer(settings: Settings | None = None) -> DistributionAnalyzer:
    return DistributionAnalyzer()

def create_reality_check_engine(settings: Settings | None = None) -> RealityCheckEngine:
    return RealityCheckEngine(settings=settings)

def create_monte_carlo_risk_analyzer(settings: Settings | None = None) -> MonteCarloRiskAnalyzer:
    return MonteCarloRiskAnalyzer()

def create_monte_carlo_store(settings: Settings | None = None, base_dir: Path | None = None) -> MonteCarloStore:
    logger = logging.getLogger("bist_signal_bot.monte_carlo.storage")
    store = MonteCarloStore(settings=settings, logger=logger)
    if base_dir:
        store.base_dir = base_dir
    return store

def create_monte_carlo_engine(settings: Settings | None = None, base_dir: Path | None = None) -> MonteCarloEngine:
    s = settings or Settings()
    logger = logging.getLogger("bist_signal_bot.monte_carlo")

    trade_adapter = create_trade_simulation_adapter(s)
    bootstrap_engine = create_bootstrap_engine(s)
    path_simulator = create_path_simulator(s)
    cost_randomizer = create_cost_randomizer(s)
    dist_analyzer = create_distribution_analyzer(s)
    risk_analyzer = create_monte_carlo_risk_analyzer(s)
    reality_check = create_reality_check_engine(s)
    scorer = MonteCarloRobustnessScorer()
    store = create_monte_carlo_store(s, base_dir)

    components = MonteCarloComponents(
        trade_adapter=trade_adapter,
        bootstrap_engine=bootstrap_engine,
        path_simulator=path_simulator,
        cost_randomizer=cost_randomizer,
        distribution_analyzer=dist_analyzer,
        risk_analyzer=risk_analyzer,
        reality_check=reality_check,
        scorer=scorer,
        store=store,
        settings=s,
        logger=logger
    )

    return MonteCarloEngine(components=components)
