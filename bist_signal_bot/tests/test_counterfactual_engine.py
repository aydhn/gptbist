
from bist_signal_bot.whatif.counterfactual import CounterfactualEngine
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.whatif.assumptions import AssumptionOverrideEngine

def test_counterfactual_engine():
    settings = Settings()
    assump = AssumptionOverrideEngine(None)
    engine = CounterfactualEngine(settings, assump, None)
    # Without invoking actual run_portfolio_construction, just verify instantiation
    assert engine is not None
