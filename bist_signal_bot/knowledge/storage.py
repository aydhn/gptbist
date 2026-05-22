import json
from datetime import datetime
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import KnowledgeStorageError, KnowledgeBaseError
from bist_signal_bot.knowledge.models import (
    AnalystMemoryCard,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeIndexBuildResult,
    KnowledgeIndexEntry,
    KnowledgeSearchResult,
    KnowledgeDocumentStatus
)
from bist_signal_bot.storage.paths import get_knowledge_dir


class KnowledgeStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings
        if base_dir:
            self.base_dir = base_dir
        else:
            self.base_dir = get_knowledge_dir(settings)

        self.documents_file = self.base_dir / "documents" / "documents.jsonl"
        self.chunks_file = self.base_dir / "chunks" / "chunks.jsonl"
        self.index_entries_file = self.base_dir / "index" / "index_entries.jsonl"
        self.term_stats_file = self.base_dir / "index" / "term_stats.json"
        self.embedding_matrix_file = self.base_dir / "index" / "embedding_matrix.npy"
        self.builds_dir = self.base_dir / "builds"
        self.search_logs_file = self.base_dir / "search_logs" / "search_logs.jsonl"
        self.memory_cards_file = self.base_dir / "memory" / "analyst_memory_cards.jsonl"
        self.reports_dir = self.base_dir / "reports"

        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        self.documents_file.parent.mkdir(parents=True, exist_ok=True)
        self.chunks_file.parent.mkdir(parents=True, exist_ok=True)
        self.index_entries_file.parent.mkdir(parents=True, exist_ok=True)
        self.builds_dir.mkdir(parents=True, exist_ok=True)
        self.search_logs_file.parent.mkdir(parents=True, exist_ok=True)
        self.memory_cards_file.parent.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def save_documents(self, documents: list[KnowledgeDocument]) -> Path:
        """Saves or updates documents via JSONL append."""
        try:
            with self.documents_file.open("a", encoding="utf-8") as f:
                for doc in documents:
                    f.write(doc.model_dump_json() + "\n")
            return self.documents_file
        except Exception as e:
            raise KnowledgeStorageError(f"Failed to save documents: {e}")

    def load_documents(self, limit: int = 10000, include_archived: bool = False) -> list[KnowledgeDocument]:
        if not self.documents_file.exists():
            return []

        docs: dict[str, KnowledgeDocument] = {}
        try:
            with self.documents_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        doc = KnowledgeDocument.model_validate_json(line)
                        if not include_archived and doc.status == KnowledgeDocumentStatus.ARCHIVED:
                            continue
                        # Keep the latest by overwriting based on document_id
                        docs[doc.document_id] = doc
                    except Exception:
                        pass # Warning should be logged, but skipping broken lines
            return list(docs.values())[-limit:]
        except Exception as e:
            raise KnowledgeStorageError(f"Failed to load documents: {e}")

    def save_chunks(self, chunks: list[KnowledgeChunk]) -> Path:
        try:
            with self.chunks_file.open("a", encoding="utf-8") as f:
                for chunk in chunks:
                    f.write(chunk.model_dump_json() + "\n")
            return self.chunks_file
        except Exception as e:
            raise KnowledgeStorageError(f"Failed to save chunks: {e}")

    def load_chunks(self, document_id: str | None = None, limit: int = 100000) -> list[KnowledgeChunk]:
        if not self.chunks_file.exists():
            return []

        chunks = []
        try:
            with self.chunks_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        chunk = KnowledgeChunk.model_validate_json(line)
                        if document_id and chunk.document_id != document_id:
                            continue
                        chunks.append(chunk)
                    except Exception:
                        pass
            return chunks[-limit:]
        except Exception as e:
            raise KnowledgeStorageError(f"Failed to load chunks: {e}")

    def save_index_entries(self, entries: list[KnowledgeIndexEntry]) -> Path:
        try:
            with self.index_entries_file.open("a", encoding="utf-8") as f:
                for entry in entries:
                    f.write(entry.model_dump_json() + "\n")
            return self.index_entries_file
        except Exception as e:
            raise KnowledgeStorageError(f"Failed to save index entries: {e}")

    def load_index_entries(self, limit: int = 100000) -> list[KnowledgeIndexEntry]:
        if not self.index_entries_file.exists():
            return []

        entries = []
        try:
            with self.index_entries_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        entry = KnowledgeIndexEntry.model_validate_json(line)
                        entries.append(entry)
                    except Exception:
                        pass
            return entries[-limit:]
        except Exception as e:
            raise KnowledgeStorageError(f"Failed to load index entries: {e}")

    def save_build_result(self, result: KnowledgeIndexBuildResult) -> dict[str, Path]:
        try:
            date_str = datetime.now().strftime("%Y%m%d")
            build_dir = self.builds_dir / date_str / result.build_id
            build_dir.mkdir(parents=True, exist_ok=True)

            result_file = build_dir / "index_build_result.json"
            result_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")

            # Maintain a symlink/latest file pointer
            latest_file = self.builds_dir / "latest_build_result.json"
            latest_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")

            return {"result_file": result_file, "latest_file": latest_file}
        except Exception as e:
            raise KnowledgeStorageError(f"Failed to save build result: {e}")

    def load_latest_build(self) -> KnowledgeIndexBuildResult | None:
        latest_file = self.builds_dir / "latest_build_result.json"
        if not latest_file.exists():
            return None

        try:
            return KnowledgeIndexBuildResult.model_validate_json(latest_file.read_text(encoding="utf-8"))
        except Exception as e:
            raise KnowledgeStorageError(f"Failed to load latest build: {e}")

    def append_search_log(self, result: KnowledgeSearchResult) -> Path:
        try:
            with self.search_logs_file.open("a", encoding="utf-8") as f:
                f.write(result.model_dump_json() + "\n")
            return self.search_logs_file
        except Exception as e:
            raise KnowledgeStorageError(f"Failed to save search log: {e}")

    def save_memory_card(self, card: AnalystMemoryCard) -> Path:
        try:
            with self.memory_cards_file.open("a", encoding="utf-8") as f:
                f.write(card.model_dump_json() + "\n")
            return self.memory_cards_file
        except Exception as e:
            raise KnowledgeStorageError(f"Failed to save memory card: {e}")

    def load_memory_cards(self, symbol: str | None = None, strategy_name: str | None = None) -> list[AnalystMemoryCard]:
        if not self.memory_cards_file.exists():
            return []

        cards: dict[str, AnalystMemoryCard] = {}
        try:
            with self.memory_cards_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        card = AnalystMemoryCard.model_validate_json(line)
                        if symbol and card.symbol != symbol:
                            continue
                        if strategy_name and card.strategy_name != strategy_name:
                            continue
                        cards[card.memory_id] = card
                    except Exception:
                        pass
            return list(cards.values())
        except Exception as e:
            raise KnowledgeStorageError(f"Failed to load memory cards: {e}")

    def index_stats(self) -> dict[str, Any]:
        stats = {
            "document_count": 0,
            "chunk_count": 0,
            "index_entry_count": 0,
            "memory_card_count": 0,
            "last_build_status": "UNKNOWN",
            "last_build_time": None
        }

        try:
            if self.documents_file.exists():
                with self.documents_file.open("r", encoding="utf-8") as f:
                    stats["document_count"] = sum(1 for line in f if line.strip())

            if self.chunks_file.exists():
                with self.chunks_file.open("r", encoding="utf-8") as f:
                    stats["chunk_count"] = sum(1 for line in f if line.strip())

            if self.index_entries_file.exists():
                with self.index_entries_file.open("r", encoding="utf-8") as f:
                    stats["index_entry_count"] = sum(1 for line in f if line.strip())

            if self.memory_cards_file.exists():
                with self.memory_cards_file.open("r", encoding="utf-8") as f:
                    stats["memory_card_count"] = sum(1 for line in f if line.strip())

            latest_build = self.load_latest_build()
            if latest_build:
                stats["last_build_status"] = latest_build.status.value
                stats["last_build_time"] = latest_build.metadata.get("completed_at")
        except Exception:
            pass

        return stats

    def clear_index(self, confirm: bool = False) -> dict[str, Any]:
        if not confirm:
            raise KnowledgeBaseError("Cannot clear index without confirmation")

        result = {"cleared_files": [], "errors": []}
        files_to_clear = [
            self.documents_file,
            self.chunks_file,
            self.index_entries_file,
            self.term_stats_file,
            self.embedding_matrix_file
        ]

        for file in files_to_clear:
            if file.exists():
                try:
                    file.unlink()
                    result["cleared_files"].append(str(file))
                except Exception as e:
                    result["errors"].append(f"Failed to delete {file}: {e}")

        return result
