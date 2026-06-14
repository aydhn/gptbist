import csv
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from bist_signal_bot.core.exceptions import FinancialImportError
from bist_signal_bot.financials.models import (
    FinancialStatementRecord,
    FinancialDataStatus,
    FinancialStatementType,
    FinancialPeriodType,
    FinancialImportResult
)

class FinancialStatementImporter:
    def __init__(self, settings=None, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir

    def import_file(self, path: Path, confirm: bool = False) -> FinancialImportResult:
        if not path.exists():
            raise FinancialImportError(f"File not found: {path}")

        records = []
        result = FinancialImportResult(
            import_id=str(uuid.uuid4()),
            created_at=datetime.now(),
            source_path=str(path),
            rows_seen=0,
            records_imported=0,
            records_skipped=0,
            duplicate_count=0,
            warnings=[],
            errors=[],
            metadata={}
        )

        try:
            if path.suffix == ".csv":
                with path.open("r", encoding="utf-8") as f:
                    header = f.readline()
                if "item_name" in header and "item_value" in header:
                    records = self.parse_long_csv(path)
                else:
                    records = self.parse_wide_csv(path)
            elif path.suffix == ".json":
                records = self.parse_json(path)
            else:
                raise FinancialImportError(f"Unsupported file format: {path.suffix}")
        except Exception as e:
            result.errors.append(str(e))
            return result

        result.rows_seen = len(records)
        if not confirm and self.settings and getattr(self.settings, "FINANCIAL_IMPORT_REQUIRES_CONFIRM", True):
            result.warnings.append("Dry run. Confirm is required to import.")
            result.records_skipped = len(records)
            return result

        validation_errors = self.validate_records(records)
        if validation_errors:
            result.errors.extend(validation_errors)
            result.records_skipped = len(records)
            return result

        unique_records, duplicates = self.deduplicate(records)
        result.records_imported = len(unique_records)
        result.duplicate_count = len(duplicates)

        return result

    def parse_csv(self, path: Path) -> list[FinancialStatementRecord]:
        return self.parse_wide_csv(path) # default

    def parse_json(self, path: Path) -> list[FinancialStatementRecord]:
        records = []
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    data = [data]

                for item in data:
                    try:
                        record = FinancialStatementRecord(
                            record_id=str(uuid.uuid4()),
                            symbol=item.get("symbol", ""),
                            period_end=datetime.fromisoformat(item.get("period_end", "1970-01-01T00:00:00")),
                            currency=item.get("currency", "TRY"),
                            values=item.get("values", {}),
                            source=item.get("source", "json_import"),
                            status=FinancialDataStatus.RAW_IMPORTED,
                            warnings=[],
                            metadata={},
                            fiscal_year=int(item.get("fiscal_year", 0)),
                            fiscal_period=item.get("fiscal_period", "")
                        )
                        records.append(record)
                    except Exception as e:
                        continue
        except Exception as e:
             raise FinancialImportError(f"Failed to parse JSON: {e}")
        return records

    def parse_long_csv(self, path: Path) -> list[FinancialStatementRecord]:
        # Group by symbol, year, period
        records_dict = {}
        try:
            with path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = (row.get("symbol"), row.get("fiscal_year"), row.get("fiscal_period"))
                    if key not in records_dict:
                        records_dict[key] = {
                            "symbol": row.get("symbol", ""),
                            "fiscal_year": int(row.get("fiscal_year", 0)) if row.get("fiscal_year") else 0,
                            "fiscal_period": row.get("fiscal_period", ""),
                            "period_end": row.get("period_end", "1970-01-01T00:00:00"),
                            "currency": row.get("currency", "TRY"),
                            "source": row.get("source", "csv_import"),
                            "values": {}
                        }

                    item_name = row.get("item_name")
                    item_value = row.get("item_value")
                    if item_name and item_value:
                        try:
                            records_dict[key]["values"][item_name] = float(item_value)
                        except ValueError:
                            records_dict[key]["values"][item_name] = item_value
        except Exception as e:
            raise FinancialImportError(f"Failed to parse long CSV: {e}")

        records = []
        for key, data in records_dict.items():
            try:
                record = FinancialStatementRecord(
                    record_id=str(uuid.uuid4()),
                    symbol=data["symbol"],
                    period_end=datetime.fromisoformat(data["period_end"]),
                    currency=data["currency"],
                    values=data["values"],
                    source=data["source"],
                    status=FinancialDataStatus.RAW_IMPORTED,
                    warnings=[],
                    metadata={},
                    fiscal_year=data["fiscal_year"],
                    fiscal_period=data["fiscal_period"]
                )
                records.append(record)
            except Exception:
                continue
        return records

    def parse_wide_csv(self, path: Path) -> list[FinancialStatementRecord]:
        records = []
        try:
            with path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    values = {}
                    for k, v in row.items():
                        if k not in ["symbol", "fiscal_year", "fiscal_period", "period_end", "currency", "source"]:
                            if v:
                                try:
                                    values[k] = float(v)
                                except ValueError:
                                    values[k] = v

                    try:
                        record = FinancialStatementRecord(
                            record_id=str(uuid.uuid4()),
                            symbol=row.get("symbol", ""),
                            period_end=datetime.fromisoformat(row.get("period_end", "1970-01-01T00:00:00")),
                            currency=row.get("currency", "TRY"),
                            values=values,
                            source=row.get("source", "csv_import"),
                            status=FinancialDataStatus.RAW_IMPORTED,
                            warnings=[],
                            metadata={},
                            fiscal_year=int(row.get("fiscal_year", 0)) if row.get("fiscal_year") else 0,
                            fiscal_period=row.get("fiscal_period", "")
                        )
                        records.append(record)
                    except Exception:
                        continue
        except Exception as e:
            raise FinancialImportError(f"Failed to parse wide CSV: {e}")
        return records

    def deduplicate(self, records: list[FinancialStatementRecord]) -> tuple[list[FinancialStatementRecord], list[FinancialStatementRecord]]:
        seen = set()
        unique = []
        duplicates = []
        for r in records:
            key = (r.symbol, r.fiscal_year, r.fiscal_period, r.statement_type)
            if key in seen:
                duplicates.append(r)
            else:
                seen.add(key)
                unique.append(r)
        return unique, duplicates

    def validate_records(self, records: list[FinancialStatementRecord]) -> list[str]:
        errors = []
        for r in records:
            if not r.symbol:
                errors.append(f"Record {r.record_id} missing symbol")
            if not r.values:
                errors.append(f"Record {r.record_id} has empty values")
        return errors
