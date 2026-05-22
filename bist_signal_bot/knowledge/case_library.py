from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.knowledge.models import SimilarCase, SimilarCaseRequest
from bist_signal_bot.knowledge.similarity import KnowledgeSimilarityEngine


class ResearchCaseLibrary:
    def __init__(self, similarity_engine: KnowledgeSimilarityEngine, settings: Settings | None = None):
        self.similarity_engine = similarity_engine
        self.settings = settings

    def build_case_library(self, symbol: str | None = None, strategy_name: str | None = None) -> list[SimilarCase]:
        request = SimilarCaseRequest(
            symbol=symbol,
            strategy_name=strategy_name,
            text_query="historical research case",
            limit=50
        )
        return self.similarity_engine.similar_cases(request).cases

    def case_history(self, symbol: str, strategy_name: str | None = None, limit: int = 20) -> list[SimilarCase]:
        request = SimilarCaseRequest(
            symbol=symbol,
            strategy_name=strategy_name,
            text_query=f"history {symbol}",
            limit=limit
        )
        return self.similarity_engine.similar_cases(request).cases

    def outcome_patterns(self, symbol: str | None = None, strategy_name: str | None = None) -> dict[str, Any]:
        cases = self.build_case_library(symbol, strategy_name)

        # In a real implementation this would analyze the 'outcome_summary' fields
        return {
            "total_cases": len(cases),
            "common_patterns": ["Pattern detection requires more data"] if not cases else ["Historical outcome found"],
            "warning": "Outcomes are historical research context only."
        }

    def frequent_failure_patterns(self, strategy_name: str | None = None) -> list[str]:
        # Fake extraction for now, would use NLP to extract 'failed', 'loss', 'false positive'
        return ["High market conflict", "Low volume breakout"]

    def frequent_success_patterns(self, strategy_name: str | None = None) -> list[str]:
         # Fake extraction
        return ["Trend alignment", "Strong breadth support"]
