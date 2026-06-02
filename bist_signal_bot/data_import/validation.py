from pathlib import Path
import uuid
from typing import Any
from datetime import datetime, timezone

from bist_signal_bot.data_import.models import (
    ImportSource,
    SchemaMapping,
    ImportPreview,
    ImportValidationResult,
    ImportValidationFinding,
    ImportStatus,
    ImportSourceFormat
)
from bist_signal_bot.security.path_guard import PathGuard
from bist_signal_bot.core.exceptions import ImportValidationError

class ImportValidationEngine:
    def __init__(self, settings: Any = None, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir

    def validate_source(self, source: ImportSource, mapping: SchemaMapping | None = None, preview: ImportPreview | None = None) -> ImportValidationResult:
        findings = []

        findings.extend(self.check_unsafe_path(source))
        if any(f.status == ImportStatus.BLOCKED for f in findings):
            return self._build_result(source, findings, mapping)

        findings.extend(self.check_file_exists(source))
        findings.extend(self.check_supported_format(source))
        findings.extend(self.check_required_columns(mapping))
        findings.extend(self.check_sample_values(preview, mapping))
        findings.extend(self.check_duplicate_preview_rows(preview))

        return self._build_result(source, findings, mapping)

    def _build_result(self, source: ImportSource, findings: list[ImportValidationFinding], mapping: SchemaMapping | None) -> ImportValidationResult:
        status = self.status_from_findings(findings)
        warnings = [f.message for f in findings if f.status in (ImportStatus.WATCH, ImportStatus.FAIL)]

        return ImportValidationResult(
            validation_id=str(uuid.uuid4()),
            source_id=source.source_id,
            created_at=datetime.now(timezone.utc),
            status=status,
            findings=findings,
            schema_mapping_id=mapping.schema_mapping_id if mapping else None,
            warnings=warnings
        )

    def check_file_exists(self, source: ImportSource) -> list[ImportValidationFinding]:
        path = Path(source.path)
        if not path.is_file():
            return [ImportValidationFinding(
                finding_id=str(uuid.uuid4()),
                source_id=source.source_id,
                rule_name="file_exists",
                status=ImportStatus.FAIL,
                severity="HIGH",
                message=f"File not found: {path}"
            )]
        return []

    def check_supported_format(self, source: ImportSource) -> list[ImportValidationFinding]:
        if source.source_format == ImportSourceFormat.UNKNOWN:
             return [ImportValidationFinding(
                finding_id=str(uuid.uuid4()),
                source_id=source.source_id,
                rule_name="supported_format",
                status=ImportStatus.FAIL,
                severity="HIGH",
                message=f"Unsupported format for path: {source.path}"
            )]
        return []

    def check_required_columns(self, mapping: SchemaMapping | None) -> list[ImportValidationFinding]:
        if not mapping:
            return []

        if mapping.missing_required_targets:
             status = ImportStatus.FAIL if getattr(self.settings, "DATA_IMPORT_FAIL_ON_MISSING_REQUIRED", True) else ImportStatus.WATCH
             return [ImportValidationFinding(
                finding_id=str(uuid.uuid4()),
                source_id=mapping.schema_mapping_id, # not exactly source id, but context
                rule_name="required_columns",
                status=status,
                severity="HIGH" if status == ImportStatus.FAIL else "MEDIUM",
                message=f"Missing required columns: {', '.join(mapping.missing_required_targets)}",
                affected_columns=mapping.missing_required_targets
             )]
        return []

    def check_sample_values(self, preview: ImportPreview | None, mapping: SchemaMapping | None) -> list[ImportValidationFinding]:
        if not preview or not mapping:
             return []

        findings = []
        for row in preview.sample_rows:
             for m in mapping.column_mappings:
                 if m.required and m.source_column in row:
                      val = row[m.source_column]
                      if val is None:
                           findings.append(ImportValidationFinding(
                                finding_id=str(uuid.uuid4()),
                                source_id=preview.preview_id,
                                rule_name="sample_values_null_required",
                                status=ImportStatus.WATCH,
                                severity="MEDIUM",
                                message=f"Required column '{m.source_column}' contains nulls in preview sample.",
                                affected_columns=[m.source_column]
                           ))
                           break # report once per column
        return findings

    def check_duplicate_preview_rows(self, preview: ImportPreview | None) -> list[ImportValidationFinding]:
        if not preview or not preview.sample_rows:
             return []

        # simple hashable check
        import json
        seen = set()
        duplicates = 0
        for row in preview.sample_rows:
            try:
                row_str = json.dumps(row, sort_keys=True)
                if row_str in seen:
                    duplicates += 1
                seen.add(row_str)
            except TypeError:
                pass

        if duplicates > 0:
            return [ImportValidationFinding(
                finding_id=str(uuid.uuid4()),
                source_id=preview.preview_id,
                rule_name="duplicate_sample_rows",
                status=ImportStatus.WATCH,
                severity="LOW",
                message=f"Found {duplicates} duplicate rows in preview sample.",
                affected_rows_count=duplicates
            )]
        return []

    def check_unsafe_path(self, source: ImportSource) -> list[ImportValidationFinding]:
        path = Path(source.path)
        try:
             PathGuard.ensure_safe_path(path, self.base_dir)
             return []
        except Exception as e:
             return [ImportValidationFinding(
                finding_id=str(uuid.uuid4()),
                source_id=source.source_id,
                rule_name="unsafe_path",
                status=ImportStatus.BLOCKED,
                severity="CRITICAL",
                message=f"Unsafe path detected: {e}"
             )]

    def status_from_findings(self, findings: list[ImportValidationFinding]) -> ImportStatus:
        statuses = [f.status for f in findings]
        if ImportStatus.BLOCKED in statuses:
            return ImportStatus.BLOCKED
        if ImportStatus.FAIL in statuses:
            return ImportStatus.FAIL
        if ImportStatus.WATCH in statuses:
            return ImportStatus.WATCH
        return ImportStatus.PASS
