import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.knowledge.storage import KnowledgeStore
from bist_signal_bot.knowledge.sources import KnowledgeSourceCollector
from bist_signal_bot.knowledge.normalizer import KnowledgeTextNormalizer
from bist_signal_bot.knowledge.chunker import KnowledgeChunker
from bist_signal_bot.knowledge.embeddings import LocalEmbeddingProvider
from bist_signal_bot.knowledge.indexer import KnowledgeIndexer
from bist_signal_bot.knowledge.models import KnowledgeIndexBuildRequest, KnowledgeIndexStatus

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
