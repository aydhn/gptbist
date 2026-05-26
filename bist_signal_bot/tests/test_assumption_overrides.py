
from bist_signal_bot.whatif.assumptions import AssumptionOverrideEngine
from bist_signal_bot.config.settings import Settings

def test_assumption_override_engine():
    engine = AssumptionOverrideEngine(logger=None)
    settings = Settings()
    ctx = engine.apply_overrides(settings, [])
    assert isinstance(ctx, dict)
