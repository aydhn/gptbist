from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.audit import AuditLogger
from bist_signal_bot.knowledge.case_library import ResearchCaseLibrary
from bist_signal_bot.knowledge.chunker import KnowledgeChunker
from bist_signal_bot.knowledge.embeddings import LocalEmbeddingProvider
from bist_signal_bot.knowledge.indexer import KnowledgeIndexer
from bist_signal_bot.knowledge.memory import AnalystMemoryBuilder
from bist_signal_bot.knowledge.normalizer import KnowledgeTextNormalizer
from bist_signal_bot.knowledge.retrieval import EvidenceRetriever
from bist_signal_bot.knowledge.search import KnowledgeSearchEngine
from bist_signal_bot.knowledge.similarity import KnowledgeSimilarityEngine
from bist_signal_bot.knowledge.sources import KnowledgeSourceCollector
from bist_signal_bot.knowledge.storage import KnowledgeStore


def create_knowledge_store(settings: Settings | None = None, base_dir: Path | None = None) -> KnowledgeStore:
    return KnowledgeStore(settings=settings, base_dir=base_dir)

def create_knowledge_indexer(
    settings: Settings | None = None,
    base_dir: Path | None = None,
    audit_logger: AuditLogger | None = None
) -> KnowledgeIndexer:
    store = create_knowledge_store(settings, base_dir)
    collector = KnowledgeSourceCollector(settings)
    normalizer = KnowledgeTextNormalizer()
    chunker = KnowledgeChunker()
    embeddings = LocalEmbeddingProvider(settings)
    return KnowledgeIndexer(
        source_collector=collector,
        normalizer=normalizer,
        chunker=chunker,
        embedding_provider=embeddings,
        store=store,
        settings=settings,
        audit_logger=audit_logger
    )

def create_knowledge_search_engine(
    settings: Settings | None = None,
    base_dir: Path | None = None,
    audit_logger: AuditLogger | None = None
) -> KnowledgeSearchEngine:
    store = create_knowledge_store(settings, base_dir)
    normalizer = KnowledgeTextNormalizer()
    embeddings = LocalEmbeddingProvider(settings)
    return KnowledgeSearchEngine(
        store=store,
        normalizer=normalizer,
        embedding_provider=embeddings,
        settings=settings,
        audit_logger=audit_logger
    )

def create_similarity_engine(settings: Settings | None = None, base_dir: Path | None = None) -> KnowledgeSimilarityEngine:
    search_engine = create_knowledge_search_engine(settings, base_dir)
    return KnowledgeSimilarityEngine(search_engine, settings)

def create_evidence_retriever(settings: Settings | None = None, base_dir: Path | None = None) -> EvidenceRetriever:
    search_engine = create_knowledge_search_engine(settings, base_dir)
    return EvidenceRetriever(search_engine, settings)

def create_case_library(settings: Settings | None = None, base_dir: Path | None = None) -> ResearchCaseLibrary:
    similarity_engine = create_similarity_engine(settings, base_dir)
    return ResearchCaseLibrary(similarity_engine, settings)

def create_analyst_memory_builder(settings: Settings | None = None, base_dir: Path | None = None) -> AnalystMemoryBuilder:
    case_library = create_case_library(settings, base_dir)
    store = create_knowledge_store(settings, base_dir)
    return AnalystMemoryBuilder(case_library, store, settings)
