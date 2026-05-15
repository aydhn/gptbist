import json
from pathlib import Path
from datetime import datetime
from typing import Any
from bist_signal_bot.docs.models import DocsValidationReport, DocsGenerationResult, CLICommandDoc
from bist_signal_bot.docs.reporting import command_catalog_to_dataframe

class DocsStore:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path("data/docs")

    def get_docs_reports_dir(self) -> Path:
        dt_str = datetime.utcnow().strftime("%Y%m%d")
        p = self.base_dir / dt_str
        p.mkdir(parents=True, exist_ok=True)
        return p

    def save_validation_report(self, report: DocsValidationReport, output_dir: Path | None = None) -> dict[str, Path]:
        d = output_dir or self.get_docs_reports_dir()
        d.mkdir(parents=True, exist_ok=True)
        jp = d / "docs_validation.json"
        jp.write_text(json.dumps(report.model_dump(mode="json")), encoding="utf-8")
        return {"json": jp}

    def save_generation_result(self, result: DocsGenerationResult, output_dir: Path | None = None) -> dict[str, Path]:
        d = output_dir or self.get_docs_reports_dir()
        d.mkdir(parents=True, exist_ok=True)
        jp = d / "docs_generation.json"
        jp.write_text(json.dumps(result.model_dump(mode="json")), encoding="utf-8")
        return {"json": jp}

    def save_command_catalog(self, commands: list[CLICommandDoc], output_dir: Path | None = None) -> Path:
        d = output_dir or self.get_docs_reports_dir()
        d.mkdir(parents=True, exist_ok=True)
        csv_path = d / "command_catalog.csv"
        df = command_catalog_to_dataframe(commands)
        if not df.empty:
            df.to_csv(csv_path, index=False)
        else:
            csv_path.write_text("")
        return csv_path

    def list_recent_docs_reports(self, limit: int = 20) -> list[dict[str, Any]]:
        return []
