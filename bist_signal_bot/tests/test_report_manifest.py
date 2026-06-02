
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
