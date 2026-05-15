import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.quality.models import QualityRunResult
from bist_signal_bot.storage.paths import get_quality_dir

class QualityReportStore:
    def __init__(self, settings: Optional[Settings] = None, logger: Optional[logging.Logger] = None):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger(__name__)

    def get_quality_dir(self) -> Path:
        return get_quality_dir(self.settings)

    def create_run_dir(self, result: QualityRunResult) -> Path:
        date_str = result.started_at.strftime("%Y%m%d")
        run_dir = self.get_quality_dir() / date_str / result.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def save_json(self, result: QualityRunResult, output_dir: Optional[Path] = None) -> Path:
        out_dir = output_dir or self.create_run_dir(result)
        path = out_dir / "quality_result.json"

        with open(path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))
        return path

    def save_markdown(self, result: QualityRunResult, output_dir: Optional[Path] = None) -> Path:
        out_dir = output_dir or self.create_run_dir(result)
        path = out_dir / "quality_report.md"

        from bist_signal_bot.quality.reporting import format_quality_markdown
        content = format_quality_markdown(result)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def save_checks_csv(self, result: QualityRunResult, output_dir: Optional[Path] = None) -> Path:
        out_dir = output_dir or self.create_run_dir(result)
        path = out_dir / "checks.csv"

        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["check_name", "tool", "status", "elapsed_seconds", "exit_code", "message"])
            for check in result.checks:
                writer.writerow([
                    check.check_name,
                    check.tool.value,
                    check.status.value,
                    f"{check.elapsed_seconds:.2f}",
                    check.exit_code if check.exit_code is not None else "",
                    check.message
                ])
        return path

    def save_summary(self, result: QualityRunResult, output_dir: Optional[Path] = None) -> Path:
        out_dir = output_dir or self.create_run_dir(result)
        path = out_dir / "summary.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(result.summary(), f, indent=2)
        return path

    def save_result(self, result: QualityRunResult, formats: Optional[list[str]] = None, output_dir: Optional[Path] = None) -> dict[str, Path]:
        out_dir = output_dir or self.create_run_dir(result)
        fmt = formats or result.config.formats
        saved_files = {}

        if "json" in fmt or "all" in fmt:
            saved_files["json"] = self.save_json(result, out_dir)
            saved_files["summary"] = self.save_summary(result, out_dir)
        if "markdown" in fmt or "all" in fmt:
            saved_files["markdown"] = self.save_markdown(result, out_dir)
        if "csv" in fmt or "all" in fmt:
            saved_files["csv"] = self.save_checks_csv(result, out_dir)

        result.output_files = {k: str(v) for k, v in saved_files.items()}
        return saved_files

    def list_recent_quality_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        quality_dir = self.get_quality_dir()
        if not quality_dir.exists():
            return []

        runs = []
        # Find all summary.json files
        for summary_file in sorted(quality_dir.rglob("summary.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                with open(summary_file, "r") as f:
                    runs.append(json.load(f))
                if len(runs) >= limit:
                    break
            except Exception as e:
                self.logger.warning(f"Could not read summary file {summary_file}: {e}")

        return runs
