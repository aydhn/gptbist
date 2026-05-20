from pathlib import Path
from bist_signal_bot.config.settings import Settings

from bist_signal_bot.stress.returns import ReturnSeriesBuilder
from bist_signal_bot.stress.monte_carlo import MonteCarloSimulator
from bist_signal_bot.stress.shocks import ShockScenarioEngine
from bist_signal_bot.stress.drawdown import DrawdownSimulator
from bist_signal_bot.stress.risk_of_ruin import RiskOfRuinEstimator
from bist_signal_bot.stress.storage import StressStore
from bist_signal_bot.stress.engine import StressTestEngine

def create_stress_store(settings: Settings | None = None, base_dir: Path | None = None) -> StressStore:
    return StressStore(base_dir=base_dir)

def create_monte_carlo_simulator(settings: Settings | None = None) -> MonteCarloSimulator:
    return MonteCarloSimulator()

def create_shock_scenario_engine(settings: Settings | None = None) -> ShockScenarioEngine:
    return ShockScenarioEngine()

def create_stress_test_engine(settings: Settings | None = None, base_dir: Path | None = None) -> StressTestEngine:
    return_builder = ReturnSeriesBuilder()
    monte_carlo_simulator = create_monte_carlo_simulator(settings)
    shock_engine = create_shock_scenario_engine(settings)
    drawdown_simulator = DrawdownSimulator()
    risk_of_ruin_estimator = RiskOfRuinEstimator()
    store = create_stress_store(settings, base_dir)

    # Needs portfolio engine to fetch latest snapshot
    try:
        from bist_signal_bot.app.portfolio_app import create_portfolio_research_engine
        portfolio_engine = create_portfolio_research_engine(settings, base_dir)
    except Exception:
        portfolio_engine = None

    return StressTestEngine(
        return_builder=return_builder,
        monte_carlo_simulator=monte_carlo_simulator,
        shock_engine=shock_engine,
        drawdown_simulator=drawdown_simulator,
        risk_of_ruin_estimator=risk_of_ruin_estimator,
        portfolio_research_engine=portfolio_engine,
        data_service=None,
        store=store,
        settings=settings
    )
