import pytest
from pathlib import Path
from bist_signal_bot.docs.validator import DocsValidator

def test_docs_validator_cache(tmp_path):
    validator = DocsValidator()
    test_file = tmp_path / "test.md"
    test_file.write_text("Hello World", encoding="utf-8")

    # First validation, it should read from disk
    findings = validator.validate_markdown_file(test_file)
    assert test_file in validator._file_cache
    assert validator._file_cache[test_file] == "Hello World"

    # Modify file on disk, shouldn't affect cache
    test_file.write_text("Modified", encoding="utf-8")
    findings = validator.validate_markdown_file(test_file)
    assert validator._file_cache[test_file] == "Hello World"
