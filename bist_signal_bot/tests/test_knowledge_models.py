import pytest
from datetime import datetime
from bist_signal_bot.core.exceptions import KnowledgeValidationError
from bist_signal_bot.knowledge.models import KnowledgeDocument, KnowledgeSourceType, KnowledgeSearchQuery

def test_knowledge_document_validation():
    doc = KnowledgeDocument(
        document_id="1",
        source_type=KnowledgeSourceType.MANUAL_NOTE,
        title="Test",
        text="Test content",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        symbol="asels"
    )
    assert doc.symbol == "ASELS"

    with pytest.raises(KnowledgeValidationError):
        KnowledgeDocument(
            document_id="2",
            source_type=KnowledgeSourceType.MANUAL_NOTE,
            title="",
            text="Test",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

def test_knowledge_search_query_validation():
    q = KnowledgeSearchQuery(query="test", limit=5, symbols=["thyao"])
    assert q.symbols == ["THYAO"]

    with pytest.raises(KnowledgeValidationError):
        KnowledgeSearchQuery(query="", limit=10)
