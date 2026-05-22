import json
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.knowledge.models import (
    CaseLibraryResult,
    KnowledgeSearchMode,
    KnowledgeSearchQuery,
    KnowledgeSearchResultItem,
    KnowledgeSourceType,
    SimilarCase,
    SimilarCaseRequest
)
from bist_signal_bot.knowledge.search import KnowledgeSearchEngine


class KnowledgeSimilarityEngine:
    def __init__(self, search_engine: KnowledgeSearchEngine, settings: Settings | None = None):
        self.search_engine = search_engine
        self.settings = settings

    def similar_cases(self, request: SimilarCaseRequest) -> CaseLibraryResult:
        result = CaseLibraryResult(request=request)

        try:
            query = self.build_similarity_query(request)
            search_result = self.search_engine.search(query)

            for item in search_result.items:
                result.cases.append(self.case_from_search_item(item))

        except Exception as e:
            result.warnings.append(f"Failed to find similar cases: {e}")

        return result

    def similar_to_signal(self, signal_payload: dict[str, Any], limit: int = 10) -> list[SimilarCase]:
        request = SimilarCaseRequest(
            symbol=signal_payload.get("symbol"),
            strategy_name=signal_payload.get("strategy_name"),
            signal_payload=signal_payload,
            limit=limit
        )
        return self.similar_cases(request).cases

    def similar_to_review_item(self, item_id: str, limit: int = 10) -> list[SimilarCase]:
        # For simplicity, just doing a text query with item_id for now
        # Real implementation would load the item and extract context
        request = SimilarCaseRequest(
            text_query=f"review item {item_id}",
            limit=limit
        )
        return self.similar_cases(request).cases

    def build_similarity_query(self, request: SimilarCaseRequest) -> KnowledgeSearchQuery:
        parts = []
        if request.text_query:
            parts.append(request.text_query)

        if request.signal_payload:
            # Extract key features to match against
            if "trend" in request.signal_payload:
                parts.append(str(request.signal_payload["trend"]))
            if "conflict_level" in request.signal_payload:
                parts.append(str(request.signal_payload["conflict_level"]))
            if "reasons" in request.signal_payload:
                parts.extend([str(r) for r in request.signal_payload["reasons"]])

        query_text = " ".join(parts)
        if not query_text:
            query_text = f"{request.symbol or ''} {request.strategy_name or ''}".strip()

        if not query_text:
            query_text = "similar research case" # Fallback to avoid empty query error

        return KnowledgeSearchQuery(
            query=query_text,
            mode=KnowledgeSearchMode.AUTO,
            symbols=[request.symbol] if request.symbol else [],
            strategies=[request.strategy_name] if request.strategy_name else [],
            limit=request.limit
        )

    def case_from_search_item(self, item: KnowledgeSearchResultItem) -> SimilarCase:
        return SimilarCase(
            case_id=f"case_{item.document_id}",
            document_id=item.document_id,
            source_type=item.source_type,
            symbol=item.symbol,
            strategy_name=item.strategy_name,
            similarity_score=item.score,
            title=item.title,
            summary=item.snippet,
            outcome_summary="Historical outcome extracted from context" if item.source_type == KnowledgeSourceType.RESEARCH_LEDGER else None,
            decision_summary="Decision extracted from context" if item.source_type == KnowledgeSourceType.DECISION_JOURNAL else None
        )
