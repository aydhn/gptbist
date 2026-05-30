import pytest
from pathlib import Path
from bist_signal_bot.docs_hub.indexer import DocsIndexer

def test_indexer_extract_title():
    indexer = DocsIndexer()
    text = "# My Title\nSome content."
    assert indexer.extract_title(text) == "My Title"

def test_indexer_extract_headings():
    indexer = DocsIndexer()
    text = "# My Title\n## Subheading\n### Subsubheading"
    headings = indexer.extract_headings(text)
    assert "Subheading" in headings
    assert "Subsubheading" in headings

def test_indexer_infer_doc_kind():
    indexer = DocsIndexer()
    path = Path("docs/00_QUICKSTART.md")
    assert indexer.infer_doc_kind(path, "").name == "QUICKSTART"

def test_indexer_infer_audience():
    indexer = DocsIndexer()
    path = Path("docs/30_DEVELOPER_GUIDE.md")
    assert indexer.infer_audience(path, "").name == "DEVELOPER"
