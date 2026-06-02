import os
from pathlib import Path

# 6. exporter.py
with open("bist_signal_bot/report_templates/exporter.py", "w") as f:
    f.write('''import uuid
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from bist_signal_bot.report_templates.models import (
    ComposedReport, ReportExportPack, ReportExportArtifact, ReportOutputFormat, ReportValidationStatus
)
from bist_signal_bot.security.path_guard import PathGuard
from bist_signal_bot.security.redaction import SecretRedactor

class ReportExporter:
    def __init__(self, settings=None, base_dir: Optional[Path] = None):
        self.settings = settings
        self.base_dir = base_dir or Path.cwd()

    def export_report(self, report: ComposedReport, output_dir: Optional[Path] = None, formats: Optional[List[ReportOutputFormat]] = None, confirm: bool = False) -> ReportExportPack:
        out_dir = output_dir or (self.base_dir / "data" / "report_templates" / "exports" / datetime.utcnow().strftime("%Y%m%d"))
        if confirm:
            out_dir.mkdir(parents=True, exist_ok=True)
            PathGuard.ensure_safe_path(out_dir, self.base_dir)

        target_formats = formats or report.output_formats
        artifacts = []
        warnings = []

        if not confirm:
            warnings.append("Export not confirmed. Dry-run mode active; no files written permanently.")

        for fmt in target_formats:
            if fmt == ReportOutputFormat.MARKDOWN:
                artifacts.append(self.export_markdown(report, out_dir, confirm))
            elif fmt == ReportOutputFormat.JSON:
                artifacts.append(self.export_json(report, out_dir, confirm))
            elif fmt == ReportOutputFormat.TEXT:
                artifacts.append(self.export_text(report, out_dir, confirm))
            elif fmt in [ReportOutputFormat.HTML_DISABLED, ReportOutputFormat.PDF_DISABLED]:
                warnings.append(f"Format {fmt.value} is disabled.")

        return ReportExportPack(
            pack_id=f"exp_{uuid.uuid4().hex[:8]}",
            report_id=report.report_id,
            created_at=datetime.utcnow(),
            artifacts=artifacts,
            status=ReportValidationStatus.PASS,
            warnings=warnings
        )

    def export_markdown(self, report: ComposedReport, output_dir: Path, confirm: bool = False) -> ReportExportArtifact:
        path = output_dir / f"{report.report_id}.md"
        size = 0
        chk = None
        if confirm and report.markdown_text:
            PathGuard.ensure_safe_path(path, self.base_dir)
            with open(path, "w") as f:
                f.write(report.markdown_text)
            size = path.stat().st_size
            chk = self.checksum(path)

        return ReportExportArtifact(
            artifact_id=f"art_{uuid.uuid4().hex[:8]}",
            report_id=report.report_id,
            output_format=ReportOutputFormat.MARKDOWN,
            path=str(path),
            created_at=datetime.utcnow(),
            size_bytes=size,
            checksum=chk,
            status=ReportValidationStatus.PASS if confirm else ReportValidationStatus.WATCH
        )

    def export_json(self, report: ComposedReport, output_dir: Path, confirm: bool = False) -> ReportExportArtifact:
        path = output_dir / f"{report.report_id}.json"
        size = 0
        chk = None
        if confirm:
            PathGuard.ensure_safe_path(path, self.base_dir)
            redacted = SecretRedactor.redact_dict(report.json_payload)
            with open(path, "w") as f:
                json.dump(redacted, f, indent=2)
            size = path.stat().st_size
            chk = self.checksum(path)

        return ReportExportArtifact(
            artifact_id=f"art_{uuid.uuid4().hex[:8]}",
            report_id=report.report_id,
            output_format=ReportOutputFormat.JSON,
            path=str(path),
            created_at=datetime.utcnow(),
            size_bytes=size,
            checksum=chk,
            status=ReportValidationStatus.PASS if confirm else ReportValidationStatus.WATCH
        )

    def export_text(self, report: ComposedReport, output_dir: Path, confirm: bool = False) -> ReportExportArtifact:
        path = output_dir / f"{report.report_id}.txt"
        size = 0
        chk = None
        if confirm and report.markdown_text:
            PathGuard.ensure_safe_path(path, self.base_dir)
            with open(path, "w") as f:
                # Naive text conversion: just use markdown content
                f.write(report.markdown_text)
            size = path.stat().st_size
            chk = self.checksum(path)

        return ReportExportArtifact(
            artifact_id=f"art_{uuid.uuid4().hex[:8]}",
            report_id=report.report_id,
            output_format=ReportOutputFormat.TEXT,
            path=str(path),
            created_at=datetime.utcnow(),
            size_bytes=size,
            checksum=chk,
            status=ReportValidationStatus.PASS if confirm else ReportValidationStatus.WATCH
        )

    def checksum(self, path: Path) -> Optional[str]:
        if not path.exists():
            return None
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def validate_artifact(self, artifact: ReportExportArtifact) -> List[str]:
        findings = []
        if artifact.size_bytes is None or artifact.size_bytes == 0:
            findings.append("Artifact has zero size.")
        if not artifact.checksum:
            findings.append("Missing checksum.")
        return findings
''')

# 7. manifest.py
with open("bist_signal_bot/report_templates/manifest.py", "w") as f:
    f.write('''import uuid
from datetime import datetime
from typing import Any, Dict, Optional
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
''')

# 8. validation.py
with open("bist_signal_bot/report_templates/validation.py", "w") as f:
    f.write('''import uuid
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
''')

# 9. storage.py
with open("bist_signal_bot/report_templates/storage.py", "w") as f:
    f.write('''import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from bist_signal_bot.report_templates.models import (
    ReportTemplate, ReportSectionDefinition, ComposedReport, ReportExportPack,
    ReportManifest, ReportTemplateValidationResult, ReportTemplatesReport, ReportTemplateKind
)
from bist_signal_bot.storage.paths import get_report_templates_dir

class ReportTemplateStore:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir or get_report_templates_dir(settings)
        self.templates_file = self.base_dir / "templates" / "report_templates.json"
        self.sections_file = self.base_dir / "sections" / "report_sections.json"
        self.composed_file = self.base_dir / "composed" / "composed_reports.jsonl"
        self.exports_file = self.base_dir / "exports" / "report_export_packs.jsonl"
        self.manifests_file = self.base_dir / "manifests" / "report_manifests.jsonl"
        self.validations_file = self.base_dir / "validations" / "report_template_validations.jsonl"

        for p in [self.templates_file, self.sections_file, self.composed_file, self.exports_file, self.manifests_file, self.validations_file]:
            p.parent.mkdir(parents=True, exist_ok=True)

    def save_templates(self, templates: List[ReportTemplate]) -> Path:
        data = [t.model_dump(mode="json") for t in templates]
        with open(self.templates_file, "w") as f:
            json.dump(data, f, indent=2)
        return self.templates_file

    def load_templates(self) -> List[ReportTemplate]:
        if not self.templates_file.exists():
            return []
        with open(self.templates_file, "r") as f:
            data = json.load(f)
        return [ReportTemplate(**d) for d in data]

    def save_sections(self, sections: List[ReportSectionDefinition]) -> Path:
        data = [s.model_dump(mode="json") for s in sections]
        with open(self.sections_file, "w") as f:
            json.dump(data, f, indent=2)
        return self.sections_file

    def load_sections(self) -> List[ReportSectionDefinition]:
        if not self.sections_file.exists():
            return []
        with open(self.sections_file, "r") as f:
            data = json.load(f)
        return [ReportSectionDefinition(**d) for d in data]

    def append_composed_report(self, report: ComposedReport) -> Path:
        with open(self.composed_file, "a") as f:
            f.write(json.dumps(report.model_dump(mode="json")) + "\\n")
        return self.composed_file

    def load_composed_reports(self, limit: int = 1000) -> List[ComposedReport]:
        if not self.composed_file.exists():
            return []
        reports = []
        with open(self.composed_file, "r") as f:
            for line in f:
                if line.strip():
                    reports.append(ComposedReport(**json.loads(line)))
        return reports[-limit:]

    def load_latest_composed_report(self, kind: Optional[ReportTemplateKind] = None) -> Optional[ComposedReport]:
        reports = self.load_composed_reports()
        if kind:
            reports = [r for r in reports if r.kind == kind]
        return reports[-1] if reports else None

    def append_export_pack(self, pack: ReportExportPack) -> Path:
        with open(self.exports_file, "a") as f:
            f.write(json.dumps(pack.model_dump(mode="json")) + "\\n")
        return self.exports_file

    def append_manifest(self, manifest: ReportManifest) -> Path:
        with open(self.manifests_file, "a") as f:
            f.write(json.dumps(manifest.model_dump(mode="json")) + "\\n")
        return self.manifests_file

    def append_validation(self, result: ReportTemplateValidationResult) -> Path:
        with open(self.validations_file, "a") as f:
            f.write(json.dumps(result.model_dump(mode="json")) + "\\n")
        return self.validations_file

    def save_report(self, report: ReportTemplatesReport, markdown_text: str) -> Dict[str, Path]:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        report_dir = self.base_dir / "reports" / date_str
        report_dir.mkdir(parents=True, exist_ok=True)
        md_path = report_dir / "report_templates_report.md"
        json_path = report_dir / "report_templates_report.json"

        with open(md_path, "w") as f:
            f.write(markdown_text)
        with open(json_path, "w") as f:
            json.dump(report.model_dump(mode="json"), f, indent=2)

        return {"markdown": md_path, "json": json_path}
''')

# 10. reporting.py
with open("bist_signal_bot/report_templates/reporting.py", "w") as f:
    f.write('''from typing import Any, Dict
from bist_signal_bot.report_templates.models import (
    ReportSectionDefinition, ReportTemplate, RenderedReportSection, ComposedReport,
    ReportNarrativeBlock, ReportExportArtifact, ReportExportPack, ReportManifest,
    ReportTemplateValidationResult, ReportTemplatesReport
)

def section_definition_to_dict(section: ReportSectionDefinition) -> Dict[str, Any]:
    return section.model_dump(mode="json")

def template_to_dict(template: ReportTemplate) -> Dict[str, Any]:
    return template.model_dump(mode="json")

def rendered_section_to_dict(section: RenderedReportSection) -> Dict[str, Any]:
    return section.model_dump(mode="json")

def composed_report_to_dict(report: ComposedReport) -> Dict[str, Any]:
    return report.model_dump(mode="json")

def narrative_block_to_dict(block: ReportNarrativeBlock) -> Dict[str, Any]:
    return block.model_dump(mode="json")

def export_artifact_to_dict(artifact: ReportExportArtifact) -> Dict[str, Any]:
    return artifact.model_dump(mode="json")

def export_pack_to_dict(pack: ReportExportPack) -> Dict[str, Any]:
    return pack.model_dump(mode="json")

def manifest_to_dict(manifest: ReportManifest) -> Dict[str, Any]:
    return manifest.model_dump(mode="json")

def validation_to_dict(result: ReportTemplateValidationResult) -> Dict[str, Any]:
    return result.model_dump(mode="json")

def report_templates_report_to_dict(report: ReportTemplatesReport) -> Dict[str, Any]:
    return report.model_dump(mode="json")

def format_template_text(template: ReportTemplate) -> str:
    lines = [
        f"Template: {template.name} ({template.kind.value})",
        f"Status: {template.status.value}",
        f"Sections: {len(template.sections)}",
        f"Required: {', '.join(template.required_sections) if template.required_sections else 'None'}"
    ]
    return "\\n".join(lines)

def format_composed_report_text(report: ComposedReport) -> str:
    lines = [
        f"Report ID: {report.report_id}",
        f"Template: {report.template_name}",
        f"Status: {report.status.value}",
        f"Sections Rendered: {len(report.sections)}"
    ]
    if report.warnings:
        lines.append("Warnings:")
        for w in report.warnings:
            lines.append(f" - {w}")
    lines.append(f"\\nDisclaimer: {report.disclaimer}")
    return "\\n".join(lines)

def format_export_pack_text(pack: ReportExportPack) -> str:
    lines = [
        f"Pack ID: {pack.pack_id}",
        f"Report ID: {pack.report_id}",
        f"Artifacts: {len(pack.artifacts)}",
        f"Status: {pack.status.value}"
    ]
    return "\\n".join(lines)

def format_manifest_text(manifest: ReportManifest) -> str:
    lines = [
        f"Manifest ID: {manifest.manifest_id}",
        f"Report ID: {manifest.report_id}",
        f"Template: {manifest.template_id}",
        f"Artifacts: {len(manifest.artifact_refs)}"
    ]
    return "\\n".join(lines)

def format_validation_text(result: ReportTemplateValidationResult) -> str:
    lines = [
        f"Validation Status: {result.status.value}",
        f"Findings: {len(result.findings)}",
        f"Unsafe Language: {len(result.unsafe_language_findings)}",
        f"Missing Required: {len(result.missing_required_sections)}"
    ]
    return "\\n".join(lines)

def format_report_templates_report_markdown(report: ReportTemplatesReport) -> str:
    lines = [
        f"# Report Templates Report",
        f"Date: {report.generated_at.isoformat()}",
        "",
        "## Summary",
        f"- Templates: {len(report.templates)}",
        f"- Composed Reports: {len(report.composed_reports)}",
        f"- Export Packs: {len(report.export_packs)}",
        f"- Validations: {len(report.validations)}",
    ]
    if report.key_findings:
        lines.append("\\n## Key Findings")
        for f in report.key_findings:
            lines.append(f"- {f}")

    lines.append(f"\\n> *{report.disclaimer}*")
    return "\\n".join(lines)
''')

print("Phase 103 Part 2 files created.")
