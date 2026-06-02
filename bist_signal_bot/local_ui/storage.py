import json
from pathlib import Path
from datetime import datetime
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.storage.paths import get_local_ui_dir
from bist_signal_bot.local_ui.models import (
    LocalUICapability, LocalUILayout, LocalUIPage,
    LocalUIShortcut, LocalUIRunResult, LocalUIReport
)

class LocalUIStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or get_settings()
        self.base_dir = base_dir or get_local_ui_dir(self.settings)

    def _append_jsonl(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

    def append_capabilities(self, capabilities: list[LocalUICapability]) -> Path:
        path = self.base_dir / "capabilities" / "local_ui_capabilities.jsonl"
        for cap in capabilities:
            self._append_jsonl(path, cap.model_dump(mode='json'))
        return path

    def append_layout(self, layout: LocalUILayout) -> Path:
        path = self.base_dir / "layouts" / "local_ui_layouts.jsonl"
        self._append_jsonl(path, layout.model_dump(mode='json'))
        return path

    def append_pages(self, pages: list[LocalUIPage]) -> Path:
        path = self.base_dir / "pages" / "local_ui_pages.jsonl"
        for page in pages:
            self._append_jsonl(path, page.model_dump(mode='json'))
        return path

    def save_shortcuts(self, shortcuts: list[LocalUIShortcut]) -> Path:
        path = self.base_dir / "shortcuts" / "local_ui_shortcuts.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [s.model_dump(mode='json') for s in shortcuts]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return path

    def load_shortcuts(self) -> list[LocalUIShortcut]:
        path = self.base_dir / "shortcuts" / "local_ui_shortcuts.json"
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return [LocalUIShortcut(**item) for item in data]
            except Exception:
                return []

    def append_run(self, result: LocalUIRunResult) -> Path:
        path = self.base_dir / "runs" / "local_ui_runs.jsonl"
        self._append_jsonl(path, result.model_dump(mode='json'))
        return path

    def load_latest_run(self) -> LocalUIRunResult | None:
        path = self.base_dir / "runs" / "local_ui_runs.jsonl"
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return None
            try:
                return LocalUIRunResult(**json.loads(lines[-1]))
            except Exception:
                return None

    def save_report(self, report: LocalUIReport, markdown_text: str) -> dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        report_dir = self.base_dir / "reports" / date_str
        report_dir.mkdir(parents=True, exist_ok=True)

        json_path = report_dir / "local_ui_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(mode='json'), f, indent=2)

        md_path = report_dir / "local_ui_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        return {"json": json_path, "markdown": md_path}
