import uuid
from datetime import datetime
from typing import Optional
from pathlib import Path

from bist_signal_bot.docs_hub.models import (
    DocsCoverageResult, DocsIndex, DocsStatus
)
from bist_signal_bot.docs_hub.indexer import DocsIndexer

class DocsCoverageAnalyzer:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.indexer = DocsIndexer(settings, base_dir)

    def analyze(self, index: Optional[DocsIndex] = None) -> DocsCoverageResult:
        if not index:
            index = self.indexer.index_docs()

        missing_docs = self.indexer.expected_docs()
        existing = []
        unsafe_findings = self.unsafe_language_findings(index)

        for p in index.pages:
            name = Path(p.path).name
            existing.append(name)
            if name in missing_docs:
                missing_docs.remove(name)

        modules_without_docs = self.modules_without_docs(index)
        commands_without_examples = self.commands_without_examples(index)
        docs_without_disclaimer = self.docs_without_disclaimer(index)

        expected_count = len(self.expected_docs())
        found_count = expected_count - len(missing_docs)

        score = (found_count / expected_count * 100.0) if expected_count > 0 else 100.0

        # Penalyze score
        score -= len(unsafe_findings) * 5
        score -= len(commands_without_examples) * 2
        score = max(0.0, score)

        status = self.classify_coverage(score, unsafe_findings)

        return DocsCoverageResult(
            coverage_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            expected_docs=self.expected_docs(),
            existing_docs=existing,
            missing_docs=missing_docs,
            modules_without_docs=modules_without_docs,
            commands_without_examples=commands_without_examples,
            docs_without_disclaimer=docs_without_disclaimer,
            unsafe_language_findings=unsafe_findings,
            coverage_score=score,
            status=status
        )

    def expected_docs(self) -> list[str]:
        return self.indexer.expected_docs()

    def expected_modules(self) -> list[str]:
        return ["scanner", "signals", "context_fusion", "ops", "qa", "docs_hub"]

    def expected_commands(self) -> list[str]:
        return ["docs-hub index", "docs-hub search"]

    def modules_without_docs(self, index: DocsIndex) -> list[str]:
        # Simplified for mock
        return []

    def commands_without_examples(self, index: DocsIndex) -> list[str]:
        # Simplified for mock
        return []

    def docs_without_disclaimer(self, index: DocsIndex) -> list[str]:
        return []

    def unsafe_language_findings(self, index: DocsIndex) -> list[str]:
        findings = []
        unsafe_terms = ["al/sat", "hedef fiyat", "kesin yükselir", "trade ready"]
        for page in index.pages:
            for term in unsafe_terms:
                if term in page.summary.lower():
                    findings.append(f"Unsafe term '{term}' in {page.title}")
        return findings

    def coverage_score(self, result: DocsCoverageResult) -> Optional[float]:
        return result.coverage_score

    def classify_coverage(self, score: Optional[float], findings: list[str]) -> DocsStatus:
        if findings: return DocsStatus.FAIL
        if score is None: return DocsStatus.UNKNOWN
        if score >= 80.0: return DocsStatus.PASS
        return DocsStatus.WATCH

def get_report_templates_coverage():
    return {"docs": ["83_ADVANCED_REPORT_TEMPLATES.md"], "examples": ["report_templates_workflow.md"]}
