import csv
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime
import logging
from bist_signal_bot.corporate_actions.models import CorporateActionRecord, CorporateActionImportResult, CorporateActionType, CorporateActionStatus
from bist_signal_bot.data.reconciliation import DataQualityIssue

logger = logging.getLogger(__name__)

class CorporateActionImporter:
    def __init__(self, storage):
        self.storage = storage

    def import_file(self, path: Path, confirm: bool = False) -> CorporateActionImportResult:
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        records = []
        if path.suffix.lower() == '.csv':
            records = self.parse_csv(path)
        elif path.suffix.lower() == '.json':
            records = self.parse_json(path)
        else:
            raise ValueError(f"Unsupported format: {path.suffix}")

        unique_records, duplicates = self.deduplicate_actions(records)

        res = CorporateActionImportResult(
            import_id=f"imp_{datetime.utcnow().timestamp()}",
            source_path=str(path),
            rows_seen=len(records),
            actions_skipped=len(duplicates)
        )

        if confirm:
            # save to storage
            res.actions_imported = len(unique_records)

        return res

    def parse_csv(self, path: Path) -> List[CorporateActionRecord]:
        records = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                try:
                    rec = CorporateActionRecord(
                        action_id=row.get('action_id', f"act_{i}_{row['symbol']}"),
                        symbol=row['symbol'],
                        action_type=CorporateActionType(row.get('action_type', 'UNKNOWN').upper()),
                        status=CorporateActionStatus(row.get('status', 'CONFIRMED').upper()),
                        effective_date=datetime.strptime(row['effective_date'], "%Y-%m-%d"),
                        cash_amount=float(row['cash_amount']) if row.get('cash_amount') else None,
                        ratio=float(row['ratio']) if row.get('ratio') else None,
                        source="import"
                    )
                    records.append(rec)
                except Exception as e:
                    logger.error(f"Error parsing row {row}: {e}")
        return records

    def parse_json(self, path: Path) -> List[CorporateActionRecord]:
        return []

    def deduplicate_actions(self, actions: List[CorporateActionRecord]) -> Tuple[List[CorporateActionRecord], List[CorporateActionRecord]]:
        return actions, []

    def validate_before_save(self, actions: List[CorporateActionRecord]) -> List[DataQualityIssue]:
        return []
