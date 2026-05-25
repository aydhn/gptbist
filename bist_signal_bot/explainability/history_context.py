import uuid
from typing import Any
from bist_signal_bot.explainability.models import HistoryContextExplanation

class HistoryContextExplainer:
    def __init__(self, settings: Any = None, base_dir: Any = None):
        self.settings = settings
        self.base_dir = base_dir

    def explain_history(self, symbol: str, strategy_name: str | None = None, query_text: str | None = None, limit: int = 5) -> HistoryContextExplanation:
        warnings = []
        # Mock logic
        warnings.append("Knowledge Base not available, insufficient data for history context.")

        return HistoryContextExplanation(
            explanation_id=str(uuid.uuid4()),
            symbol=symbol,
            strategy_name=strategy_name,
            similar_cases_count=0,
            relevant_memory=[],
            repeated_patterns=[],
            warnings=warnings,
            disclaimer="Historical patterns do not guarantee future success. Research-only."
        )

    def extract_repeated_patterns(self, search_results: list[Any]) -> list[str]:
        return []

    def memory_points(self, search_results: list[Any]) -> list[str]:
        return []
