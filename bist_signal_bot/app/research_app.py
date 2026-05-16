from pathlib import Path

from ..config.settings import Settings, get_settings
from ..research.storage import ResearchStore
from ..research.ledger import ResearchLedger
from ..research.journal import SignalJournal
from ..research.comparison import ResearchComparator
from ..research.attribution import ResearchAttributionEngine
from ..research.events import ResearchEventBuilder
from ..research.lineage import ResearchLineageResolver
from ..research.notes import ResearchNoteManager
from ..research.query import ResearchQueryEngine

def create_research_store(settings: Settings | None = None, base_dir: Path | None = None) -> ResearchStore:
    return ResearchStore(settings=settings, base_dir=base_dir)

def create_research_ledger(settings: Settings | None = None, base_dir: Path | None = None) -> ResearchLedger:
    store = create_research_store(settings, base_dir)
    return ResearchLedger(storage=store, settings=settings)

def create_signal_journal(settings: Settings | None = None, base_dir: Path | None = None) -> SignalJournal:
    store = create_research_store(settings, base_dir)
    return SignalJournal(storage=store, settings=settings)

def create_research_comparator(settings: Settings | None = None, base_dir: Path | None = None) -> ResearchComparator:
    ledger = create_research_ledger(settings, base_dir)
    return ResearchComparator(ledger=ledger, settings=settings)

def create_attribution_engine(settings: Settings | None = None, base_dir: Path | None = None) -> ResearchAttributionEngine:
    journal = create_signal_journal(settings, base_dir)
    return ResearchAttributionEngine(journal=journal, settings=settings)

def create_research_event_builder(settings: Settings | None = None) -> ResearchEventBuilder:
    return ResearchEventBuilder(settings=settings)

def create_research_lineage_resolver(settings: Settings | None = None, base_dir: Path | None = None) -> ResearchLineageResolver:
    ledger = create_research_ledger(settings, base_dir)
    return ResearchLineageResolver(ledger=ledger)

def create_research_note_manager(settings: Settings | None = None, base_dir: Path | None = None) -> ResearchNoteManager:
    store = create_research_store(settings, base_dir)
    return ResearchNoteManager(storage=store, settings=settings)

def create_research_query_engine(settings: Settings | None = None, base_dir: Path | None = None) -> ResearchQueryEngine:
    ledger = create_research_ledger(settings, base_dir)
    journal = create_signal_journal(settings, base_dir)
    return ResearchQueryEngine(ledger=ledger, journal=journal)
