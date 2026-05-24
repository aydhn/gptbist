import logging
from typing import Any
from datetime import datetime
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.reports.models import ReportConfig, ReportDataBundle, ReportType

class ReportDataCollector:
    def __init__(self, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.settings = settings or get_settings()
        self.logger = logger or logging.getLogger(__name__)

    def collect(self, config: ReportConfig) -> ReportDataBundle:
        self.logger.info(f"Collecting data for report {config.report_type.value}")
        bundle = ReportDataBundle(report_type=config.report_type)

        bundle.research_runs = self.collect_research_runs(config)
        bundle.journal_items = self.collect_signal_journal(config)
        bundle.scanner_items = self.collect_scanner_highlights(config)
        bundle.paper_items = self.collect_paper_summary(config)
        bundle.portfolio_research_summary = self.collect_portfolio_research_summary(config)
        bundle.source_summaries = self.build_source_summaries(bundle)

        # Merge operations summary into bundle dicts as appropriate, or keep separate logic.
        return bundle

    def collect_research_runs(self, config: ReportConfig) -> list[dict[str, Any]]:
        # In a real impl, read from ResearchLedger
        return []

    def collect_signal_journal(self, config: ReportConfig) -> list[dict[str, Any]]:
        # Read from SignalJournal
        return []

    def collect_scanner_highlights(self, config: ReportConfig) -> list[dict[str, Any]]:
        # Read from ScannerStorage
        return []


    def collect_portfolio_research_summary(self, config: ReportConfig) -> dict[str, Any]:
        if not getattr(self.settings, "REPORT_INCLUDE_PORTFOLIO_RESEARCH", False):
            return {}
        try:
            from bist_signal_bot.app.portfolio_research_app import create_portfolio_research_engine
            engine = create_portfolio_research_engine(self.settings)
            snapshot = engine.latest_snapshot()
            if snapshot:
                return snapshot.summary()
        except Exception as e:
            self.logger.warning(f"Failed to collect portfolio research summary: {e}")
        return {}

    def collect_paper_summary(self, config: ReportConfig) -> list[dict[str, Any]]:
        # Read from PaperLedger
        return []

    def collect_operations_summary(self, config: ReportConfig) -> dict[str, Any]:
        # Collect operations monitoring data
        return {}

    def build_source_summaries(self, bundle: ReportDataBundle) -> dict[str, Any]:
        summary = {}

        try:
            from bist_signal_bot.data.providers_v2.health import ProviderHealthTracker
            tracker = ProviderHealthTracker(self.settings)
            summary["provider_health"] = tracker.summarize_health()
        except:
            pass
        return {
            "research_runs": len(bundle.research_runs),
            "journal_items": len(bundle.journal_items),
            "scanner_items": len(bundle.scanner_items),
            "paper_items": len(bundle.paper_items)
        }

    def _collect_knowledge(self, settings: Any = None) -> dict:
        try:
            from bist_signal_bot.app.knowledge_app import create_knowledge_store
            store = create_knowledge_store(settings)
            return store.index_stats()
        except Exception:
            return {}

    def collect_validation_section(self) -> dict:
        return {"validation_included": True}
