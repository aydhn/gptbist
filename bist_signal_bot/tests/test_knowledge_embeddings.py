import pytest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.knowledge.embeddings import LocalEmbeddingProvider

def test_fallback_embedding():
    settings = Settings(KNOWLEDGE_USE_LOCAL_EMBEDDINGS=False)
    provider = LocalEmbeddingProvider(settings)
    assert not provider.is_available()

    emb = provider.embed_query("test query")
    assert len(emb) == 128
    assert sum(v*v for v in emb) == pytest.approx(1.0, 0.01)
