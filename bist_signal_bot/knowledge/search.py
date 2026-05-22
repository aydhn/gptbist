import math
import time
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.audit import AuditLogger
from bist_signal_bot.knowledge.embeddings import LocalEmbeddingProvider
from bist_signal_bot.knowledge.models import (
    KnowledgeIndexStatus,
    KnowledgeSearchMode,
    KnowledgeSearchQuery,
    KnowledgeSearchResult,
    KnowledgeSearchResultItem,
    KnowledgeDocument,
    KnowledgeChunk
)
from bist_signal_bot.knowledge.normalizer import KnowledgeTextNormalizer
from bist_signal_bot.knowledge.storage import KnowledgeStore


class KnowledgeSearchEngine:
    def __init__(
        self,
        store: KnowledgeStore,
        normalizer: KnowledgeTextNormalizer,
        embedding_provider: LocalEmbeddingProvider,
        settings: Settings | None = None,
        audit_logger: AuditLogger | None = None
    ):
        self.store = store
        self.normalizer = normalizer
        self.embedding_provider = embedding_provider
        self.settings = settings
        self.audit_logger = audit_logger

        self._doc_cache: dict[str, KnowledgeDocument] = {}
        self._chunk_cache: dict[str, KnowledgeChunk] = {}

    def _load_caches(self):
        docs = self.store.load_documents()
        self._doc_cache = {d.document_id: d for d in docs}

        chunks = self.store.load_chunks()
        self._chunk_cache = {c.chunk_id: c for c in chunks}

    def search(self, query: KnowledgeSearchQuery) -> KnowledgeSearchResult:
        start_time = time.time()
        result = KnowledgeSearchResult(
            query=query,
            mode_used=query.mode,
            status=KnowledgeIndexStatus.READY
        )

        try:
            self._load_caches()
            entries = self.store.load_index_entries()

            if not entries:
                result.status = KnowledgeIndexStatus.EMPTY
                return result

            # Mode selection
            mode = query.mode
            if mode == KnowledgeSearchMode.AUTO:
                if self.embedding_provider.is_available() and self.settings and self.settings.KNOWLEDGE_USE_LOCAL_EMBEDDINGS:
                    mode = KnowledgeSearchMode.HYBRID
                else:
                    mode = KnowledgeSearchMode.BM25_LITE

            result.mode_used = mode

            items = []
            if mode == KnowledgeSearchMode.KEYWORD:
                items = self.keyword_search(query, entries)
            elif mode == KnowledgeSearchMode.BM25_LITE:
                items = self.bm25_lite_search(query, entries)
            elif mode == KnowledgeSearchMode.EMBEDDING:
                items = self.embedding_search(query, entries)
            elif mode == KnowledgeSearchMode.HYBRID:
                items = self.hybrid_search(query, entries)

            filtered = self.apply_filters(items, query)
            ranked = self.rank_and_deduplicate(filtered, query.limit)

            result.items = ranked
            result.total_matches = len(ranked)

        except Exception as e:
            result.status = KnowledgeIndexStatus.FAILED
            result.warnings.append(f"Search failed: {e}")

        result.elapsed_seconds = time.time() - start_time

        if self.settings and self.settings.KNOWLEDGE_SAVE_SEARCH_LOGS:
            try:
                self.store.append_search_log(result)
            except Exception:
                pass

        if self.audit_logger:
            self.audit_logger.log_event(
                event_type="KNOWLEDGE_SEARCH_EXECUTED",
                description=f"Knowledge search executed with {result.total_matches} results",
                actor="SYSTEM",
                metadata={
                    "query": query.query,
                    "mode": result.mode_used.value,
                    "result_count": result.total_matches,
                    "no_real_order_sent": True
                }
            )

        return result

    def keyword_search(self, query: KnowledgeSearchQuery, entries: list) -> list:
        query_terms = self.normalizer.extract_terms(query.query)
        if not query_terms:
            return []

        items = []
        for entry in entries:
            score = 0.0
            for term in query_terms:
                if term in entry.terms:
                    score += entry.terms[term]

            if score > 0:
                items.append(self._build_item(entry, score))

        return sorted(items, key=lambda x: x.score, reverse=True)

    def bm25_lite_search(self, query: KnowledgeSearchQuery, entries: list) -> list:
        query_terms = self.normalizer.extract_terms(query.query)
        if not query_terms:
            return []

        # Compute doc frequencies
        df = {}
        for entry in entries:
            for term in entry.terms:
                df[term] = df.get(term, 0) + 1

        N = len(entries)
        avgdl = sum(sum(e.terms.values()) for e in entries) / max(1, N)
        k1 = 1.2
        b = 0.75

        items = []
        for entry in entries:
            dl = sum(entry.terms.values())
            score = 0.0
            for term in query_terms:
                if term in entry.terms:
                    # IDF
                    idf = math.log((N - df.get(term, 0) + 0.5) / (df.get(term, 0) + 0.5) + 1.0)
                    # TF
                    tf = entry.terms[term]
                    score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avgdl))

            if score > 0:
                items.append(self._build_item(entry, score))

        return sorted(items, key=lambda x: x.score, reverse=True)

    def embedding_search(self, query: KnowledgeSearchQuery, entries: list) -> list:
        q_emb = self.embedding_provider.embed_query(query.query)
        if not q_emb:
            return []

        items = []
        for entry in entries:
            if not entry.embedding_vector:
                # Use fallback if original entry didn't have one
                entry.embedding_vector = self.embedding_provider.fallback_embedding(entry.normalized_text)

            v_emb = entry.embedding_vector
            # Cosine similarity
            dot = sum(q * v for q, v in zip(q_emb, v_emb))
            norm_q = sum(q * q for q in q_emb) ** 0.5
            norm_v = sum(v * v for v in v_emb) ** 0.5

            if norm_q > 0 and norm_v > 0:
                score = dot / (norm_q * norm_v)
                # Keep positive similarities
                if score > 0.1:
                    items.append(self._build_item(entry, score))

        return sorted(items, key=lambda x: x.score, reverse=True)

    def hybrid_search(self, query: KnowledgeSearchQuery, entries: list) -> list:
        k_weight = self.settings.KNOWLEDGE_HYBRID_KEYWORD_WEIGHT if self.settings else 0.6
        e_weight = self.settings.KNOWLEDGE_HYBRID_EMBEDDING_WEIGHT if self.settings else 0.4

        bm25_items = {i.chunk_id: i.score for i in self.bm25_lite_search(query, entries)}
        emb_items = {i.chunk_id: i.score for i in self.embedding_search(query, entries)}

        # Normalize scores (Min-Max)
        max_bm25 = max(bm25_items.values()) if bm25_items else 1.0
        max_emb = max(emb_items.values()) if emb_items else 1.0

        all_chunk_ids = set(bm25_items.keys()) | set(emb_items.keys())

        items = []
        for entry in entries:
            if entry.chunk_id in all_chunk_ids:
                s_b = (bm25_items.get(entry.chunk_id, 0.0) / max_bm25) * k_weight
                s_e = (emb_items.get(entry.chunk_id, 0.0) / max_emb) * e_weight
                score = s_b + s_e
                items.append(self._build_item(entry, score))

        return sorted(items, key=lambda x: x.score, reverse=True)

    def _build_item(self, entry: Any, score: float) -> KnowledgeSearchResultItem:
        doc = self._doc_cache.get(entry.document_id)
        chunk = self._chunk_cache.get(entry.chunk_id)

        title = doc.title if doc else "Unknown"
        source_type = doc.source_type if doc else None

        snippet = ""
        if chunk:
            snippet = self.normalizer.safe_snippet(chunk.text)
        elif doc:
            snippet = self.normalizer.safe_snippet(doc.text)

        return KnowledgeSearchResultItem(
            rank=0, # Assigned later
            document_id=entry.document_id,
            chunk_id=entry.chunk_id,
            source_type=source_type,
            source_ref=doc.source_ref if doc else None,
            title=title,
            snippet=snippet,
            score=score,
            symbol=doc.symbol if doc else None,
            strategy_name=doc.strategy_name if doc else None,
            tags=doc.tags if doc else [],
            created_at=doc.created_at if doc else None
        )

    def apply_filters(self, items: list[KnowledgeSearchResultItem], query: KnowledgeSearchQuery) -> list[KnowledgeSearchResultItem]:
        filtered = []
        for item in items:
            if query.symbols and item.symbol not in query.symbols:
                continue
            if query.strategies and item.strategy_name not in query.strategies:
                continue
            if query.source_types and item.source_type not in query.source_types:
                continue
            if query.tags and not any(tag in item.tags for tag in query.tags):
                continue
            filtered.append(item)
        return filtered

    def rank_and_deduplicate(self, items: list[KnowledgeSearchResultItem], limit: int) -> list[KnowledgeSearchResultItem]:
        dedupe = self.settings.KNOWLEDGE_DEDUPE_DOCUMENT_RESULTS if self.settings else True
        seen_docs = set()

        ranked = []
        for i, item in enumerate(items):
            if dedupe:
                if item.document_id in seen_docs:
                    continue
                seen_docs.add(item.document_id)

            item.rank = len(ranked) + 1
            ranked.append(item)

            if len(ranked) >= limit:
                break

        return ranked

    def get_telegram_summary(self) -> dict:
        return {"documents_indexed": 0, "last_search": None}
