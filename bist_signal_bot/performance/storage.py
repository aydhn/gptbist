import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from bist_signal_bot.performance.models import (
    WorkloadProfileResult, CacheReport, PerformanceBenchmarkResult
)
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_performance_dir
from bist_signal_bot.performance.reporting import (
    workload_profile_to_dict, cache_report_to_dict, benchmark_result_to_dict,
    format_performance_markdown
)

class PerformanceReportStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        from bist_signal_bot.config.settings import get_settings
        self.settings = settings or get_settings()
        self.base_dir = base_dir or get_performance_dir(self.settings)
        self.logger = logging.getLogger("bist_signal_bot.performance.storage")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_performance_dir(self) -> Path:
        return self.base_dir

    def create_run_dir(self, run_id: str) -> Path:
        today = datetime.utcnow().strftime("%Y%m%d")
        run_dir = self.base_dir / today / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def save_profile_result(self, result: WorkloadProfileResult, output_dir: Path | None = None) -> dict[str, Path]:
        if not output_dir:
            run_id = f"profile_{result.request.workload_type.value}_{datetime.utcnow().strftime('%H%M%S')}"
            output_dir = self.create_run_dir(run_id)

        saved_files = {}
        formats = self.settings.PERFORMANCE_REPORT_FORMATS.split(",")

        if "json" in formats:
            json_path = output_dir / "performance_result.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(workload_profile_to_dict(result), f, indent=2, ensure_ascii=False)
            saved_files["json"] = json_path

        if "markdown" in formats:
            md_path = output_dir / "performance_report.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(format_performance_markdown(result))
            saved_files["markdown"] = md_path

        return saved_files

    def save_cache_report(self, report: CacheReport, output_dir: Path | None = None) -> dict[str, Path]:
        if not output_dir:
            run_id = f"cache_report_{datetime.utcnow().strftime('%H%M%S')}"
            output_dir = self.create_run_dir(run_id)

        json_path = output_dir / "cache_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(cache_report_to_dict(report), f, indent=2, ensure_ascii=False)

        return {"json": json_path}

    def save_benchmark_result(self, result: PerformanceBenchmarkResult, output_dir: Path | None = None) -> dict[str, Path]:
        if not output_dir:
            run_id = f"benchmark_{result.benchmark_id}_{datetime.utcnow().strftime('%H%M%S')}"
            output_dir = self.create_run_dir(run_id)

        json_path = output_dir / "benchmark_result.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(benchmark_result_to_dict(result), f, indent=2, ensure_ascii=False)

        return {"json": json_path}

    def list_recent_performance_reports(self, limit: int = 20) -> list[dict[str, Any]]:
        reports = []
        if not self.base_dir.exists():
            return reports

        for day_dir in sorted(self.base_dir.iterdir(), reverse=True):
            if not day_dir.is_dir():
                continue
            for run_dir in sorted(day_dir.iterdir(), reverse=True):
                if not run_dir.is_dir():
                    continue
                json_file = run_dir / "performance_result.json"
                if json_file.exists():
                    try:
                        with open(json_file, "r") as f:
                            data = json.load(f)
                            reports.append({
                                "run_id": run_dir.name,
                                "date": day_dir.name,
                                "workload_type": data.get("request", {}).get("workload_type"),
                                "elapsed_seconds": data.get("elapsed_seconds")
                            })
                            if len(reports) >= limit:
                                return reports
                    except Exception:
                        pass
        return reports
