
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
