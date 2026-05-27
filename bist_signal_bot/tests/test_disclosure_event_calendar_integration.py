from bist_signal_bot.events.risk import EventRiskEngine
def test_event_risk_disclosure_integration():
    engine = EventRiskEngine()
    class MockWindowBuilder:
        def build_windows(self, a, b): return []
        def active_windows(self, a, b, symbol=None): return []
    engine.window_builder = MockWindowBuilder()
    res = engine.assess_symbol("ASELS")
    assert res is not None
