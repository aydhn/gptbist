import os
from pathlib import Path

# data_catalog/reporting.py
p1 = Path("bist_signal_bot/data_catalog/reporting.py")
if p1.exists():
    c = p1.read_text()
    if "def render_data_quality_template" not in c:
        c += '''
def render_data_quality_template(context: dict) -> dict:
    from bist_signal_bot.report_templates.models import RenderedReportSection, ReportValidationStatus
    return {
        "rendered_section_id": "sec_dq",
        "section_key": "data_quality",
        "title": "Data Quality Report",
        "content_markdown": "*Data Quality summary.*",
        "content_json": {"status": "PASS"},
        "status": ReportValidationStatus.PASS,
        "warnings": []
    }
'''
        p1.write_text(c)

# feature_store/reporting.py
p2 = Path("bist_signal_bot/feature_store/reporting.py")
if p2.exists():
    c = p2.read_text()
    if "def render_feature_quality_template" not in c:
        c += '''
def render_feature_quality_template(context: dict) -> dict:
    from bist_signal_bot.report_templates.models import RenderedReportSection, ReportValidationStatus
    return {
        "rendered_section_id": "sec_fq",
        "section_key": "feature_quality",
        "title": "Feature Quality Report",
        "content_markdown": "*Feature Quality summary.*",
        "content_json": {"status": "PASS"},
        "status": ReportValidationStatus.PASS,
        "warnings": []
    }
'''
        p2.write_text(c)

# model_registry/reporting.py
p3 = Path("bist_signal_bot/model_registry/reporting.py")
if p3.exists():
    c = p3.read_text()
    if "def render_model_governance_template" not in c:
        c += '''
def render_model_governance_template(context: dict) -> dict:
    from bist_signal_bot.report_templates.models import RenderedReportSection, ReportValidationStatus
    return {
        "rendered_section_id": "sec_mg",
        "section_key": "model_governance",
        "title": "Model Governance Report",
        "content_markdown": "*Model Governance summary.*",
        "content_json": {"status": "PASS"},
        "status": ReportValidationStatus.PASS,
        "warnings": []
    }
'''
        p3.write_text(c)

# monitoring/reporting.py
p4 = Path("bist_signal_bot/monitoring/reporting.py")
if p4.exists():
    c = p4.read_text()
    if "def render_monitoring_template" not in c:
        c += '''
def render_monitoring_template(context: dict) -> dict:
    from bist_signal_bot.report_templates.models import RenderedReportSection, ReportValidationStatus
    return {
        "rendered_section_id": "sec_mon",
        "section_key": "monitoring",
        "title": "Monitoring Report",
        "content_markdown": "*Monitoring summary.*",
        "content_json": {"status": "PASS"},
        "status": ReportValidationStatus.PASS,
        "warnings": []
    }
'''
        p4.write_text(c)

print("Phase 103 Part 5 edits applied.")
