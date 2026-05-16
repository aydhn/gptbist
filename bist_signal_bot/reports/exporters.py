import json
import csv
from pathlib import Path
from bist_signal_bot.reports.models import GeneratedReport, ReportOutputFormat
from bist_signal_bot.reports.templates import ReportTemplateRenderer
from bist_signal_bot.core.exceptions import ReportExportError

class ReportExporter:
    def __init__(self, renderer: ReportTemplateRenderer | None = None):
        self.renderer = renderer or ReportTemplateRenderer()

    def export(self, report: GeneratedReport, formats: list[ReportOutputFormat], output_dir: Path) -> dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        files = {}

        try:
            if ReportOutputFormat.MARKDOWN in formats:
                files["markdown"] = self.export_markdown(report, output_dir)
            if ReportOutputFormat.JSON in formats:
                files["json"] = self.export_json(report, output_dir)
            if ReportOutputFormat.CSV in formats:
                csv_files = self.export_csv(report, output_dir)
                for k, v in csv_files.items():
                    files[f"csv_{k}"] = v
            if ReportOutputFormat.HTML in formats:
                files["html"] = self.export_html(report, output_dir)
            if ReportOutputFormat.PDF in formats:
                pdf_path = self.export_pdf(report, output_dir)
                if pdf_path:
                    files["pdf"] = pdf_path
        except Exception as e:
            raise ReportExportError(f"Failed to export report: {e}")

        return files

    def export_markdown(self, report: GeneratedReport, output_dir: Path) -> Path:
        p = output_dir / "report.md"
        p.write_text(self.renderer.render_markdown(report), encoding="utf-8")
        return p

    def export_json(self, report: GeneratedReport, output_dir: Path) -> Path:
        p = output_dir / "report.json"
        p.write_text(json.dumps(self.renderer.render_json(report), indent=2), encoding="utf-8")
        return p

    def export_csv(self, report: GeneratedReport, output_dir: Path) -> dict[str, Path]:
        tables = self.renderer.render_csv_tables(report)
        paths = {}
        for name, data in tables.items():
            if not data:
                continue
            p = output_dir / f"{name}.csv"
            with open(p, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            paths[name] = p
        return paths

    def export_html(self, report: GeneratedReport, output_dir: Path) -> Path:
        p = output_dir / "report.html"
        p.write_text(self.renderer.render_html(report), encoding="utf-8")
        return p

    def export_pdf(self, report: GeneratedReport, output_dir: Path) -> Path | None:
        # PDF is an optional feature. Returning None means skipped.
        return None
