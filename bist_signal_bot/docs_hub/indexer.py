import re
from pathlib import Path
from datetime import datetime
import uuid
from typing import Optional

from bist_signal_bot.docs_hub.models import (
    DocsIndex, DocPage, DocKind, DocAudience, DocsStatus
)
from bist_signal_bot.config.settings import Settings

class DocsIndexer:
    def __init__(self, settings: Optional[Settings] = None, base_dir: Optional[Path] = None):
        self.settings = settings or Settings()
        self.base_dir = base_dir or Path(getattr(self.settings, "DOCS_HUB_DOCS_ROOT", "bist_signal_bot/docs"))

    def index_docs(self, root: Optional[Path] = None) -> DocsIndex:
        root_dir = root or self.base_dir
        pages = []
        missing_expected_docs = self.expected_docs()
        warnings = []

        if root_dir.exists():
            for p in root_dir.glob("**/*.md"):
                if p.is_file():
                    page = self.parse_doc_page(p)
                    pages.append(page)
                    if p.name in missing_expected_docs:
                        missing_expected_docs.remove(p.name)

        return DocsIndex(
            index_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            pages=pages,
            total_pages=len(pages),
            missing_expected_docs=missing_expected_docs,
            stale_docs=[],
            warnings=warnings
        )

    def expected_docs(self) -> list[str]:
        return [
            "00_QUICKSTART.md",
            "30_DEVELOPER_GUIDE.md",
            "64_DOCUMENTATION_HUB.md",
            "65_ARCHITECTURE_MAP.md",
            "66_TROUBLESHOOTING.md",
            "67_COMMAND_COOKBOOK.md",
            "68_MVP_HANDOFF.md"
        ]

    def parse_doc_page(self, path: Path) -> DocPage:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            text = ""

        return DocPage(
            page_id=str(uuid.uuid4()),
            path=str(path),
            title=self.extract_title(text) or path.stem,
            kind=self.infer_doc_kind(path, text),
            audience=self.infer_audience(path, text),
            summary=text[:200] if text else "",
            headings=self.extract_headings(text),
            related_modules=self.related_modules(text),
            related_commands=self.related_commands(text),
            last_indexed_at=datetime.utcnow(),
            status=DocsStatus.PASS if text else DocsStatus.FAIL
        )

    def extract_title(self, text: str) -> str:
        for line in text.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return ""

    def extract_headings(self, text: str) -> list[str]:
        headings = []
        for line in text.splitlines():
            if line.startswith("## ") or line.startswith("### "):
                headings.append(line.lstrip("#").strip())
        return headings

    def infer_doc_kind(self, path: Path, text: str) -> DocKind:
        name = path.name.lower()
        if "quickstart" in name: return DocKind.QUICKSTART
        if "architecture" in name: return DocKind.ARCHITECTURE
        if "developer" in name: return DocKind.MODULE_GUIDE
        if "cookbook" in name: return DocKind.COMMAND_RECIPE
        if "troubleshoot" in name: return DocKind.TROUBLESHOOTING
        if "handoff" in name: return DocKind.HANDOFF
        return DocKind.CUSTOM

    def infer_audience(self, path: Path, text: str) -> DocAudience:
        name = path.name.lower()
        if "developer" in name: return DocAudience.DEVELOPER
        if "operator" in name or "troubleshoot" in name: return DocAudience.OPERATOR
        if "quickstart" in name: return DocAudience.USER
        return DocAudience.ALL

    def related_modules(self, text: str) -> list[str]:
        # Simple extraction logic for demo
        modules = []
        if "context_fusion" in text: modules.append("context_fusion")
        if "scanner" in text: modules.append("scanner")
        return modules

    def related_commands(self, text: str) -> list[str]:
        commands = []
        if "docs-hub" in text: commands.append("docs-hub")
        if "healthcheck" in text: commands.append("healthcheck")
        return commands
