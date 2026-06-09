import uuid
from datetime import datetime
from typing import Any, Dict, Optional, List
from bist_signal_bot.report_templates.models import ComposedReport, ReportExportPack, ReportManifest

class ReportManifestBuilder:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def build_manifest(self, report: ComposedReport, pack: Optional[ReportExportPack] = None) -> ReportManifest:
        return ReportManifest(
            manifest_id=f"man_{uuid.uuid4().hex[:8]}",
            report_id=report.report_id,
            template_id=report.template_id,
            created_at=datetime.utcnow(),
            source_refs=self.source_refs(report),
            artifact_refs=self.artifact_refs(pack),
            checksum_manifest=self.checksum_manifest(pack),
            section_statuses=self.section_statuses(report)
        )

    def source_refs(self, report: ComposedReport) -> Dict[str, Any]:
        return {"template": report.template_id, "kind": report.kind.value}

    def artifact_refs(self, pack: Optional[ReportExportPack] = None) -> Dict[str, str]:
        if not pack:
            return {}
        return {a.artifact_id: a.path for a in pack.artifacts}

    def checksum_manifest(self, pack: Optional[ReportExportPack] = None) -> Dict[str, str]:
        if not pack:
            return {}
        return {a.path: a.checksum for a in pack.artifacts if a.checksum}

    def section_statuses(self, report: ComposedReport) -> Dict[str, str]:
        return {s.section_key: s.status.value for s in report.sections}

    def validate_manifest(self, manifest: ReportManifest) -> List[str]:
        findings = []
        if not manifest.report_id:
            findings.append("Missing report ID.")
        return findings
