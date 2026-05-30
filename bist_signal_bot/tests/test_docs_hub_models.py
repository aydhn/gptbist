import pytest
from bist_signal_bot.docs_hub.models import (
    DocPage, DocsIndex, DocsSearchResult, ArchitectureNode,
    ArchitectureEdge, ArchitectureMap, CommandCookbookEntry,
    CommandCookbook, TroubleshootingEntry, TroubleshootingKnowledgeBase,
    DocsCoverageResult, MVPHandoffManifest, DocsStatus, DocKind, DocAudience,
    ArchitectureNodeType, TroubleshootingSeverity
)
from datetime import datetime

def test_doc_page_validation():
    page = DocPage(
        page_id="123",
        path="docs/test.md",
        title="Test Doc",
        kind=DocKind.CUSTOM,
        audience=DocAudience.ALL,
        summary="A test doc",
        headings=["Introduction"],
        related_modules=[],
        related_commands=[],
        last_indexed_at=datetime.utcnow(),
        status=DocsStatus.PASS
    )
    assert page.title == "Test Doc"

def test_docs_index_disclaimer():
    index = DocsIndex(
        index_id="1",
        created_at=datetime.utcnow(),
        pages=[],
        total_pages=0
    )
    assert "local software documentation metadata only" in index.disclaimer
