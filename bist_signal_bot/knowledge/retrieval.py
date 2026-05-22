from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.knowledge.models import (
    KnowledgeSearchMode,
    KnowledgeSearchQuery,
    KnowledgeSearchResultItem,
    KnowledgeSourceType
)
from bist_signal_bot.knowledge.search import KnowledgeSearchEngine


class EvidenceRetriever:
    def __init__(self, search_engine: KnowledgeSearchEngine, settings: Settings | None = None):
        self.search_engine = search_engine
        self.settings = settings

    def retrieve_for_review_item(self, item_id: str, limit: int = 10) -> list[KnowledgeSearchResultItem]:
        query = KnowledgeSearchQuery(
            query=f"review decision evidence {item_id}",
            mode=KnowledgeSearchMode.AUTO,
            source_types=[
                KnowledgeSourceType.REVIEW_INBOX,
                KnowledgeSourceType.DECISION_JOURNAL,
                KnowledgeSourceType.REVIEW_THESIS
            ],
            limit=limit
        )
        return self.search_engine.search(query).items

    def retrieve_for_symbol(self, symbol: str, limit: int = 20) -> list[KnowledgeSearchResultItem]:
        query = KnowledgeSearchQuery(
            query=f"symbol analysis {symbol}",
            mode=KnowledgeSearchMode.AUTO,
            symbols=[symbol],
            limit=limit
        )
        return self.search_engine.search(query).items

    def retrieve_for_strategy(self, strategy_name: str, limit: int = 20) -> list[KnowledgeSearchResultItem]:
        query = KnowledgeSearchQuery(
            query=f"strategy behavior {strategy_name}",
            mode=KnowledgeSearchMode.AUTO,
            strategies=[strategy_name],
            limit=limit
        )
        return self.search_engine.search(query).items

    def retrieve_for_report_context(self, symbols: list[str], strategies: list[str] | None = None, limit: int = 20) -> list[KnowledgeSearchResultItem]:
        query = KnowledgeSearchQuery(
            query=" ".join(symbols + (strategies or [])),
            mode=KnowledgeSearchMode.AUTO,
            symbols=symbols,
            strategies=strategies or [],
            limit=limit
        )
        return self.search_engine.search(query).items

    def retrieve_for_research_lab_job(self, job: Any, limit: int = 10) -> list[KnowledgeSearchResultItem]:
        query = KnowledgeSearchQuery(
            query="failed patterns optimization drift",
            mode=KnowledgeSearchMode.AUTO,
            source_types=[KnowledgeSourceType.RESEARCH_LAB, KnowledgeSourceType.RESEARCH_LEDGER],
            limit=limit
        )
        return self.search_engine.search(query).items

    def build_evidence_summary(self, items: list[KnowledgeSearchResultItem]) -> str:
        if not items:
            return "No historical evidence found."

        summary = "Historical Evidence Summary:\n"
        for i, item in enumerate(items, 1):
            summary += f"{i}. [{item.source_type.value}] {item.title}\n"
            summary += f"   Snippet: {item.snippet}\n"

        return summary
