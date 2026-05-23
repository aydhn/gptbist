import time
import uuid
from datetime import datetime

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.audit import AuditLogger
from bist_signal_bot.knowledge.chunker import KnowledgeChunker
from bist_signal_bot.knowledge.embeddings import LocalEmbeddingProvider
from bist_signal_bot.knowledge.models import (
    KnowledgeDocument,
    KnowledgeIndexBuildRequest,
    KnowledgeIndexBuildResult,
    KnowledgeIndexEntry,
    KnowledgeIndexStatus,
)
from bist_signal_bot.knowledge.normalizer import KnowledgeTextNormalizer
from bist_signal_bot.knowledge.sources import KnowledgeSourceCollector
from bist_signal_bot.knowledge.storage import KnowledgeStore


class KnowledgeIndexer:
    def __init__(
        self,
        source_collector: KnowledgeSourceCollector,
        normalizer: KnowledgeTextNormalizer,
        chunker: KnowledgeChunker,
        embedding_provider: LocalEmbeddingProvider,
        store: KnowledgeStore,
        settings: Settings | None = None,
        audit_logger: AuditLogger | None = None
    ):
        self.source_collector = source_collector
        self.normalizer = normalizer
        self.chunker = chunker
        self.embedding_provider = embedding_provider
        self.store = store
        self.settings = settings
        self.audit_logger = audit_logger

    def build_index(self, request: KnowledgeIndexBuildRequest) -> KnowledgeIndexBuildResult:
        start_time = time.time()

        # Inject Optional Profiler
        profiler = None
        timer_span = None
        if getattr(self.settings, 'ENABLE_PERFORMANCE_PROFILING', False):
            from bist_signal_bot.app.performance_app import create_local_profiler
            profiler = create_local_profiler(self.settings)
            timer_span = profiler.timer.start_span("knowledge_build_index")

        result = KnowledgeIndexBuildResult(
            build_id=str(uuid.uuid4()),
            request=request,
            status=KnowledgeIndexStatus.BUILDING
        )

        if request.rebuild and not request.confirm_rebuild:
            if self.settings and self.settings.KNOWLEDGE_REBUILD_REQUIRES_CONFIRM:
                result.status = KnowledgeIndexStatus.FAILED
                result.errors.append("Rebuild requires confirmation.")
                return result

        if request.rebuild:
            try:
                self.store.clear_index(confirm=True)
            except Exception as e:
                result.status = KnowledgeIndexStatus.FAILED
                result.errors.append(f"Failed to clear index: {e}")
                return result

        try:
            # 1. Collect
            docs = self.source_collector.collect_documents(
                source_types=request.source_types if request.source_types else None,
                include_archived=request.include_archived
            )
            result.documents_seen = len(docs)

            existing_docs = []
            if request.incremental and not request.rebuild:
                existing_docs = self.store.load_documents(limit=100000)

            existing_doc_map = {d.document_id: d for d in existing_docs}

            docs_to_index = []
            for doc in docs:
                if request.rebuild or not request.incremental:
                    docs_to_index.append(doc)
                else:
                    existing = existing_doc_map.get(doc.document_id)
                    if not existing or existing.updated_at < doc.updated_at:
                        docs_to_index.append(doc)
                    else:
                        result.skipped_documents += 1

            if not docs_to_index and request.incremental:
                result.status = KnowledgeIndexStatus.READY
                result.elapsed_seconds = time.time() - start_time
                return result

            # 2. Save docs
            if docs_to_index:
                self.store.save_documents(docs_to_index)
                result.documents_indexed = len(docs_to_index)

            # 3. Chunk
            all_chunks = []
            for doc in docs_to_index:
                try:
                    chunks = self.chunker.chunk_document(doc)
                    all_chunks.extend(chunks)
                except Exception as e:
                    result.warnings.append(f"Failed to chunk document {doc.document_id}: {e}")

            if all_chunks:
                self.store.save_chunks(all_chunks)
                result.chunks_created = len(all_chunks)

            # 4. Index entries
            entries = []
            now = datetime.now()
            for chunk in all_chunks:
                try:
                    terms = self.normalizer.extract_terms(chunk.text)
                    norm_text = self.normalizer.normalize_text(chunk.text)
                    emb = None
                    if request.use_embeddings:
                        emb = self.embedding_provider.embed_query(chunk.text)
                        if emb:
                            result.embeddings_created += 1

                    entries.append(
                        KnowledgeIndexEntry(
                            entry_id=str(uuid.uuid4()),
                            chunk_id=chunk.chunk_id,
                            document_id=chunk.document_id,
                            terms=terms,
                            normalized_text=norm_text,
                            embedding_vector=emb,
                            indexed_at=now,
                            metadata={"symbol": chunk.symbol, "strategy": chunk.strategy_name}
                        )
                    )
                except Exception as e:
                    result.warnings.append(f"Failed to index chunk {chunk.chunk_id}: {e}")

            if entries:
                self.store.save_index_entries(entries)
                result.entries_indexed = len(entries)

            # 5. Clean up stale if rebuild
            if request.rebuild:
                pass # Already cleared

            # Finish
            result.status = KnowledgeIndexStatus.READY

        except Exception as e:
            result.status = KnowledgeIndexStatus.FAILED
            result.errors.append(f"Indexing failed: {e}")

        result.elapsed_seconds = time.time() - start_time

        try:
            paths = self.store.save_build_result(result)
            result.output_files = {k: str(v) for k, v in paths.items()}
        except Exception as e:
            result.warnings.append(f"Failed to save build result: {e}")

        if self.audit_logger:
            status_event = "KNOWLEDGE_INDEX_COMPLETED" if result.status == KnowledgeIndexStatus.READY else "KNOWLEDGE_INDEX_FAILED"
            self.audit_logger.log_event(
                event_type=status_event,
                description=f"Knowledge index build finished with status {result.status.value}",
                actor="SYSTEM",
                metadata={
                    "build_id": result.build_id,
                    "documents_indexed": result.documents_indexed,
                    "chunks_created": result.chunks_created,
                    "elapsed_seconds": result.elapsed_seconds,
                    "no_real_order_sent": True
                }
            )

        return result
