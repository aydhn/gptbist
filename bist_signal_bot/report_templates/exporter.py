import uuid
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
