import json
import logging
from pathlib import Path
from typing import Any, List, Dict, Optional


from bist_signal_bot.config.settings import Settings
from bist_signal_bot.scanner.models import ScanReport
from bist_signal_bot.scanner.reporting import (
    scan_report_to_dict,
    scan_results_to_dataframe,
    scan_rankings_to_dataframe,
    scan_issues_to_dataframe,
    format_scan_markdown,
)
from bist_signal_bot.storage.paths import get_scans_dir


class ScanReportStore:
    def __init__(self, settings: Settings, base_dir: Optional[Path] = None):
        self.settings = settings
        self.base_dir = base_dir or get_scans_dir(settings)
        self.logger = logging.getLogger(__name__)

    def get_scans_dir(self) -> Path:
        return self.base_dir

    def create_scan_output_dir(self, report: ScanReport) -> Path:
        dt_str = report.started_at.strftime("%Y%m%d")
        scan_id = report.started_at.strftime("%H%M%S_") + report.request.strategy_name[:10]
        out_dir = self.base_dir / dt_str / scan_id
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir

    def save_json(self, report: ScanReport, output_dir: Optional[Path] = None) -> Path:
        if not output_dir:
            output_dir = self.create_scan_output_dir(report)
        file_path = output_dir / "scan_report.json"

        data = scan_report_to_dict(report)
        # remove big objects if any?
        # Ensure it's json serializable
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        return file_path

    def save_csv(self, report: ScanReport, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        if not output_dir:
            output_dir = self.create_scan_output_dir(report)

        paths = {}

        # Rankings
        if report.rankings:
            df = scan_rankings_to_dataframe(report.rankings)
            p = output_dir / "rankings.csv"
            df.to_csv(p, index=False)
            paths["rankings"] = p

        # Results
        if report.results:
            df = scan_results_to_dataframe(report.results)
            p = output_dir / "results.csv"
            df.to_csv(p, index=False)
            paths["results"] = p

        # Issues
        if report.issues:
            df = scan_issues_to_dataframe(report.issues)
            p = output_dir / "issues.csv"
            df.to_csv(p, index=False)
            paths["issues"] = p

        return paths

    def save_markdown(self, report: ScanReport, output_dir: Optional[Path] = None) -> Path:
        if not output_dir:
            output_dir = self.create_scan_output_dir(report)
        file_path = output_dir / "scan_report.md"

        content = format_scan_markdown(report)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return file_path

    def save_report(
        self,
        report: ScanReport,
        formats: Optional[List[str]] = None,
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Path]:
        if not formats:
            formats = ["json", "csv", "markdown"]

        if "all" in formats:
            formats = ["json", "csv", "markdown"]

        if not output_dir:
            output_dir = self.create_scan_output_dir(report)

        saved_paths = {}
        if "json" in formats:
            try:
                saved_paths["json"] = self.save_json(report, output_dir)
            except Exception as e:
                self.logger.error(f"Error saving JSON: {e}")
        if "csv" in formats:
            try:
                saved_paths.update(self.save_csv(report, output_dir))
            except Exception as e:
                self.logger.error(f"Error saving CSV: {e}")
        if "markdown" in formats:
            try:
                saved_paths["markdown"] = self.save_markdown(report, output_dir)
            except Exception as e:
                self.logger.error(f"Error saving Markdown: {e}")

        return saved_paths

    def list_recent_scans(self, limit: int = 20) -> List[Dict[str, Any]]:
        # Find all scan_report.json files
        scans = []
        if not self.base_dir.exists():
            return scans

        for json_file in self.base_dir.rglob("scan_report.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Extract summary info
                req = data.get("request", {})
                scans.append(
                    {
                        "date": data.get("started_at"),
                        "strategy": req.get("strategy_name"),
                        "mode": req.get("universe_mode"),
                        "status": data.get("status"),
                        "total": data.get("total_symbols"),
                        "passed": data.get("passed_count"),
                        "path": str(json_file.parent),
                    }
                )
            except Exception:
                continue

        # Sort by date desc
        scans.sort(key=lambda x: x.get("date", ""), reverse=True)
        return scans[:limit]
