from typing import Any
import logging
import uuid
from datetime import datetime
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.reports.models import ReportConfig, GeneratedReport, ReportType, ReportStatus, ReportAudience
from bist_signal_bot.reports.collector import ReportDataCollector
from bist_signal_bot.reports.sections import ReportSectionBuilder
from bist_signal_bot.reports.templates import ReportTemplateRenderer

class ResearchReportGenerator:
    def __init__(self, collector: ReportDataCollector | None = None, section_builder: ReportSectionBuilder | None = None, renderer: ReportTemplateRenderer | None = None, storage: Any = None, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.settings = settings or get_settings()
        self.logger = logger or logging.getLogger(__name__)
        self.collector = collector or ReportDataCollector(settings=self.settings, logger=self.logger)
        self.section_builder = section_builder or ReportSectionBuilder()
        self.renderer = renderer or ReportTemplateRenderer()
        self.storage = storage # Assuming injected

    def generate(self, config: ReportConfig | None = None) -> GeneratedReport:
        if not config:
            config = self.build_default_config()

        start_time = datetime.utcnow()
        report_id = f"REP-{uuid.uuid4().hex[:8].upper()}"

        try:
            bundle = self.collector.collect(config)
            sections = self.section_builder.build_sections(bundle, config)

            elapsed = (datetime.utcnow() - start_time).total_seconds()

            report = GeneratedReport(
                report_id=report_id,
                report_type=config.report_type,
                audience=config.audience,
                status=ReportStatus.SUCCESS,
                title=f"BIST Research Report - {config.report_type.value}",
                sections=sections,
                data_bundle_summary=bundle.source_summaries,
                elapsed_seconds=elapsed
            )

            if config.save_report and self.storage:
                self.storage.save_report(report, config.formats)

            return report
        except Exception as e:
            self.logger.exception(f"Report generation failed: {e}")
            return GeneratedReport(
                report_id=report_id,
                report_type=config.report_type,
                audience=config.audience,
                status=ReportStatus.FAILED,
                title=f"BIST Research Report - {config.report_type.value}",
                issues=[str(e)]
            )

    def generate_daily(self, symbols: list[str] | None = None, save_report: bool = True) -> GeneratedReport:
        config = self.build_default_config(ReportType.DAILY)
        if symbols:
            config.symbols = symbols
        config.save_report = save_report
        return self.generate(config)

    def generate_weekly(self, symbols: list[str] | None = None, save_report: bool = True) -> GeneratedReport:
        config = self.build_default_config(ReportType.WEEKLY)
        if symbols:
            config.symbols = symbols
        config.save_report = save_report
        return self.generate(config)

    def generate_runtime_summary(self, runtime_run_id: str | None = None) -> GeneratedReport:
        config = self.build_default_config(ReportType.RUNTIME_SUMMARY)
        if runtime_run_id:
            config.metadata["runtime_run_id"] = runtime_run_id
        return self.generate(config)

    def build_default_config(self, report_type: ReportType = ReportType.DAILY) -> ReportConfig:
        return ReportConfig(report_type=report_type)