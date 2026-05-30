from bist_signal_bot.docs_hub.handoff import MVPHandoffBuilder

def test_handoff_builder():
    builder = MVPHandoffBuilder()
    manifest = builder.build_handoff()
    assert manifest.qa_status is not None
