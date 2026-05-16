from pathlib import Path
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.reports.generator import ResearchReportGenerator
from bist_signal_bot.reports.storage import ReportStore
from bist_signal_bot.reports.digest import ReportDigestBuilder
from bist_signal_bot.reports.collector import ReportDataCollector

def create_report_store(settings: Settings | None = None, base_dir: Path | None = None) -> ReportStore:
    settings = settings or get_settings()
    store = ReportStore(settings=settings)
    if base_dir:
        store.base_dir = base_dir
        store.base_dir.mkdir(parents=True, exist_ok=True)
    return store

def create_report_collector(settings: Settings | None = None) -> ReportDataCollector:
    settings = settings or get_settings()
    return ReportDataCollector(settings=settings)

def create_report_generator(settings: Settings | None = None, base_dir: Path | None = None) -> ResearchReportGenerator:
    settings = settings or get_settings()
    collector = create_report_collector(settings)
    store = create_report_store(settings, base_dir)
    return ResearchReportGenerator(collector=collector, storage=store, settings=settings)

def create_digest_builder(settings: Settings | None = None) -> ReportDigestBuilder:
    settings = settings or get_settings()
    return ReportDigestBuilder(settings=settings)
