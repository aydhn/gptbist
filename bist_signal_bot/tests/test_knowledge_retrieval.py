import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.knowledge.storage import KnowledgeStore
from bist_signal_bot.knowledge.normalizer import KnowledgeTextNormalizer
from bist_signal_bot.knowledge.embeddings import LocalEmbeddingProvider
from bist_signal_bot.knowledge.search import KnowledgeSearchEngine
from bist_signal_bot.knowledge.retrieval import EvidenceRetriever

def test_evidence_retriever(tmp_path):
    settings = Settings(ENABLE_KNOWLEDGE_BASE=True)
    store = KnowledgeStore(settings, base_dir=tmp_path)
    norm = KnowledgeTextNormalizer()
    emb = LocalEmbeddingProvider(settings)
    search_engine = KnowledgeSearchEngine(store, norm, emb, settings)
    retriever = EvidenceRetriever(search_engine, settings)

    items = retriever.retrieve_for_symbol("ASELS")
    assert len(items) == 0

    summary = retriever.build_evidence_summary(items)
    assert "No historical evidence" in summary
