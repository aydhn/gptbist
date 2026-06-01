import pytest
from bist_signal_bot.final_audit.risk_register import FinalRiskRegisterBuilder

def test_risk_register_builder_default_risks():
    builder = FinalRiskRegisterBuilder()
    items = builder.build_risk_register(None)
    assert len(items) > 0
    assert any("No broker" in i.title for i in items)

def test_risk_register_validation():
    builder = FinalRiskRegisterBuilder()
    items = builder.build_risk_register(None)
    items[0].title = ""
    errors = builder.validate_risk_register(items)
    assert len(errors) == 1
