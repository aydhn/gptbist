import pytest
from bist_signal_bot.release.notes import ReleaseNotesBuilder
from bist_signal_bot.release.models import ReleaseStage

def test_release_notes_markdown():
    builder = ReleaseNotesBuilder()
    notes = builder.build_notes("0.1.0", ReleaseStage.RELEASE_CANDIDATE)
    md = builder.render_markdown(notes)
    assert "# BIST Signal Bot 0.1.0 (RELEASE_CANDIDATE)" in md
    assert "**Disclaimer**: Release notes are operational documentation only" in md
