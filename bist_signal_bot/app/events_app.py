from pathlib import Path
from bist_signal_bot.config.settings import Settings

from bist_signal_bot.events.storage import EventStore
from bist_signal_bot.events.calendar import EventCalendar
from bist_signal_bot.events.importer import EventImporter
from bist_signal_bot.events.windows import EventWindowBuilder
from bist_signal_bot.events.risk import EventRiskEngine
from bist_signal_bot.events.blackout import BlackoutPolicyManager
from bist_signal_bot.events.linking import EventLinker

def create_event_store(settings: Settings | None = None, base_dir: Path | None = None) -> EventStore:
    # Use provided base_dir or fallback to settings/default
    if not base_dir:
        from bist_signal_bot.storage.paths import get_events_dir
        base_dir = get_events_dir(settings)
    return EventStore(base_dir=base_dir)

def create_event_calendar(settings: Settings | None = None, base_dir: Path | None = None) -> EventCalendar:
    store = create_event_store(settings, base_dir)
    return EventCalendar(store=store)

def create_event_importer(settings: Settings | None = None, base_dir: Path | None = None) -> EventImporter:
    calendar = create_event_calendar(settings, base_dir)
    return EventImporter(calendar=calendar)

def create_event_window_builder(settings: Settings | None = None, base_dir: Path | None = None) -> EventWindowBuilder:
    return EventWindowBuilder()

def create_blackout_policy_manager(settings: Settings | None = None, base_dir: Path | None = None) -> BlackoutPolicyManager:
    return BlackoutPolicyManager()

def create_event_risk_engine(settings: Settings | None = None, base_dir: Path | None = None) -> EventRiskEngine:
    calendar = create_event_calendar(settings, base_dir)
    window_builder = create_event_window_builder(settings, base_dir)
    policy_manager = create_blackout_policy_manager(settings, base_dir)
    return EventRiskEngine(calendar=calendar, window_builder=window_builder, policy_manager=policy_manager)

def create_event_linker(settings: Settings | None = None, base_dir: Path | None = None) -> EventLinker:
    return EventLinker()
