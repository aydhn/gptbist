import pytest
from bist_signal_bot.final_handoff.operator_playbook import OperatorPlaybookBuilder

def test_operator_playbook_builder_render():
    builder = OperatorPlaybookBuilder()
    pb = builder.build_playbook()
    md = builder.render_markdown(pb)
    assert "Daily Routine" in md
    assert "python -m bist_signal_bot ops status" in md
