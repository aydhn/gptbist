import json
from pathlib import Path
from typing import List, Optional, Any
from bist_signal_bot.storage.paths import get_disclosures_dir
from bist_signal_bot.disclosures.models import (
    DisclosureRecord,
    DisclosureEntityLink,
    DisclosureRiskTag,
    DisclosureEventExtraction,
    DisclosureImpactAssessment,
    DisclosureDigest,
    DisclosureImportResult,
    DisclosureType
)

class DisclosureStore:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir or get_disclosures_dir(settings)
        self.records_file = self.base_dir / "records" / "disclosure_records.jsonl"
        self.entities_file = self.base_dir / "entities" / "disclosure_entity_links.jsonl"
        self.tags_file = self.base_dir / "risk_tags" / "disclosure_risk_tags.jsonl"
        self.events_file = self.base_dir / "events" / "disclosure_event_extractions.jsonl"
        self.impact_file = self.base_dir / "impact" / "disclosure_impact_assessments.jsonl"
        self.digests_file = self.base_dir / "digests" / "disclosure_digests.jsonl"

        for f in [self.records_file, self.entities_file, self.tags_file,
                  self.events_file, self.impact_file, self.digests_file]:
            f.parent.mkdir(parents=True, exist_ok=True)

    def _append_jsonl(self, filepath: Path, item: Any) -> Path:
        with open(filepath, 'a', encoding='utf-8') as f:
            # item.model_dump_json() is pydantic v2
            f.write(item.model_dump_json() + '\\n')
        return filepath

    def append_record(self, record: DisclosureRecord) -> Path:
        return self._append_jsonl(self.records_file, record)

    def load_records(self, symbol: Optional[str] = None, disclosure_type: Optional[DisclosureType] = None, limit: int = 10000) -> List[DisclosureRecord]:
        records = []
        if not self.records_file.exists():
            return records

        with open(self.records_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                try:
                    r = DisclosureRecord.model_validate_json(line)
                    if symbol and symbol not in r.symbols:
                        continue
                    if disclosure_type and r.disclosure_type != disclosure_type:
                        continue
                    records.append(r)
                except Exception:
                    pass

        return records[-limit:]

    def get_record(self, disclosure_id: str) -> Optional[DisclosureRecord]:
        if not self.records_file.exists():
            return None
        with open(self.records_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                try:
                    r = DisclosureRecord.model_validate_json(line)
                    if r.disclosure_id == disclosure_id:
                        return r
                except Exception:
                    pass
        return None

    def append_entity_links(self, links: List[DisclosureEntityLink]) -> Path:
        for link in links:
            self._append_jsonl(self.entities_file, link)
        return self.entities_file

    def load_entity_links(self, disclosure_id: Optional[str] = None, limit: int = 10000) -> List[DisclosureEntityLink]:
        links = []
        if not self.entities_file.exists():
            return links
        with open(self.entities_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                try:
                    l = DisclosureEntityLink.model_validate_json(line)
                    if disclosure_id and l.disclosure_id != disclosure_id:
                        continue
                    links.append(l)
                except Exception:
                    pass
        return links[-limit:]

    def append_risk_tags(self, tags: List[DisclosureRiskTag]) -> Path:
        for tag in tags:
            self._append_jsonl(self.tags_file, tag)
        return self.tags_file

    def load_risk_tags(self, disclosure_id: Optional[str] = None, symbol: Optional[str] = None, limit: int = 10000) -> List[DisclosureRiskTag]:
        tags = []
        if not self.tags_file.exists():
            return tags
        with open(self.tags_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                try:
                    t = DisclosureRiskTag.model_validate_json(line)
                    if disclosure_id and t.disclosure_id != disclosure_id:
                        continue
                    # Symbol filtering would require joining with record, ignoring for now or if tag had symbol
                    tags.append(t)
                except Exception:
                    pass
        return tags[-limit:]

    def append_event_extractions(self, extractions: List[DisclosureEventExtraction]) -> Path:
        for ex in extractions:
            self._append_jsonl(self.events_file, ex)
        return self.events_file

    def load_event_extractions(self, disclosure_id: Optional[str] = None, limit: int = 10000) -> List[DisclosureEventExtraction]:
        exts = []
        if not self.events_file.exists():
            return exts
        with open(self.events_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                try:
                    e = DisclosureEventExtraction.model_validate_json(line)
                    if disclosure_id and e.disclosure_id != disclosure_id:
                        continue
                    exts.append(e)
                except Exception:
                    pass
        return exts[-limit:]

    def append_impact_assessment(self, assessment: DisclosureImpactAssessment) -> Path:
        return self._append_jsonl(self.impact_file, assessment)

    def load_impact_assessments(self, symbol: Optional[str] = None, limit: int = 10000) -> List[DisclosureImpactAssessment]:
        assessments = []
        if not self.impact_file.exists():
            return assessments
        with open(self.impact_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                try:
                    a = DisclosureImpactAssessment.model_validate_json(line)
                    if symbol and symbol not in a.symbols:
                        continue
                    assessments.append(a)
                except Exception:
                    pass
        return assessments[-limit:]

    def append_digest(self, digest: DisclosureDigest) -> Path:
        return self._append_jsonl(self.digests_file, digest)

    def load_latest_digest(self, symbol: Optional[str] = None) -> Optional[DisclosureDigest]:
        # Very crude implementation, read all, return last
        digests = []
        if not self.digests_file.exists():
            return None
        with open(self.digests_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                try:
                    d = DisclosureDigest.model_validate_json(line)
                    if symbol and symbol not in d.symbols_covered:
                        continue
                    digests.append(d)
                except Exception:
                    pass
        return digests[-1] if digests else None

    def save_import_result(self, result: DisclosureImportResult) -> dict:
        date_str = result.created_at.strftime('%Y%m%d')
        dir_path = self.base_dir / "imports" / date_str / result.import_id
        dir_path.mkdir(parents=True, exist_ok=True)

        file_path = dir_path / "disclosure_import_result.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(result.model_dump_json(indent=2))

        return {"file_path": file_path}

    def save_report(self, markdown_text: str) -> Path:
        from datetime import datetime
        date_str = datetime.now().strftime('%Y%m%d')
        dir_path = self.base_dir / "reports" / date_str
        dir_path.mkdir(parents=True, exist_ok=True)

        file_path = dir_path / "disclosure_report.md"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_text)

        return file_path
