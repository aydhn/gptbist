from pathlib import Path
from bist_signal_bot.app.events_app import create_event_risk_engine
from bist_signal_bot.events.risk import EventRiskEngine

class MockSettings:
    pass

def test_create_event_risk_engine_default():
    engine = create_event_risk_engine()
    assert isinstance(engine, EventRiskEngine)
    assert engine.calendar is not None
    assert engine.window_builder is not None
    assert engine.policy_manager is not None

def test_create_event_risk_engine_with_settings_and_base_dir():
    settings = MockSettings()
    base_dir = Path("/tmp/test_events_app")
    engine = create_event_risk_engine(settings=settings, base_dir=base_dir)
    assert isinstance(engine, EventRiskEngine)
    assert engine.calendar is not None
    assert engine.window_builder is not None
    assert engine.policy_manager is not None
