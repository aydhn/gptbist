import json
import csv
from pathlib import Path
from typing import Optional, List, Dict, Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.runtime.models import RuntimePipelineResult
from bist_signal_bot.storage.paths import get_runtime_runs_dir

class RuntimeReportStore:
    def __init__(self, settings: Optional[Settings] = None, base_dir: Optional[Path] = None):
        self.settings = settings or Settings()
        self.base_dir = base_dir or get_runtime_runs_dir(self.settings)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_runtime_dir(self) -> Path:
        return self.base_dir.parent

    def get_runs_dir(self) -> Path:
        return self.base_dir

    def create_run_dir(self, result: RuntimePipelineResult) -> Path:
        date_str = result.started_at.strftime("%Y%m%d")
        run_dir = self.base_dir / date_str / result.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def save_json(self, result: RuntimePipelineResult, output_dir: Optional[Path] = None) -> Path:
        dir_path = output_dir or self.create_run_dir(result)
        file_path = dir_path / "runtime_result.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))
        return file_path

    def save_markdown(self, result: RuntimePipelineResult, output_dir: Optional[Path] = None) -> Path:
        dir_path = output_dir or self.create_run_dir(result)
        file_path = dir_path / "runtime_report.md"

        lines = [
            f"# BIST Signal Bot - Runtime Report",
            f"**Run ID:** {result.run_id}",
            f"**Status:** {result.status.value}",
            f"**Started:** {result.started_at.isoformat()}",
            f"**Elapsed:** {result.elapsed_seconds:.2f}s",
            "",
            f"> **Disclaimer:** {result.disclaimer}",
            ""
        ]

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return file_path

    def save_jobs_csv(self, result: RuntimePipelineResult, output_dir: Optional[Path] = None) -> Path:
        dir_path = output_dir or self.create_run_dir(result)
        file_path = dir_path / "jobs.csv"

        if not result.job_results:
            return file_path

        with open(file_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Job ID", "Type", "Status", "Elapsed (s)", "Issues"])
            for job in result.job_results:
                writer.writerow([
                    job.job_id,
                    job.job_type.value,
                    job.status.value,
                    f"{job.elapsed_seconds:.2f}",
                    len(job.issues)
                ])
        return file_path

    def save_summary(self, result: RuntimePipelineResult, output_dir: Optional[Path] = None) -> Path:
        dir_path = output_dir or self.create_run_dir(result)
        file_path = dir_path / "summary.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(result.summary(), f, indent=2)
        return file_path

    def save_result(self, result: RuntimePipelineResult, formats: Optional[List[str]] = None, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        dir_path = output_dir or self.create_run_dir(result)
        paths = {}

        if not formats:
            formats = ["json"]

        if "json" in formats or "all" in formats:
            paths["json"] = self.save_json(result, dir_path)
            paths["summary"] = self.save_summary(result, dir_path)
        if "markdown" in formats or "all" in formats:
            paths["markdown"] = self.save_markdown(result, dir_path)
        if "csv" in formats or "all" in formats:
            paths["csv"] = self.save_jobs_csv(result, dir_path)

        return paths

    def list_recent_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        runs = []
        for date_dir in sorted(self.base_dir.iterdir(), reverse=True):
            if not date_dir.is_dir(): continue
            for run_dir in sorted(date_dir.iterdir(), reverse=True):
                if not run_dir.is_dir(): continue

                summary_file = run_dir / "summary.json"
                if summary_file.exists():
                    try:
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            runs.append(data)
                            if len(runs) >= limit:
                                return runs
                    except Exception:
                        pass
        return runs
