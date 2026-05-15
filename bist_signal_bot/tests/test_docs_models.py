import pytest
from pathlib import Path
from bist_signal_bot.docs.models import DocsPage, DocsPageType, CLICommandDoc, CommandRiskLevel
from bist_signal_bot.docs.generator import DocsGenerator
from bist_signal_bot.docs.validator import DocsValidator
from bist_signal_bot.docs.catalog import CommandCatalogBuilder
from bist_signal_bot.docs.storage import DocsStore
from bist_signal_bot.docs.runbooks import RunbookBuilder
from bist_signal_bot.docs.examples import DocsExampleRunner

def test_docs_page_validation():
    page = DocsPage(path="test.md", title="Test", page_type=DocsPageType.OVERVIEW, description="Test page")
    assert page.path == "test.md"

def test_cli_command_doc_no_real_order():
    with pytest.raises(ValueError):
        CLICommandDoc(
            command="test",
            description="test",
            risk_level=CommandRiskLevel.SAFE,
            requires_network=False,
            sends_telegram=False,
            writes_files=False,
            requires_confirm=False,
            no_real_order_sent=False,
            module="test"
        )

def test_command_catalog_builder():
    builder = CommandCatalogBuilder()
    cmds = builder.build_command_catalog()
    assert len(cmds) > 0
    md = builder.command_to_markdown(cmds)
    assert "| Command |" in md

def test_docs_generator(tmp_path):
    gen = DocsGenerator()
    res = gen.generate_all_docs(output_dir=tmp_path)
    assert res.pages_created > 0
    assert (tmp_path / "01_QUICKSTART.md").exists()

def test_docs_validator(tmp_path):
    val = DocsValidator()
    # Missing pages
    missing = val.validate_required_pages(tmp_path)
    assert "00_DISCLAIMER.md" in missing

    # Safe text
    text = "Hello world\nThis is safe"
    findings = val.validate_no_unsafe_claims(text, "test.md")
    assert len(findings) == 0

    # Unsafe text
    unsafe = "Bu araç kesin al sinyali üretir."
    findings = val.validate_no_unsafe_claims(unsafe, "test.md")
    assert len(findings) > 0

def test_runbook_builder():
    builder = RunbookBuilder()
    rb = builder.build_runtime_stuck_lock_runbook()
    assert rb.runbook_id == "RB-001"
    md = builder.render_runbook_markdown(rb)
    assert "Symptom" in md

def test_docs_example_runner(tmp_path):
    runner = DocsExampleRunner()
    md = tmp_path / "test.md"
    md.write_text("Test `python -m bist_signal_bot healthcheck`\n")
    cmds = runner.extract_commands_from_markdown(md)
    assert "python -m bist_signal_bot healthcheck" in cmds

def test_docs_store(tmp_path):
    store = DocsStore(base_dir=tmp_path)
    assert store.get_docs_reports_dir().exists()
