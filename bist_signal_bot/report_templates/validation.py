import uuid
from datetime import datetime
from typing import List, Optional
from bist_signal_bot.report_templates.models import (
    ReportTemplate, ComposedReport, ReportExportPack, ReportTemplateValidationResult, ReportValidationStatus
)

class ReportTemplateValidator:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def validate_template(self, template: ReportTemplate) -> ReportTemplateValidationResult:
        findings = []
        unsafe = []
        missing = self.missing_required_sections(template)

        if "disclaimer" not in [s.section_key for s in template.sections]:
            findings.append("Missing disclaimer in template sections.")
            missing.append("disclaimer")

        status = self.status_from_findings(findings, unsafe, missing)
        return ReportTemplateValidationResult(
            validation_id=f"val_{uuid.uuid4().hex[:8]}",
            template_id=template.template_id,
            created_at=datetime.utcnow(),
            status=status,
            findings=findings,
            unsafe_language_findings=unsafe,
            missing_required_sections=missing
        )

    def validate_report(self, report: ComposedReport) -> ReportTemplateValidationResult:
        findings = []
        unsafe = []
        missing = []
        # In a full implementation we would check the report against its template.
        # Here we just do basic content checks.
        if "disclaimer" not in report.disclaimer.lower():
             findings.append("Disclaimer text missing disclaimer keywords.")
        unsafe.extend(self.unsafe_language_findings(report.markdown_text or ""))

        status = self.status_from_findings(findings, unsafe, missing)
        return ReportTemplateValidationResult(
            validation_id=f"val_{uuid.uuid4().hex[:8]}",
            report_id=report.report_id,
            template_id=report.template_id,
            created_at=datetime.utcnow(),
            status=status,
            findings=findings,
            unsafe_language_findings=unsafe,
            missing_required_sections=missing
        )

    def validate_export_pack(self, pack: ReportExportPack) -> ReportTemplateValidationResult:
        findings = []
        if not pack.artifacts:
            findings.append("No artifacts exported.")
        status = ReportValidationStatus.FAIL if findings else ReportValidationStatus.PASS
        return ReportTemplateValidationResult(
            validation_id=f"val_{uuid.uuid4().hex[:8]}",
            report_id=pack.report_id,
            created_at=datetime.utcnow(),
            status=status,
            findings=findings
        )

    def missing_required_sections(self, template: ReportTemplate, report: Optional[ComposedReport] = None) -> List[str]:
        missing = []
        keys = [s.section_key for s in template.sections]
        for req in template.required_sections:
            if req not in keys:
                missing.append(req)

        if report:
            rep_keys = [s.section_key for s in report.sections]
            for req in template.required_sections:
                 if req not in rep_keys and req not in missing:
                     missing.append(req)
        return missing

    def unsafe_language_findings(self, text: str) -> List[str]:
        unsafe_keywords = ["al", "sat", "kesin al", "kesin sat", "hedef fiyat", "trade ready", "yatırım tavsiyesi"]
        findings = []
        for kw in unsafe_keywords:
            if kw in text.lower():
                findings.append(kw)
        return findings

    def status_from_findings(self, findings: List[str], unsafe: List[str], missing: List[str]) -> ReportValidationStatus:
        if unsafe:
            return ReportValidationStatus.BLOCKED
        if missing or ("Missing disclaimer in template sections." in findings):
            return ReportValidationStatus.FAIL
        if findings:
            return ReportValidationStatus.WATCH
        return ReportValidationStatus.PASS
