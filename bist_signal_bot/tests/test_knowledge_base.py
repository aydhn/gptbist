
import pytest
from datetime import datetime
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import KnowledgeValidationError, KnowledgeBaseError
from bist_signal_bot.knowledge.models import (
    KnowledgeDocument,
    KnowledgeSourceType,
    KnowledgeSearchQuery,
    KnowledgeSearchMode,
    KnowledgeIndexBuildResult,
    KnowledgeIndexBuildRequest,
    KnowledgeIndexStatus
)
from bist_signal_bot.knowledge.normalizer import KnowledgeTextNormalizer
from bist_signal_bot.knowledge.chunker import KnowledgeChunker
from bist_signal_bot.knowledge.embeddings import LocalEmbeddingProvider
from bist_signal_bot.knowledge.sources import KnowledgeSourceCollector
from bist_signal_bot.knowledge.storage import KnowledgeStore
from bist_signal_bot.knowledge.indexer import KnowledgeIndexer
from bist_signal_bot.knowledge.search import KnowledgeSearchEngine
from bist_signal_bot.knowledge.similarity import KnowledgeSimilarityEngine
from bist_signal_bot.knowledge.retrieval import EvidenceRetriever
from bist_signal_bot.knowledge.case_library import ResearchCaseLibrary
from bist_signal_bot.knowledge.memory import AnalystMemoryBuilder


def test_knowledge_document_validation():
    # Valid
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

    # Invalid
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

def test_knowledge_normalizer():
    norm = KnowledgeTextNormalizer()
    text = "ASELS momentum çok güçlü!"
    sanitized = norm.sanitize_text(text)
    assert sanitized == text

    normalized = norm.normalize_text(text)
    assert normalized == "asels momentum cok guclu"

    terms = norm.extract_terms(text)
    assert "asels" in terms
    assert "momentum" in terms

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

def test_fallback_embedding():
    settings = Settings(KNOWLEDGE_USE_LOCAL_EMBEDDINGS=False)
    provider = LocalEmbeddingProvider(settings)
    assert not provider.is_available()

    emb = provider.embed_query("test query")
    assert len(emb) == 128
    assert sum(v*v for v in emb) == pytest.approx(1.0, 0.01)

def test_storage(tmp_path):
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

def test_search_engine(tmp_path):
    settings = Settings(ENABLE_KNOWLEDGE_BASE=True)
    store = KnowledgeStore(settings, base_dir=tmp_path)
    norm = KnowledgeTextNormalizer()
    emb = LocalEmbeddingProvider(settings)
    engine = KnowledgeSearchEngine(store, norm, emb, settings)

    # Search on empty
    q = KnowledgeSearchQuery(query="test")
    res = engine.search(q)
    assert res.status == KnowledgeIndexStatus.EMPTY

def test_index_build(tmp_path):
    settings = Settings(ENABLE_KNOWLEDGE_BASE=True)
    store = KnowledgeStore(settings, base_dir=tmp_path)
    collector = KnowledgeSourceCollector(settings)
    norm = KnowledgeTextNormalizer()
    chunker = KnowledgeChunker()
    emb = LocalEmbeddingProvider(settings)
    indexer = KnowledgeIndexer(collector, norm, chunker, emb, store, settings)

    req = KnowledgeIndexBuildRequest(rebuild=True, confirm_rebuild=True)
    res = indexer.build_index(req)
    assert res.status == KnowledgeIndexStatus.READY

def test_clear_index(tmp_path):
    settings = Settings(ENABLE_KNOWLEDGE_BASE=True)
    store = KnowledgeStore(settings, base_dir=tmp_path)

    with pytest.raises(KnowledgeBaseError):
        store.clear_index(confirm=False)
