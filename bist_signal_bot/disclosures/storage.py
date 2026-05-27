import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from bist_signal_bot.disclosures.models import (
    DisclosureRecord, DisclosureEntityLink, DisclosureRiskTag,
    DisclosureEventExtraction, DisclosureImpactAssessment, DisclosureDigest, DisclosureImportResult, DisclosureType
)
from bist_signal_bot.storage.paths import get_disclosures_dir

class DisclosureStore:
    def __init__(self, settings=None, base_dir=None):
        self.base_dir = base_dir or get_disclosures_dir(settings)
        self.records_path = self.base_dir / "records" / "disclosure_records.jsonl"
        self.entities_path = self.base_dir / "entities" / "disclosure_entity_links.jsonl"
        self.risk_tags_path = self.base_dir / "risk_tags" / "disclosure_risk_tags.jsonl"
        self.events_path = self.base_dir / "events" / "disclosure_event_extractions.jsonl"
        self.impact_path = self.base_dir / "impact" / "disclosure_impact_assessments.jsonl"
        self.digests_path = self.base_dir / "digests" / "disclosure_digests.jsonl"

        for path in [self.records_path, self.entities_path, self.risk_tags_path, self.events_path, self.impact_path, self.digests_path]:
            path.parent.mkdir(parents=True, exist_ok=True)

    def _append_jsonl(self, path: Path, data: dict):
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, default=str) + "\n")

    def _load_jsonl(self, path: Path) -> List[dict]:
        if not path.exists():
            return []
        res = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    res.append(json.loads(line))
        return res

    def append_record(self, record: DisclosureRecord) -> Path:
        self._append_jsonl(self.records_path, record.dict())
        return self.records_path

    def load_records(self, symbol: Optional[str] = None, disclosure_type: Optional[DisclosureType] = None, limit: int = 10000) -> List[DisclosureRecord]:
        raw = self._load_jsonl(self.records_path)
        records = []
        for r in raw:
            if symbol and symbol not in r.get("symbols", []):
                continue
            if disclosure_type and r.get("disclosure_type") != disclosure_type.value:
                continue
            records.append(DisclosureRecord(**r))
            if len(records) >= limit:
                break
        return records

    def get_record(self, disclosure_id: str) -> Optional[DisclosureRecord]:
        for r in self._load_jsonl(self.records_path):
            if r.get("disclosure_id") == disclosure_id:
                return DisclosureRecord(**r)
        return None

    def append_entity_links(self, links: List[DisclosureEntityLink]) -> Path:
        for link in links:
            self._append_jsonl(self.entities_path, link.dict())
        return self.entities_path

    def load_entity_links(self, disclosure_id: Optional[str] = None, limit: int = 10000) -> List[DisclosureEntityLink]:
        return []

    def append_risk_tags(self, tags: List[DisclosureRiskTag]) -> Path:
        for tag in tags:
            self._append_jsonl(self.risk_tags_path, tag.dict())
        return self.risk_tags_path

    def load_risk_tags(self, disclosure_id: Optional[str] = None, symbol: Optional[str] = None, limit: int = 10000) -> List[DisclosureRiskTag]:
        raw = self._load_jsonl(self.risk_tags_path)
        tags = []
        for r in raw:
            if disclosure_id and r.get("disclosure_id") != disclosure_id:
                continue
            # Note: simplified symbol checking
            tags.append(DisclosureRiskTag(**r))
            if len(tags) >= limit:
                break
        return tags

    def append_event_extractions(self, extractions: List[DisclosureEventExtraction]) -> Path:
        for ext in extractions:
            self._append_jsonl(self.events_path, ext.dict())
        return self.events_path

    def load_event_extractions(self, disclosure_id: Optional[str] = None, limit: int = 10000) -> List[DisclosureEventExtraction]:
        return []

    def append_impact_assessment(self, assessment: DisclosureImpactAssessment) -> Path:
        self._append_jsonl(self.impact_path, assessment.dict())
        return self.impact_path

    def load_impact_assessments(self, symbol: Optional[str] = None, limit: int = 10000) -> List[DisclosureImpactAssessment]:
        raw = self._load_jsonl(self.impact_path)
        assessments = []
        for r in raw:
            if symbol and symbol not in r.get("symbols", []):
                continue
            assessments.append(DisclosureImpactAssessment(**r))
            if len(assessments) >= limit:
                break
        return assessments

    def append_digest(self, digest: DisclosureDigest) -> Path:
        self._append_jsonl(self.digests_path, digest.dict())
        return self.digests_path

    def load_latest_digest(self, symbol: Optional[str] = None) -> Optional[DisclosureDigest]:
        return None

    def save_import_result(self, result: DisclosureImportResult) -> Dict[str, Path]:
        return {}

    def save_report(self, markdown_text: str) -> Path:
        path = self.base_dir / "reports" / "report.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
        return path
