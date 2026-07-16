from bist_signal_bot.docs_hub.troubleshooting import TroubleshootingKBBuilder
from bist_signal_bot.config.settings import Settings

def test_troubleshooting_builder():
    builder = TroubleshootingKBBuilder()
    kb = builder.build_kb()
    assert len(kb.entries) > 0
    assert builder.entry_for_error("QA Blocked") is not None

def test_troubleshooting_builder_settings():
    builder = TroubleshootingKBBuilder()
    assert isinstance(builder.settings, Settings)

    custom_settings = Settings(DRY_RUN=False)
    builder2 = TroubleshootingKBBuilder(settings=custom_settings)
    assert builder2.settings is custom_settings
    assert builder2.settings.DRY_RUN is False
