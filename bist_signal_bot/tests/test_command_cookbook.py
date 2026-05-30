from bist_signal_bot.docs_hub.cookbook import CommandCookbookBuilder

def test_cookbook_builder():
    builder = CommandCookbookBuilder()
    cookbook = builder.build_cookbook()
    assert len(cookbook.entries) > 0
