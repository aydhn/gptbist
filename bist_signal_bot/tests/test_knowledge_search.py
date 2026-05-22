import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.knowledge.storage import KnowledgeStore
from bist_signal_bot.knowledge.normalizer import KnowledgeTextNormalizer
from bist_signal_bot.knowledge.embeddings import LocalEmbeddingProvider
from bist_signal_bot.knowledge.search import KnowledgeSearchEngine
from bist_signal_bot.knowledge.models import KnowledgeSearchQuery, KnowledgeIndexStatus

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
