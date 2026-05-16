import json
from pathlib import Path
from typing import Any
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.storage.paths import get_reports_dir
from bist_signal_bot.reports.models import GeneratedReport, TelegramDigest, ReportOutputFormat, ReportType
from bist_signal_bot.reports.exporters import ReportExporter

class ReportStore:
    def __init__(self, settings: Settings | None = None, exporter: ReportExporter | None = None):
        self.settings = settings or get_settings()
        self.exporter = exporter or ReportExporter()
        self.base_dir = get_reports_dir(self.settings)

    def get_reports_dir(self) -> Path:
        return self.base_dir

    def create_report_dir(self, report: GeneratedReport) -> Path:
        date_str = report.generated_at.strftime("%Y%m%d")
        report_dir = self.base_dir / date_str / report.report_id
        report_dir.mkdir(parents=True, exist_ok=True)
        return report_dir

    def save_report(self, report: GeneratedReport, formats: list[ReportOutputFormat] | None = None, output_dir: Path | None = None) -> dict[str, Path]:
        formats = formats or [ReportOutputFormat.MARKDOWN, ReportOutputFormat.JSON, ReportOutputFormat.CSV]
        if output_dir:
            dir_to_use = output_dir
            dir_to_use.mkdir(parents=True, exist_ok=True)
        else:
            dir_to_use = self.create_report_dir(report)

        files = self.exporter.export(report, formats, dir_to_use)
        report.output_files = {k: str(v) for k, v in files.items()}

        # Save metadata
        meta_path = dir_to_use / "metadata.json"
        meta_path.write_text(json.dumps(report.summary(), indent=2), encoding="utf-8")

        return files

    def save_digest(self, digest: TelegramDigest, output_dir: Path | None = None) -> Path:
        if not output_dir:
            output_dir = self.base_dir / "digests"
            output_dir.mkdir(parents=True, exist_ok=True)
        p = output_dir / f"{digest.digest_id}.txt"
        p.write_text(digest.message, encoding="utf-8")
        return p

    def load_latest_report(self, report_type: ReportType | None = None) -> GeneratedReport | None:
        # Dummy implementation
        return None

    def list_recent_reports(self, limit: int = 20) -> list[dict[str, Any]]:
        return []
