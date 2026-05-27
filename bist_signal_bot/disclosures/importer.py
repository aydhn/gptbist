import csv
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.core.exceptions import DisclosureImportError
from bist_signal_bot.disclosures.models import (
    DisclosureRecord, DisclosureType, DisclosureProcessingStatus, DisclosureImportResult
)
from bist_signal_bot.security.redaction import SecretRedactor

logger = logging.getLogger(__name__)

class DisclosureImporter:
    def __init__(self, settings: Settings | None = None, store=None, normalizer=None, classifier=None, linker=None, tagger=None, extractor=None):
        self.settings = settings or get_settings()
        self.store = store
        self.normalizer = normalizer
        self.classifier = classifier
        self.linker = linker
        self.tagger = tagger
        self.extractor = extractor

    def import_file(self, path: Path, confirm: bool = False) -> DisclosureImportResult:
        import_id = str(uuid.uuid4())
        result = DisclosureImportResult(import_id=import_id, source_path=str(path))

        try:
            path = path.resolve()
            if not path.is_file():
                result.errors.append(f"File not found: {path}")
                return result

            records = []
            suffix = path.suffix.lower()
            if suffix == ".csv":
                records = self.parse_csv(path)
            elif suffix == ".json":
                records = self.parse_json(path)
            elif suffix == ".txt":
                records = [self.parse_txt(path)]
            else:
                result.errors.append(f"Unsupported file format: {suffix}")
                return result

            result.rows_seen = len(records)
            new_records, duplicates = self.deduplicate(records)
            result.duplicate_count = len(duplicates)

            validation_errors = self.validate_records(new_records)
            if validation_errors:
                result.errors.extend(validation_errors)

            valid_records = []
            for r in new_records:
                try:
                    r.title = str(r.title)
                    r.body = str(r.body)

                    if getattr(self.settings, 'DISCLOSURE_AUTO_NORMALIZE_ON_IMPORT', True) and self.normalizer:
                        r = self.normalizer.normalize(r)
                    if getattr(self.settings, 'DISCLOSURE_AUTO_CLASSIFY_ON_IMPORT', True) and self.classifier:
                        r = self.classifier.classify(r)

                    valid_records.append(r)
                except Exception as e:
                    logger.warning(f"Failed to process record {r.external_id or r.title}: {e}")
                    result.disclosures_skipped += 1

            if confirm and self.store:
                for r in valid_records:
                    self.store.append_record(r)

                    if getattr(self.settings, 'DISCLOSURE_AUTO_LINK_ENTITIES_ON_IMPORT', True) and self.linker:
                        links = self.linker.link_entities(r)
                        if links:
                            self.store.append_entity_links(links)

                    if getattr(self.settings, 'DISCLOSURE_AUTO_TAG_RISKS_ON_IMPORT', True) and self.tagger:
                        tags = self.tagger.tag(r)
                        if tags:
                            self.store.append_risk_tags(tags)

                    if getattr(self.settings, 'DISCLOSURE_AUTO_EXTRACT_EVENTS_ON_IMPORT', True) and self.extractor:
                        exts = self.extractor.extract_events(r)
                        if exts:
                            self.store.append_event_extractions(exts)

                self.store.save_import_result(result)
                result.disclosures_imported = len(valid_records)
            else:
                result.disclosures_imported = 0
                if valid_records and not confirm:
                    result.warnings.append("Confirm flag not set. No records were saved.")

            return result
        except Exception as e:
            logger.error(f"Disclosure import failed: {e}", exc_info=True)
            result.errors.append(str(e))
            raise DisclosureImportError(f"Import failed: {e}") from e

    def import_folder(self, path: Path, confirm: bool = False) -> DisclosureImportResult:
        import_id = str(uuid.uuid4())
        result = DisclosureImportResult(import_id=import_id, source_path=str(path))

        path = path.resolve()
        if not path.is_dir():
            result.errors.append(f"Directory not found: {path}")
            return result

        all_records = []
        for file_path in path.glob("**/*"):
            if not file_path.is_file():
                continue
            suffix = file_path.suffix.lower()
            try:
                if suffix == ".csv":
                    all_records.extend(self.parse_csv(file_path))
                elif suffix == ".json":
                    all_records.extend(self.parse_json(file_path))
                elif suffix == ".txt":
                    all_records.append(self.parse_txt(file_path))
            except Exception as e:
                result.errors.append(f"Failed to parse {file_path}: {e}")

        result.rows_seen = len(all_records)
        new_records, duplicates = self.deduplicate(all_records)
        result.duplicate_count = len(duplicates)

        valid_records = []
        for r in new_records:
            try:
                r.title = str(r.title)
                r.body = str(r.body)
                valid_records.append(r)
            except Exception as e:
                result.disclosures_skipped += 1

        if confirm and self.store:
            for r in valid_records:
                self.store.append_record(r)
            self.store.save_import_result(result)
            result.disclosures_imported = len(valid_records)
        else:
            result.disclosures_imported = 0
            if valid_records and not confirm:
                result.warnings.append("Confirm flag not set. No records were saved.")

        return result

    def parse_csv(self, path: Path) -> List[DisclosureRecord]:
        records = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    title = row.get("title", "")
                    body = row.get("body", "")
                    if not title.strip() and not body.strip():
                        continue

                    symbols = [s.strip() for s in row.get("symbols", "").split(",") if s.strip()]
                    pub_str = row.get("published_at")
                    pub_date = None
                    if pub_str:
                        try:
                            pub_date = datetime.fromisoformat(pub_str)
                        except ValueError:
                            pass

                    disc_type_str = row.get("disclosure_type", "UNKNOWN").upper()
                    try:
                        disc_type = DisclosureType(disc_type_str)
                    except ValueError:
                        disc_type = DisclosureType.UNKNOWN

                    record = DisclosureRecord(
                        disclosure_id=str(uuid.uuid4()),
                        external_id=row.get("external_id"),
                        title=title,
                        body=body,
                        disclosure_type=disc_type,
                        published_at=pub_date,
                        symbols=symbols,
                        company_names=[c.strip() for c in row.get("company_names", "").split(",") if c.strip()],
                        sectors=[s.strip() for s in row.get("sectors", "").split(",") if s.strip()],
                        source=row.get("source", "LOCAL_CSV"),
                        source_ref=row.get("source_ref"),
                        language=row.get("language", "tr"),
                        tags=[t.strip() for t in row.get("tags", "").split(",") if t.strip()]
                    )
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Error parsing CSV row {row}: {e}")
        return records

    def parse_json(self, path: Path) -> List[DisclosureRecord]:
        records = []
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                try:
                    title = item.get("title", "")
                    body = item.get("body", "")
                    if not title.strip() and not body.strip():
                        continue

                    pub_str = item.get("published_at")
                    pub_date = None
                    if pub_str:
                        try:
                            pub_date = datetime.fromisoformat(pub_str)
                        except ValueError:
                            pass

                    disc_type_str = item.get("disclosure_type", "UNKNOWN").upper()
                    try:
                        disc_type = DisclosureType(disc_type_str)
                    except ValueError:
                        disc_type = DisclosureType.UNKNOWN

                    record = DisclosureRecord(
                        disclosure_id=str(uuid.uuid4()),
                        external_id=item.get("external_id"),
                        title=title,
                        body=body,
                        disclosure_type=disc_type,
                        published_at=pub_date,
                        symbols=item.get("symbols", []),
                        company_names=item.get("company_names", []),
                        sectors=item.get("sectors", []),
                        source=item.get("source", "LOCAL_JSON"),
                        source_ref=item.get("source_ref"),
                        language=item.get("language", "tr"),
                        tags=item.get("tags", [])
                    )
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Error parsing JSON item {item}: {e}")
        return records

    def parse_txt(self, path: Path) -> DisclosureRecord:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n', 1)
        title = lines[0] if lines else path.name
        body = lines[1] if len(lines) > 1 else content

        return DisclosureRecord(
            disclosure_id=str(uuid.uuid4()),
            title=title,
            body=body,
            source="LOCAL_TXT",
            source_ref=path.name
        )

    def deduplicate(self, records: List[DisclosureRecord]) -> Tuple[List[DisclosureRecord], List[DisclosureRecord]]:
        seen = set()
        new_records = []
        duplicates = []

        for r in records:
            key = r.external_id if r.external_id else r.body
            if key in seen:
                duplicates.append(r)
            else:
                seen.add(key)
                new_records.append(r)

        return new_records, duplicates

    def validate_records(self, records: List[DisclosureRecord]) -> List[str]:
        errors = []
        for i, r in enumerate(records):
            if not r.title.strip() and not r.body.strip():
                errors.append(f"Record {i} missing title and body.")
            if not r.source:
                r.warnings.append("Missing source.")
        return errors