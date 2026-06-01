import pytest
from bist_signal_bot.final_handoff.developer_playbook import DeveloperPlaybookBuilder

def test_developer_playbook_builder_render():
    builder = DeveloperPlaybookBuilder()
    pb = builder.build_playbook()
    md = builder.render_markdown(pb)
    assert "Coding Standards" in md
    assert "Use Type hints" in md
