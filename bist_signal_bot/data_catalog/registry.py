import uuid
from datetime import datetime, timezone
from pathlib import Path

from bist_signal_bot.data_catalog.models import (
    DatasetFormat,
    DatasetKind,
    DatasetRecord,
    DatasetStatus,
)
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.security.path_guard import PathGuard


class DataCatalogRegistry:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or get_settings()
        self.base_dir = base_dir
        self.path_guard = PathGuard(settings=self.settings, base_dir=self.base_dir)
        self._records: dict[str, DatasetRecord] = {}

    def register_dataset(
        self,
        path: Path,
        dataset_kind: DatasetKind,
        name: str | None = None,
        source_name: str | None = None,
        confirm: bool = False,
    ) -> DatasetRecord:

        # Path validation and redaction
        safe_path = self.path_guard.validate_and_resolve(path)
        redacted_path = str(self.path_guard.redact_path(safe_path))

        status = DatasetStatus.ACTIVE if safe_path.exists() else DatasetStatus.MISSING
        dataset_format = self.infer_format(safe_path)

        record = DatasetRecord(
            dataset_id=f"ds_{uuid.uuid4().hex[:12]}",
            name=name or path.stem,
            dataset_kind=dataset_kind,
            dataset_format=dataset_format,
            path=redacted_path,
            registered_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc) if status == DatasetStatus.ACTIVE else None,
            source_name=source_name,
            status=status,
        )

        if confirm:
            self._records[record.dataset_id] = record

        return record

    def discover_datasets(self, root: Path | None = None, confirm: bool = False) -> list[DatasetRecord]:
        if root is None:
            if self.base_dir:
                 root = self.base_dir / "data"
            else:
                 root = Path("data")

        if not root.exists() or not root.is_dir():
             return []

        records = []
        for file_path in root.rglob("*.*"):
             if file_path.is_file():
                 kind = self.infer_kind_from_path(file_path)
                 if kind != DatasetKind.CUSTOM:
                     record = self.register_dataset(
                         path=file_path,
                         dataset_kind=kind,
                         confirm=confirm
                     )
                     records.append(record)
        return records

    def list_datasets(self, kind: DatasetKind | None = None, status: DatasetStatus | None = None) -> list[DatasetRecord]:
        results = []
        for record in self._records.values():
            if kind and record.dataset_kind != kind:
                continue
            if status and record.status != status:
                continue
            results.append(record)
        return results

    def get_dataset(self, dataset_id: str) -> DatasetRecord | None:
        return self._records.get(dataset_id)

    def update_dataset_status(self, dataset_id: str, status: DatasetStatus, warning: str | None = None) -> DatasetRecord:
        record = self.get_dataset(dataset_id)
        if not record:
            raise ValueError(f"Dataset not found: {dataset_id}")

        record.status = status
        if warning:
            record.warnings.append(warning)
        return record

    def infer_kind_from_path(self, path: Path) -> DatasetKind:
        name = path.name.lower()
        if "ohlcv" in name and "adjusted" not in name:
            return DatasetKind.OHLCV
        if "adjusted_ohlcv" in name:
            return DatasetKind.ADJUSTED_OHLCV
        if "instrument" in name or "symbols" in name:
            return DatasetKind.INSTRUMENTS
        if "corporate" in name or "actions" in name:
            return DatasetKind.CORPORATE_ACTIONS
        if "event" in name:
            return DatasetKind.EVENTS
        if "disclosure" in name or "kap" in name:
             return DatasetKind.DISCLOSURES
        if "financial" in name or "balance_sheet" in name or "income_statement" in name:
             return DatasetKind.FINANCIALS
        if "macro" in name:
             return DatasetKind.MACRO
        if "valuation" in name:
             return DatasetKind.VALUATION
        if "factor" in name:
             return DatasetKind.FACTORS
        if "breadth" in name:
             return DatasetKind.BREADTH
        if "context" in name:
             return DatasetKind.CONTEXT
        if "review" in name:
             return DatasetKind.REVIEW_WORKFLOW
        if "qa" in name:
             return DatasetKind.QA
        if "ops" in name:
             return DatasetKind.OPS
        if "report" in name:
             return DatasetKind.REPORTS

        return DatasetKind.CUSTOM

    def infer_format(self, path: Path) -> DatasetFormat:
        if path.is_dir():
            return DatasetFormat.DIRECTORY

        ext = path.suffix.lower()
        if ext == ".csv":
            return DatasetFormat.CSV
        if ext == ".json":
            return DatasetFormat.JSON
        if ext == ".jsonl":
            return DatasetFormat.JSONL
        if ext == ".parquet":
            return DatasetFormat.PARQUET
        if ext in (".db", ".sqlite", ".sqlite3"):
            return DatasetFormat.SQLITE
        if ext == ".md":
            return DatasetFormat.MARKDOWN

        return DatasetFormat.UNKNOWN
