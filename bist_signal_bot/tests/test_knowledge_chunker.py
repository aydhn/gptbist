import pytest
from datetime import datetime
from bist_signal_bot.knowledge.chunker import KnowledgeChunker
from bist_signal_bot.knowledge.models import KnowledgeDocument, KnowledgeSourceType

def test_knowledge_chunker():
    chunker = KnowledgeChunker()
    doc = KnowledgeDocument(
        document_id="1",
        source_type=KnowledgeSourceType.MANUAL_NOTE,
        title="Test",
        text="Short text.",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    chunks = chunker.chunk_document(doc, chunk_size=100, overlap=10)
    assert len(chunks) == 1
    assert chunks[0].text == "Short text."
