import uuid
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.data_import.models import (
    ImportJob,
    ImportSource,
    ImportDatasetType,
    ImportStatus,
    SchemaMapping,
    NormalizedImportResult,
)
from bist_signal_bot.data_import.adapters import LocalImportAdapterRegistry
from bist_signal_bot.data_import.preview import ImportPreviewBuilder
from bist_signal_bot.data_import.schema_mapping import SchemaMappingEngine
from bist_signal_bot.data_import.validation import ImportValidationEngine
from bist_signal_bot.data_import.normalization import ImportNormalizer
from bist_signal_bot.data_import.chunking import ImportChunkReader
from bist_signal_bot.data_import.storage import DataImportStore
from bist_signal_bot.core.exceptions import LocalDataImporterError
from bist_signal_bot.security.path_guard import PathGuard

class LocalDataImporter:
    def __init__(self, settings: Any = None, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir
        self.registry = LocalImportAdapterRegistry(settings, base_dir)
        self.preview_builder = ImportPreviewBuilder(settings, base_dir)
        self.mapping_engine = SchemaMappingEngine(settings)
        self.validation_engine = ImportValidationEngine(settings, base_dir)
        self.normalizer = ImportNormalizer(settings)
        self.chunk_reader = ImportChunkReader(settings, base_dir)
        self.store = DataImportStore(settings, base_dir)

    def run_import(self, path: Path, dataset_type: ImportDatasetType, output_dir: Path | None = None, dry_run: bool = True, confirm: bool = False, save_catalog: bool = False) -> ImportJob:
        if not dry_run and getattr(self.settings, "DATA_IMPORT_WRITE_REQUIRES_CONFIRM", True) and not confirm:
             raise LocalDataImporterError("Writing to disk requires explicit confirmation (--confirm).")

        job_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)

        # Build source
        source = self.build_source(path, dataset_type)

        # Preview
        preview = self.preview_builder.build_preview(path, dataset_type)
        preview.source_id = source.source_id

        # Mapping
        mapping = self.mapping_engine.infer_mapping(preview.columns, dataset_type)

        # Validate
        validation = self.validation_engine.validate_source(source, mapping, preview)

        if validation.status in (ImportStatus.FAIL, ImportStatus.BLOCKED):
            return ImportJob(
                job_id=job_id,
                source=source,
                schema_mapping=mapping,
                preview=preview,
                validation=validation,
                dry_run=dry_run,
                confirm=confirm,
                status=validation.status,
                started_at=started_at,
                finished_at=datetime.now(timezone.utc),
                warnings=validation.warnings,
                errors=["Validation failed. Aborting import."]
            )

        # Normalize
        normalized_result = None
        if not dry_run and confirm:
             normalized_result = self.normalize_and_write(source, mapping, output_dir, confirm=confirm)

        job_status = ImportStatus.PASS if not dry_run else ImportStatus.DRY_RUN
        warnings = validation.warnings.copy()

        if normalized_result and normalized_result.status != ImportStatus.PASS:
             job_status = normalized_result.status
             warnings.extend(normalized_result.warnings)

        job = ImportJob(
            job_id=job_id,
            source=source,
            schema_mapping=mapping,
            preview=preview,
            validation=validation,
            normalized_result=normalized_result,
            dry_run=dry_run,
            confirm=confirm,
            status=job_status,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            warnings=warnings
        )

        # Optionally register catalog
        if save_catalog and not dry_run and confirm:
            if getattr(self.settings, "DATA_IMPORT_REGISTER_CATALOG_REQUIRES_CONFIRM", True):
                self.register_catalog(job, confirm=confirm)

        # Store job
        if getattr(self.settings, "DATA_IMPORT_SAVE_RESULTS", True):
            self.store.append_job(job)

        return job

    def build_source(self, path: Path, dataset_type: ImportDatasetType) -> ImportSource:
        fmt = self.registry.infer_format(path)
        size = path.stat().st_size if path.exists() else None

        return ImportSource(
            source_id=str(uuid.uuid4()),
            path=str(path),
            source_format=fmt,
            dataset_type=dataset_type,
            created_at=datetime.now(timezone.utc),
            size_bytes=size
        )

    def normalize_and_write(self, source: ImportSource, mapping: SchemaMapping, output_dir: Path | None, confirm: bool = False) -> NormalizedImportResult:
        if not confirm:
             raise LocalDataImporterError("Writing to disk requires explicit confirmation.")

        if not output_dir:
             from bist_signal_bot.storage.paths import get_data_dir
             output_dir = get_data_dir(self.settings) / "normalized" / source.dataset_type.lower()

        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"{source.source_id}.parquet"
        PathGuard.ensure_safe_path(out_path, self.base_dir)

        in_path = Path(source.path)

        if getattr(self.settings, "DATA_IMPORT_CHUNKING_ENABLED", True):
             # chunked write
             chunk_size = getattr(self.settings, "DATA_IMPORT_CHUNK_SIZE", 50000)
             try:
                 chunks = self.chunk_reader.normalize_chunks(in_path, mapping, source.dataset_type, chunk_size)
                 import pyarrow as pa
                 import pyarrow.parquet as pq

                 writer = None
                 total_rows = 0
                 dup_removed = 0
                 inv_removed = 0
                 columns = []

                 for chunk, stats in chunks:
                     total_rows += len(chunk)
                     dup_removed += stats.get("duplicate_rows_removed", 0)
                     inv_removed += stats.get("invalid_rows_removed", 0)
                     if not columns:
                         columns = list(chunk.columns)

                     table = pa.Table.from_pandas(chunk)
                     if writer is None:
                         writer = pq.ParquetWriter(out_path, table.schema)
                     writer.write_table(table)

                 if writer:
                     writer.close()

                 return NormalizedImportResult(
                     normalized_id=str(uuid.uuid4()),
                     source_id=source.source_id,
                     dataset_type=source.dataset_type,
                     created_at=datetime.now(timezone.utc),
                     output_path=str(out_path),
                     row_count=total_rows,
                     column_count=len(columns),
                     normalized_columns=columns,
                     duplicate_rows_removed=dup_removed,
                     invalid_rows_removed=inv_removed,
                     status=ImportStatus.PASS
                 )
             except Exception as e:
                 return NormalizedImportResult(
                     normalized_id=str(uuid.uuid4()),
                     source_id=source.source_id,
                     dataset_type=source.dataset_type,
                     created_at=datetime.now(timezone.utc),
                     row_count=0,
                     column_count=0,
                     status=ImportStatus.FAIL,
                     warnings=[f"Chunk normalization failed: {e}"]
                 )
        else:
             # in-memory write
             try:
                 df = self.registry.read_dataframe(in_path)
                 df_norm, stats = self.normalizer.normalize_dataframe(df, mapping, source.dataset_type)
                 df_norm.to_parquet(out_path, index=False)

                 return NormalizedImportResult(
                     normalized_id=str(uuid.uuid4()),
                     source_id=source.source_id,
                     dataset_type=source.dataset_type,
                     created_at=datetime.now(timezone.utc),
                     output_path=str(out_path),
                     row_count=len(df_norm),
                     column_count=len(df_norm.columns),
                     normalized_columns=list(df_norm.columns),
                     duplicate_rows_removed=stats.get("duplicate_rows_removed", 0),
                     invalid_rows_removed=stats.get("invalid_rows_removed", 0),
                     status=ImportStatus.PASS
                 )
             except Exception as e:
                 return NormalizedImportResult(
                     normalized_id=str(uuid.uuid4()),
                     source_id=source.source_id,
                     dataset_type=source.dataset_type,
                     created_at=datetime.now(timezone.utc),
                     row_count=0,
                     column_count=0,
                     status=ImportStatus.FAIL,
                     warnings=[f"In-memory normalization failed: {e}"]
                 )

    def register_catalog(self, job: ImportJob, confirm: bool = False) -> dict[str, Any]:
        if not confirm:
            return {}
        # Simulate registration logic
        return {"catalog_id": "simulated", "status": "registered"}

    def import_summary(self, job: ImportJob) -> list[str]:
        summary = [f"Import Job {job.job_id} ({job.status})"]
        summary.append(f"Source: {job.source.path} [{job.source.dataset_type}]")
        if job.dry_run:
            summary.append("Mode: DRY_RUN (No files written)")
        if job.validation and job.validation.warnings:
            summary.append(f"Warnings: {len(job.validation.warnings)}")
        if job.normalized_result:
            summary.append(f"Normalized Rows: {job.normalized_result.row_count}")
            summary.append(f"Output: {job.normalized_result.output_path}")
        return summary
