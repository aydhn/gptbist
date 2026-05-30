import pytest
from bist_signal_bot.docs_hub.coverage import DocsCoverageAnalyzer
from bist_signal_bot.docs_hub.models import DocsIndex, DocPage, DocKind, DocAudience, DocsStatus
from datetime import datetime

def test_coverage_score():
    analyzer = DocsCoverageAnalyzer()

    # Mock index with missing docs
    index = DocsIndex(
        index_id="1",
        created_at=datetime.utcnow(),
        pages=[
            DocPage(
                page_id="p1",
                path="docs/00_QUICKSTART.md",
                title="Quickstart",
                kind=DocKind.QUICKSTART,
                audience=DocAudience.USER,
                summary="Start here",
                headings=[],
                related_modules=[],
                related_commands=[],
                last_indexed_at=datetime.utcnow(),
                status=DocsStatus.PASS
            )
        ],
        total_pages=1
    )

    result = analyzer.analyze(index)
    assert result.coverage_score < 100.0
    assert "00_QUICKSTART.md" in result.existing_docs

def test_unsafe_language_findings():
    analyzer = DocsCoverageAnalyzer()

    index = DocsIndex(
        index_id="1",
        created_at=datetime.utcnow(),
        pages=[
            DocPage(
                page_id="p1",
                path="docs/test.md",
                title="Test",
                kind=DocKind.CUSTOM,
                audience=DocAudience.USER,
                summary="kesin yükselir trade ready",
                headings=[],
                related_modules=[],
                related_commands=[],
                last_indexed_at=datetime.utcnow(),
                status=DocsStatus.PASS
            )
        ],
        total_pages=1
    )

    findings = analyzer.unsafe_language_findings(index)
    assert len(findings) == 2
