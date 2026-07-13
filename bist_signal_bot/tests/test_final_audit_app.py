from bist_signal_bot.app.final_audit_app import create_final_risk_register_builder
from bist_signal_bot.final_audit.risk_register import FinalRiskRegisterBuilder
from bist_signal_bot.config.settings import Settings

class MockSettings(Settings):
    pass

def test_create_final_risk_register_builder():
    builder = create_final_risk_register_builder()
    assert isinstance(builder, FinalRiskRegisterBuilder)
    assert isinstance(builder.settings, Settings)

def test_create_final_risk_register_builder_with_settings():
    settings = MockSettings()
    builder = create_final_risk_register_builder(settings=settings)
    assert isinstance(builder, FinalRiskRegisterBuilder)
    assert builder.settings is settings
