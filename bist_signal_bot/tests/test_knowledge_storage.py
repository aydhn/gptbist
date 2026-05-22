import pytest
from datetime import datetime
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import KnowledgeBaseError
from bist_signal_bot.knowledge.storage import KnowledgeStore
from bist_signal_bot.knowledge.models import KnowledgeDocument, KnowledgeSourceType

def test_storage_documents(tmp_path):
    settings = Settings(ENABLE_KNOWLEDGE_BASE=True)
    store = KnowledgeStore(settings, base_dir=tmp_path)

    doc = KnowledgeDocument(
        document_id="1",
        source_type=KnowledgeSourceType.MANUAL_NOTE,
        title="Test",
        text="Content",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    store.save_documents([doc])

    loaded = store.load_documents()
    assert len(loaded) == 1
    assert loaded[0].document_id == "1"

def test_clear_index(tmp_path):
    settings = Settings(ENABLE_KNOWLEDGE_BASE=True)
    store = KnowledgeStore(settings, base_dir=tmp_path)

    with pytest.raises(KnowledgeBaseError):
        store.clear_index(confirm=False)
