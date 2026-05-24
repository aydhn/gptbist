import csv
import json
from pathlib import Path
from typing import Dict, Any, List
import logging
from bist_signal_bot.instruments.models import InstrumentRecord, InstrumentType, InstrumentStatus
from bist_signal_bot.data.reconciliation import DataQualityIssue

logger = logging.getLogger(__name__)

class InstrumentImporter:
    def __init__(self, master):
        self.master = master

    def import_file(self, path: Path, confirm: bool = False) -> Dict[str, Any]:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        records = []
        if path.suffix.lower() == '.csv':
            records = self.parse_csv(path)
        elif path.suffix.lower() == '.json':
            records = self.parse_json(path)
        else:
            raise ValueError(f"Unsupported format: {path.suffix}")

        if confirm:
            for rec in records:
                self.master.upsert_instrument(rec, confirm_overwrite=True)

        return {
            "file": str(path),
            "rows_read": len(records),
            "imported": len(records) if confirm else 0,
            "dry_run": not confirm
        }

    def parse_csv(self, path: Path) -> List[InstrumentRecord]:
        records = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Simple mapping logic
                    status = row.get('status', 'UNKNOWN').upper()
                    if status not in [e.value for e in InstrumentStatus]:
                         status = 'UNKNOWN'

                    itype = row.get('instrument_type', 'EQUITY').upper()
                    if itype not in [e.value for e in InstrumentType]:
                        itype = 'EQUITY'

                    rec = InstrumentRecord(
                        symbol=row['symbol'],
                        isin=row.get('isin'),
                        name=row['name'],
                        instrument_type=InstrumentType(itype),
                        status=InstrumentStatus(status),
                        sector=row.get('sector')
                    )
                    records.append(rec)
                except Exception as e:
                    logger.error(f"Error parsing row {row}: {e}")
        return records

    def parse_json(self, path: Path) -> List[InstrumentRecord]:
        records = []
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                try:
                    records.append(InstrumentRecord(**item))
                except Exception as e:
                    logger.error(f"Error parsing item {item}: {e}")
        return records

    def validate_records(self, records: List[InstrumentRecord]) -> List[DataQualityIssue]:
        return []
