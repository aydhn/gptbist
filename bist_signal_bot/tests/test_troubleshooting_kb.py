from bist_signal_bot.docs_hub.troubleshooting import TroubleshootingKBBuilder

def test_troubleshooting_builder():
    builder = TroubleshootingKBBuilder()
    kb = builder.build_kb()
    assert len(kb.entries) > 0
    assert builder.entry_for_error("QA Blocked") is not None
