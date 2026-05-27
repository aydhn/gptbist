import os
from pathlib import Path

base_dir = Path("bist_signal_bot")

# 6. financials/importer.py
with open(base_dir / "financials" / "importer.py", "w") as f:
    f.write('''import csv
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
                        record.__post_init__()
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
                record.__post_init__()
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
                        record.__post_init__()
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
''')

# 7. financials/normalizer.py
with open(base_dir / "financials" / "normalizer.py", "w") as f:
    f.write('''import uuid
from typing import Any
from bist_signal_bot.financials.models import (
    FinancialStatementRecord,
    NormalizedFinancialStatement,
    FinancialPeriodType
)

class FinancialStatementNormalizer:
    def __init__(self, settings=None):
        self.settings = settings
        self.synonyms = {
            "revenue": ["revenue", "net sales", "satış gelirleri", "hasılat"],
            "gross_profit": ["gross profit", "brüt kar", "brüt kâr"],
            "operating_profit": ["operating profit", "faaliyet karı", "esas faaliyet kârı"],
            "ebitda": ["ebitda", "favök"],
            "net_income": ["net income", "net dönem karı", "net kâr"],
            "total_assets": ["total assets", "toplam varlıklar", "aktif toplamı"],
            "total_equity": ["total equity", "equity", "özkaynaklar", "toplam özkaynaklar"],
            "total_debt": ["total debt", "debt", "finansal borçlar", "kısa ve uzun vadeli borçlar"],
            "cash_and_equivalents": ["cash and equivalents", "cash", "nakit ve nakit benzerleri"],
            "operating_cash_flow": ["operating cash flow", "işletme faaliyetlerinden nakit akışı"],
            "capex": ["capex", "capital expenditure", "yatırım harcamaları"]
        }

    def normalize_records(self, records: list[FinancialStatementRecord]) -> list[NormalizedFinancialStatement]:
        groups = {}
        for r in records:
            key = (r.symbol, r.fiscal_year, r.fiscal_period)
            if key not in groups:
                groups[key] = []
            groups[key].append(r)

        results = []
        for key, recs in groups.items():
            results.append(self.normalize_symbol_period(key[0], key[1], key[2], recs))
        return results

    def normalize_symbol_period(self, symbol: str, fiscal_year: int, fiscal_period: str, records: list[FinancialStatementRecord]) -> NormalizedFinancialStatement:
        values = {}
        source_records = []
        period_end = None
        currency = "TRY"
        reported_at = None
        period_type = FinancialPeriodType.UNKNOWN

        for r in records:
            source_records.append(r.record_id)
            if r.period_end:
                period_end = r.period_end
            if r.currency:
                currency = r.currency
            if r.reported_at:
                reported_at = r.reported_at
            if r.period_type != FinancialPeriodType.UNKNOWN:
                period_type = r.period_type

            for k, v in r.values.items():
                mapped_k = self.map_item_name(k)
                if mapped_k:
                    values[mapped_k] = self.coerce_numeric(v)
                else:
                    values[k] = self.coerce_numeric(v) # Try direct mapping

        # Construct NormalizedFinancialStatement
        statement = NormalizedFinancialStatement(
            normalized_id=str(uuid.uuid4()),
            symbol=symbol,
            fiscal_year=fiscal_year,
            fiscal_period=fiscal_period,
            period_type=period_type,
            period_end=period_end, # type: ignore
            currency=currency,
            source_records=source_records,
            warnings=[],
            metadata={},
            reported_at=reported_at,
            revenue=values.get("revenue"),
            gross_profit=values.get("gross_profit"),
            operating_profit=values.get("operating_profit"),
            ebitda=values.get("ebitda"),
            net_income=values.get("net_income"),
            total_assets=values.get("total_assets"),
            total_equity=values.get("total_equity"),
            total_debt=values.get("total_debt"),
            cash_and_equivalents=values.get("cash_and_equivalents"),
            operating_cash_flow=values.get("operating_cash_flow"),
            capex=values.get("capex")
        )

        warnings = self.validate_normalized(statement)
        statement.warnings.extend(warnings)

        return statement

    def map_item_name(self, item_name: str) -> str | None:
        item_lower = item_name.lower().strip()
        for key, synonyms_list in self.synonyms.items():
            if item_lower in [s.lower() for s in synonyms_list]:
                return key
        return None

    def coerce_numeric(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            if isinstance(value, str):
                value = value.replace(",", "")
            return float(value)
        except (ValueError, TypeError):
            return None

    def validate_normalized(self, statement: NormalizedFinancialStatement) -> list[str]:
        warnings = []
        essential_fields = ["revenue", "net_income", "total_assets", "total_equity"]
        for field in essential_fields:
            if getattr(statement, field) is None:
                warnings.append(f"Missing essential field: {field}")
        return warnings
''')

# 8. financials/periods.py
with open(base_dir / "financials" / "periods.py", "w") as f:
    f.write('''from bist_signal_bot.financials.models import NormalizedFinancialStatement
from datetime import datetime

class FinancialPeriodEngine:
    def __init__(self, settings=None):
        self.settings = settings

    def sort_periods(self, statements: list[NormalizedFinancialStatement]) -> list[NormalizedFinancialStatement]:
        return sorted(statements, key=lambda s: (s.fiscal_year, s.fiscal_period))

    def previous_period(self, statement: NormalizedFinancialStatement, statements: list[NormalizedFinancialStatement]) -> NormalizedFinancialStatement | None:
        sorted_stmts = self.sort_periods(statements)
        idx = -1
        for i, s in enumerate(sorted_stmts):
            if s.normalized_id == statement.normalized_id:
                idx = i
                break

        if idx > 0:
            return sorted_stmts[idx - 1]
        return None

    def same_period_previous_year(self, statement: NormalizedFinancialStatement, statements: list[NormalizedFinancialStatement]) -> NormalizedFinancialStatement | None:
        target_year = statement.fiscal_year - 1
        for s in statements:
            if s.fiscal_year == target_year and s.fiscal_period == statement.fiscal_period:
                return s
        return None

    def build_ttm(self, symbol: str, statements: list[NormalizedFinancialStatement], as_of: datetime | None = None) -> NormalizedFinancialStatement | None:
        # Simplified TTM implementation
        sorted_stmts = self.sort_periods([s for s in statements if s.symbol == symbol])
        if not sorted_stmts:
            return None

        latest = sorted_stmts[-1]
        # In a real scenario, this would aggregate the last 4 quarters
        # For now, return the latest statement as a placeholder for TTM
        return latest

    def period_key(self, statement: NormalizedFinancialStatement) -> str:
        return f"{statement.fiscal_year}-{statement.fiscal_period}"
''')
