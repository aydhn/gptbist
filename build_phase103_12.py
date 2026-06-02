import os
from pathlib import Path

# test_report_exporter.py
Path("bist_signal_bot/tests/test_report_exporter.py").write_text('''
import pytest
from bist_signal_bot.report_templates.exporter import ReportExporter
from bist_signal_bot.report_templates.models import ComposedReport, ReportOutputFormat, ReportValidationStatus, ReportTemplateKind
from datetime import datetime

def test_exporter_dry_run():
    report = ComposedReport(
        report_id="r1", template_id="t1", template_name="test",
        kind=ReportTemplateKind.CUSTOM, generated_at=datetime.utcnow(),
        output_formats=[ReportOutputFormat.MARKDOWN]
    )
    exporter = ReportExporter()
    pack = exporter.export_report(report, confirm=False)
    assert pack.status == ReportValidationStatus.PASS
    assert "Dry-run mode active" in pack.warnings[0]
    assert pack.artifacts[0].status == ReportValidationStatus.WATCH

def test_exporter_confirm(tmp_path):
    report = ComposedReport(
        report_id="r2", template_id="t1", template_name="test",
        kind=ReportTemplateKind.CUSTOM, generated_at=datetime.utcnow(),
        output_formats=[ReportOutputFormat.MARKDOWN, ReportOutputFormat.JSON],
        markdown_text="# test", json_payload={"data": "test"}
    )
    exporter = ReportExporter(base_dir=tmp_path)
    pack = exporter.export_report(report, output_dir=tmp_path, confirm=True)
    assert pack.status == ReportValidationStatus.PASS
    assert len(pack.artifacts) == 2
    md_art = next(a for a in pack.artifacts if a.output_format == ReportOutputFormat.MARKDOWN)
    assert md_art.status == ReportValidationStatus.PASS
    assert Path(md_art.path).exists()
    assert md_art.checksum is not None
''')

# test_report_manifest.py
Path("bist_signal_bot/tests/test_report_manifest.py").write_text('''
from bist_signal_bot.report_templates.manifest import ReportManifestBuilder
from bist_signal_bot.report_templates.models import ComposedReport, ReportTemplateKind, RenderedReportSection, ReportValidationStatus
from datetime import datetime

def test_manifest_builder():
    report = ComposedReport(
        report_id="r1", template_id="t1", template_name="test",
        kind=ReportTemplateKind.CUSTOM, generated_at=datetime.utcnow(),
        sections=[RenderedReportSection(rendered_section_id="rs1", section_key="s1", title="S1", content_markdown="", status=ReportValidationStatus.PASS)]
    )
    builder = ReportManifestBuilder()
    manifest = builder.build_manifest(report)
    assert manifest.report_id == "r1"
    assert manifest.template_id == "t1"
    assert "s1" in manifest.section_statuses
    assert manifest.section_statuses["s1"] == "PASS"
''')

# test_report_template_validation.py
Path("bist_signal_bot/tests/test_report_template_validation.py").write_text('''
from bist_signal_bot.report_templates.validation import ReportTemplateValidator
from bist_signal_bot.report_templates.models import ReportTemplate, ReportTemplateKind, ReportSectionDefinition, ReportSectionKind, ReportValidationStatus

def test_validate_template_missing_disclaimer():
    val = ReportTemplateValidator()
    t = ReportTemplate(
        template_id="t1", name="n1", kind=ReportTemplateKind.CUSTOM, version="1", description="",
        sections=[ReportSectionDefinition(section_id="s1", section_key="summary", title="S", kind=ReportSectionKind.SUMMARY, order=1)]
    )
    res = val.validate_template(t)
    assert res.status == ReportValidationStatus.FAIL
    assert "disclaimer" in res.missing_required_sections

def test_unsafe_language_status():
    val = ReportTemplateValidator()
    unsafe = val.unsafe_language_findings("Bu kesin al diyor")
    assert "kesin al" in unsafe
    status = val.status_from_findings([], unsafe, [])
    assert status == ReportValidationStatus.BLOCKED
''')

# test_report_template_storage.py
Path("bist_signal_bot/tests/test_report_template_storage.py").write_text('''
from bist_signal_bot.report_templates.storage import ReportTemplateStore
from bist_signal_bot.report_templates.models import ReportTemplate, ReportTemplateKind
import pytest

def test_save_and_load_templates(tmp_path):
    store = ReportTemplateStore(base_dir=tmp_path)
    t = ReportTemplate(template_id="t1", name="test", kind=ReportTemplateKind.CUSTOM, version="1", description="")
    store.save_templates([t])
    loaded = store.load_templates()
    assert len(loaded) == 1
    assert loaded[0].template_id == "t1"
''')

# test_report_template_reporting.py
Path("bist_signal_bot/tests/test_report_template_reporting.py").write_text('''
from bist_signal_bot.report_templates.reporting import format_template_text, format_composed_report_text
from bist_signal_bot.report_templates.models import ReportTemplate, ReportTemplateKind, ComposedReport
from datetime import datetime

def test_format_template_text():
    t = ReportTemplate(template_id="t1", name="test_tmpl", kind=ReportTemplateKind.CUSTOM, version="1", description="")
    out = format_template_text(t)
    assert "test_tmpl" in out
    assert "CUSTOM" in out

def test_format_composed_report_text():
    r = ComposedReport(report_id="r1", template_id="t1", template_name="test_tmpl", kind=ReportTemplateKind.CUSTOM, generated_at=datetime.utcnow())
    out = format_composed_report_text(r)
    assert "r1" in out
    assert "test_tmpl" in out
    assert "local research software output only" in out
''')

print("Phase 103 Part 12 test files generated.")
