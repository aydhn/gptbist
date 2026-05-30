import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Any

from bist_signal_bot.docs_hub.models import (
    DocsIndex, DocsSearchResult, ArchitectureMap, CommandCookbook,
    TroubleshootingKnowledgeBase, DocsCoverageResult, MVPHandoffManifest,
    DocsHubReport
)

class DocsHubStore:
    def __init__(self, settings=None, base_dir: Optional[Path] = None):
        self.settings = settings
        # Simplified for mock
        self.base_dir = base_dir or Path("data/docs_hub")
        self.index_file = self.base_dir / "index/docs_index.json"
        self.search_file = self.base_dir / "search/docs_search_results.jsonl"
        self.architecture_file = self.base_dir / "architecture/architecture_map.json"
        self.cookbook_file = self.base_dir / "cookbook/command_cookbook.json"
        self.troubleshooting_file = self.base_dir / "troubleshooting/troubleshooting_kb.json"
        self.coverage_file = self.base_dir / "coverage/docs_coverage_results.jsonl"
        self.handoff_file = self.base_dir / "handoff/mvp_handoff_manifests.jsonl"

    def _ensure_dir(self, filepath: Path):
        filepath.parent.mkdir(parents=True, exist_ok=True)

    def save_index(self, index: DocsIndex) -> Path:
        self._ensure_dir(self.index_file)
        self.index_file.write_text(index.model_dump_json(indent=2))
        return self.index_file

    def load_index(self) -> Optional[DocsIndex]:
        if not self.index_file.exists():
            return None
        return DocsIndex.model_validate_json(self.index_file.read_text())

    def append_search_result(self, result: DocsSearchResult) -> Path:
        self._ensure_dir(self.search_file)
        with self.search_file.open("a") as f:
            f.write(result.model_dump_json() + "\n")
        return self.search_file

    def save_architecture_map(self, amap: ArchitectureMap) -> Path:
        self._ensure_dir(self.architecture_file)
        self.architecture_file.write_text(amap.model_dump_json(indent=2))
        return self.architecture_file

    def load_architecture_map(self) -> Optional[ArchitectureMap]:
        if not self.architecture_file.exists():
            return None
        return ArchitectureMap.model_validate_json(self.architecture_file.read_text())

    def save_cookbook(self, cookbook: CommandCookbook) -> Path:
        self._ensure_dir(self.cookbook_file)
        self.cookbook_file.write_text(cookbook.model_dump_json(indent=2))
        return self.cookbook_file

    def load_cookbook(self) -> Optional[CommandCookbook]:
        if not self.cookbook_file.exists():
            return None
        return CommandCookbook.model_validate_json(self.cookbook_file.read_text())

    def save_troubleshooting_kb(self, kb: TroubleshootingKnowledgeBase) -> Path:
        self._ensure_dir(self.troubleshooting_file)
        self.troubleshooting_file.write_text(kb.model_dump_json(indent=2))
        return self.troubleshooting_file

    def load_troubleshooting_kb(self) -> Optional[TroubleshootingKnowledgeBase]:
        if not self.troubleshooting_file.exists():
            return None
        return TroubleshootingKnowledgeBase.model_validate_json(self.troubleshooting_file.read_text())

    def append_coverage_result(self, result: DocsCoverageResult) -> Path:
        self._ensure_dir(self.coverage_file)
        with self.coverage_file.open("a") as f:
            f.write(result.model_dump_json() + "\n")
        return self.coverage_file

    def load_latest_coverage(self) -> Optional[DocsCoverageResult]:
        if not self.coverage_file.exists():
            return None
        lines = self.coverage_file.read_text().splitlines()
        if not lines:
            return None
        return DocsCoverageResult.model_validate_json(lines[-1])

    def append_handoff(self, manifest: MVPHandoffManifest) -> Path:
        self._ensure_dir(self.handoff_file)
        with self.handoff_file.open("a") as f:
            f.write(manifest.model_dump_json() + "\n")
        return self.handoff_file

    def load_latest_handoff(self) -> Optional[MVPHandoffManifest]:
        if not self.handoff_file.exists():
            return None
        lines = self.handoff_file.read_text().splitlines()
        if not lines:
            return None
        return MVPHandoffManifest.model_validate_json(lines[-1])

    def save_report(self, report: DocsHubReport, markdown_text: str) -> dict[str, Path]:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        report_dir = self.base_dir / f"reports/{date_str}"
        report_dir.mkdir(parents=True, exist_ok=True)

        md_file = report_dir / "docs_hub_report.md"
        json_file = report_dir / "docs_hub_report.json"

        md_file.write_text(markdown_text)
        json_file.write_text(report.model_dump_json(indent=2))

        return {"markdown": md_file, "json": json_file}
