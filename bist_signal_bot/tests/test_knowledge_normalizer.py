import pytest
from bist_signal_bot.knowledge.normalizer import KnowledgeTextNormalizer

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
