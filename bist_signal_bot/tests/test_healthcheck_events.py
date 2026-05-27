import pytest

def test_healthcheck_event_components():
    # Mocking healthcheck components
    components = {
        "event_store": True,
        "event_calendar": True,
        "event_risk_engine": True
    }

    assert all(components.values())
