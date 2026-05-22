import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.knowledge.storage import KnowledgeStore
from bist_signal_bot.knowledge.normalizer import KnowledgeTextNormalizer
from bist_signal_bot.knowledge.embeddings import LocalEmbeddingProvider
from bist_signal_bot.knowledge.search import KnowledgeSearchEngine
from bist_signal_bot.knowledge.similarity import KnowledgeSimilarityEngine
from bist_signal_bot.knowledge.models import SimilarCaseRequest

def test_similarity_engine(tmp_path):
    settings = Settings(ENABLE_KNOWLEDGE_BASE=True)
    store = KnowledgeStore(settings, base_dir=tmp_path)
    norm = KnowledgeTextNormalizer()
    emb = LocalEmbeddingProvider(settings)
    search_engine = KnowledgeSearchEngine(store, norm, emb, settings)
    engine = KnowledgeSimilarityEngine(search_engine, settings)

    req = SimilarCaseRequest(symbol="ASELS", strategy_name="momentum")
    res = engine.similar_cases(req)
    assert len(res.cases) == 0
