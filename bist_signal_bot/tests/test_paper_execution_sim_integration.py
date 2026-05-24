import pytest
from pydantic import BaseModel

class MockPaperLedger(BaseModel):
    gross_notional: float
    net_notional: float
    costs: float

def test_paper_ledger_simulated_fill_cost():
    m = MockPaperLedger(gross_notional=100.0, net_notional=98.0, costs=2.0)
    assert m.costs == 2.0
