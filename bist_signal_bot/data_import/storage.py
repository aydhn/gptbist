import json
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from bist_signal_bot.data_import.models import (
    ImportSource,
    ImportPreview,
    SchemaMapping,
    ImportValidationResult,
    NormalizedImportResult,
    ImportJob,
    DataImportReport
)
from bist_signal_bot.storage.paths import get_data_import_dir

class DataImportStore:
    def __init__(self, settings: Any = None, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir
        self.data_dir = get_data_import_dir(settings)

    def _append_jsonl(self, subdir: str, filename: str, data: dict[str, Any]) -> Path:
        target_dir = self.data_dir / subdir
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / filename
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, default=str) + "\n")
        return file_path

    def append_source(self, source: ImportSource) -> Path:
        return self._append_jsonl("sources", "import_sources.jsonl", source.model_dump())

    def append_preview(self, preview: ImportPreview) -> Path:
        return self._append_jsonl("previews", "import_previews.jsonl", preview.model_dump())

    def append_mapping(self, mapping: SchemaMapping) -> Path:
        return self._append_jsonl("mappings", "schema_mappings.jsonl", mapping.model_dump())

    def append_validation(self, validation: ImportValidationResult) -> Path:
        return self._append_jsonl("validations", "import_validations.jsonl", validation.model_dump())

    def append_normalized_result(self, result: NormalizedImportResult) -> Path:
        return self._append_jsonl("normalized", "normalized_import_results.jsonl", result.model_dump())

    def append_job(self, job: ImportJob) -> Path:
        return self._append_jsonl("jobs", "import_jobs.jsonl", job.model_dump())

    def load_jobs(self, limit: int = 1000) -> list[ImportJob]:
        file_path = self.data_dir / "jobs" / "import_jobs.jsonl"
        if not file_path.exists():
            return []

        jobs = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        jobs.append(ImportJob(**data))
                        if len(jobs) >= limit:
                            break
                    except Exception:
                        pass
        except Exception:
             pass
        return jobs

    def load_latest_job(self) -> ImportJob | None:
        jobs = self.load_jobs(limit=1)
        return jobs[0] if jobs else None

    def save_report(self, report: DataImportReport, markdown_text: str) -> dict[str, Path]:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        report_dir = self.data_dir / "reports" / date_str
        report_dir.mkdir(parents=True, exist_ok=True)

        md_path = report_dir / "data_import_report.md"
        json_path = report_dir / "data_import_report.json"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, default=str, indent=2)

        return {"md": md_path, "json": json_path}
