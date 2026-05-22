import uuid
from datetime import datetime
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.knowledge.case_library import ResearchCaseLibrary
from bist_signal_bot.knowledge.models import AnalystMemoryCard, SimilarCase
from bist_signal_bot.knowledge.storage import KnowledgeStore


class AnalystMemoryBuilder:
    def __init__(self, case_library: ResearchCaseLibrary, store: KnowledgeStore, settings: Settings | None = None):
        self.case_library = case_library
        self.store = store
        self.settings = settings

    def build_memory_card(self, symbol: str | None = None, strategy_name: str | None = None) -> AnalystMemoryCard:
        cases = self.case_library.build_case_library(symbol, strategy_name)

        card = AnalystMemoryCard(
            memory_id=str(uuid.uuid4()),
            symbol=symbol,
            strategy_name=strategy_name,
            title=f"Analyst Memory: {symbol or 'General'} - {strategy_name or 'All'}",
            summary=f"Synthesized from {len(cases)} historical research cases.",
            key_lessons=self.extract_key_lessons(cases),
            repeated_patterns=self.extract_repeated_patterns(cases),
            risk_notes=self.extract_risk_notes(cases),
            last_seen_at=datetime.now(),
            evidence_refs=[c.document_id for c in cases[:5]]
        )

        if self.settings and self.settings.KNOWLEDGE_BUILD_MEMORY_CARDS:
            min_cases = self.settings.KNOWLEDGE_MEMORY_MIN_CASES if self.settings else 3
            if len(cases) >= min_cases:
                self.save_memory_card(card)

        return card

    def extract_key_lessons(self, cases: list[SimilarCase]) -> list[str]:
        if not cases:
            return ["No historical cases to extract lessons from."]
        return ["Historical context suggests reviewing breadth signals before confirmation."]

    def extract_repeated_patterns(self, cases: list[SimilarCase]) -> list[str]:
        if not cases:
            return []
        return ["Frequent occurrences of divergence."]

    def extract_risk_notes(self, cases: list[SimilarCase]) -> list[str]:
        if not cases:
            return []
        return ["Watch for sudden regime changes as seen in past cases."]

    def save_memory_card(self, card: AnalystMemoryCard) -> Path:
        return self.store.save_memory_card(card)

    def load_memory_card(self, symbol: str | None = None, strategy_name: str | None = None) -> AnalystMemoryCard | None:
        cards = self.store.load_memory_cards(symbol, strategy_name)
        if cards:
            return cards[-1] # Return latest
        return None
