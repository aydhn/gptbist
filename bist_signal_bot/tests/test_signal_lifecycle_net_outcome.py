import pytest
from pydantic import BaseModel

class MockSignalOutcome(BaseModel):
    gross_outcome_return_pct: float | None = None
    net_outcome_return_pct: float | None = None
    estimated_cost_bps: float | None = None

def test_signal_lifecycle_net_outcome():
    out = MockSignalOutcome(
        gross_outcome_return_pct=5.0, net_outcome_return_pct=4.5,
        estimated_cost_bps=50.0
    )
    assert out.net_outcome_return_pct == 4.5
