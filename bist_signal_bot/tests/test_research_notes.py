import pytest
from bist_signal_bot.research.notes import ResearchNoteManager
from bist_signal_bot.research.storage import ResearchStore
from bist_signal_bot.config.settings import Settings

@pytest.fixture
def mock_settings(tmp_path):
    s = Settings()
    s.DATA_DIR = str(tmp_path)
    return s

@pytest.fixture
def manager(mock_settings, tmp_path):
    store = ResearchStore(settings=mock_settings, base_dir=tmp_path / "test_research")
    return ResearchNoteManager(storage=store, settings=mock_settings)

def test_note_manager_add_list_delete(manager):
    note = manager.add_note(title="T1", body="B1", tags=["t1"])
    assert note.title == "T1"

    notes = manager.list_notes()
    assert len(notes) == 1

    # Must confirm
    with pytest.raises(Exception):
        manager.delete_note(note.note_id)

    res = manager.delete_note(note.note_id, confirm=True)
    assert res is True

    assert len(manager.list_notes()) == 0

def test_note_unsafe_claim():
    from bist_signal_bot.research.models import ResearchNote
    with pytest.raises(ValueError):
         ResearchNote(note_id="x", title="T", body="This is guaranteed profit")
