import json
import csv
from pathlib import Path
from typing import List, Tuple
from datetime import datetime
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureImportResult, DisclosureType
from bist_signal_bot.core.exceptions import DisclosureImportError

class DisclosureImporter:
    def __init__(self):
        pass

    def import_file(self, path: Path, confirm: bool = False) -> DisclosureImportResult:
        result = DisclosureImportResult(
            import_id=f"imp_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            created_at=datetime.now(),
            source_path=str(path)
        )

        if not confirm:
            result.warnings.append("Dry run: confirm=False")
            return result

        try:
            if path.suffix == ".csv":
                records = self.parse_csv(path)
            elif path.suffix == ".json":
                records = self.parse_json(path)
            elif path.suffix == ".txt":
                records = [self.parse_txt(path)]
            else:
                raise DisclosureImportError(f"Unsupported file format: {path.suffix}")

            result.rows_seen = len(records)
            result.disclosures_imported = len(records)
            return result

        except Exception as e:
            result.errors.append(str(e))
            return result

    def import_folder(self, path: Path, confirm: bool = False) -> DisclosureImportResult:
        result = DisclosureImportResult(
            import_id=f"imp_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            created_at=datetime.now(),
            source_path=str(path)
        )

        if not confirm:
            result.warnings.append("Dry run: confirm=False")
            return result

        return result

    def parse_csv(self, path: Path) -> List[DisclosureRecord]:
        records = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                try:
                    if not row.get("title") or not row.get("body"):
                        continue

                    record = DisclosureRecord(
                        disclosure_id=f"csv_{i}",
                        title=row.get("title", ""),
                        body=row.get("body", ""),
                        disclosure_type=DisclosureType(row.get("disclosure_type", DisclosureType.UNKNOWN)),
                        symbols=[s.strip() for s in row.get("symbols", "").split(",") if s.strip()],
                        received_at=datetime.now(),
                        source=row.get("source", "csv_import"),
                        language=row.get("language", "tr")
                    )
                    records.append(record)
                except Exception:
                    continue
        return records

    def parse_json(self, path: Path) -> List[DisclosureRecord]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        records = []
        for i, item in enumerate(data):
            if not item.get("title") or not item.get("body"):
                continue

            record = DisclosureRecord(
                disclosure_id=f"json_{i}",
                title=item.get("title", ""),
                body=item.get("body", ""),
                received_at=datetime.now(),
                source=item.get("source", "json_import"),
                language=item.get("language", "tr")
            )
            records.append(record)
        return records

    def parse_txt(self, path: Path) -> DisclosureRecord:
        with open(path, "r", encoding="utf-8") as f:
            body = f.read()

        return DisclosureRecord(
            disclosure_id=f"txt_{path.name}",
            title=path.stem,
            body=body,
            received_at=datetime.now(),
            source="txt_import",
            language="tr"
        )

    def deduplicate(self, records: List[DisclosureRecord]) -> Tuple[List[DisclosureRecord], List[DisclosureRecord]]:
        return records, []

    def validate_records(self, records: List[DisclosureRecord]) -> List[str]:
        return []
