import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.core.exceptions import DisclosureStorageError
from bist_signal_bot.disclosures.models import (
    DisclosureRecord, DisclosureEntityLink, DisclosureRiskTag, DisclosureEventExtraction,
    DisclosureImpactAssessment, DisclosureDigest, DisclosureImportResult, DisclosureType
)

logger = logging.getLogger(__name__)

class DisclosureStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or get_settings()
        self.base_dir = base_dir or Path("data/disclosures")

    def _ensure_file(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _append_jsonl(self, path: Path, model: Any) -> Path:
        try:
            self._ensure_file(path)
            with open(path, "a", encoding="utf-8") as f:
                f.write(model.model_dump_json() + "\n")
            return path
        except Exception as e:
            raise DisclosureStorageError(f"Failed to append to {path}: {e}") from e

    def _load_jsonl(self, path: Path, model_cls: Any, limit: int = 10000) -> List[Any]:
        if not path.exists(): return []
        results = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        obj = model_cls.model_validate_json(line)
                        results.append(obj)
                        if len(results) >= limit: break
                    except Exception: pass
            return results
        except Exception as e:
            raise DisclosureStorageError(f"Failed to read {path}: {e}") from e

    def append_record(self, record: DisclosureRecord) -> Path:
        return self._append_jsonl(self.base_dir / "records" / "disclosure_records.jsonl", record)

    def load_records(self, symbol: str | None = None, disclosure_type: DisclosureType | None = None, limit: int = 10000) -> List[DisclosureRecord]:
        records = self._load_jsonl(self.base_dir / "records" / "disclosure_records.jsonl", DisclosureRecord, limit * 10)
        filtered = []
        for r in records:
            if symbol and symbol not in r.symbols: continue
            if disclosure_type and r.disclosure_type != disclosure_type: continue
            filtered.append(r)
            if len(filtered) >= limit: break
        return filtered

    def get_record(self, disclosure_id: str) -> DisclosureRecord | None:
        path = self.base_dir / "records" / "disclosure_records.jsonl"
        if not path.exists(): return None
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    if data.get("disclosure_id") == disclosure_id:
                        return DisclosureRecord.model_validate(data)
                except Exception: continue
        return None

    def append_entity_links(self, links: List[DisclosureEntityLink]) -> Path:
        path = self.base_dir / "entities" / "disclosure_entity_links.jsonl"
        for link in links: self._append_jsonl(path, link)
        return path

    def load_entity_links(self, disclosure_id: str | None = None, limit: int = 10000) -> List[DisclosureEntityLink]:
        links = self._load_jsonl(self.base_dir / "entities" / "disclosure_entity_links.jsonl", DisclosureEntityLink, limit * 10)
        if disclosure_id: return [l for l in links if l.disclosure_id == disclosure_id][:limit]
        return links[:limit]

    def append_risk_tags(self, tags: List[DisclosureRiskTag]) -> Path:
        path = self.base_dir / "risk_tags" / "disclosure_risk_tags.jsonl"
        for tag in tags: self._append_jsonl(path, tag)
        return path

    def load_risk_tags(self, disclosure_id: str | None = None, symbol: str | None = None, limit: int = 10000) -> List[DisclosureRiskTag]:
        tags = self._load_jsonl(self.base_dir / "risk_tags" / "disclosure_risk_tags.jsonl", DisclosureRiskTag, limit * 10)
        if disclosure_id: tags = [t for t in tags if t.disclosure_id == disclosure_id]
        return tags[:limit]

    def append_event_extractions(self, extractions: List[DisclosureEventExtraction]) -> Path:
        path = self.base_dir / "events" / "disclosure_event_extractions.jsonl"
        for e in extractions: self._append_jsonl(path, e)
        return path

    def load_event_extractions(self, disclosure_id: str | None = None, limit: int = 10000) -> List[DisclosureEventExtraction]:
        exts = self._load_jsonl(self.base_dir / "events" / "disclosure_event_extractions.jsonl", DisclosureEventExtraction, limit * 10)
        if disclosure_id: exts = [e for e in exts if e.disclosure_id == disclosure_id]
        return exts[:limit]

    def append_impact_assessment(self, assessment: DisclosureImpactAssessment) -> Path:
        return self._append_jsonl(self.base_dir / "impact" / "disclosure_impact_assessments.jsonl", assessment)

    def load_impact_assessments(self, symbol: str | None = None, limit: int = 10000) -> List[DisclosureImpactAssessment]:
        ass = self._load_jsonl(self.base_dir / "impact" / "disclosure_impact_assessments.jsonl", DisclosureImpactAssessment, limit * 10)
        if symbol: ass = [a for a in ass if symbol in a.symbols]
        return ass[:limit]

    def append_digest(self, digest: DisclosureDigest) -> Path:
        return self._append_jsonl(self.base_dir / "digests" / "disclosure_digests.jsonl", digest)

    def load_latest_digest(self, symbol: str | None = None) -> DisclosureDigest | None:
        digests = self._load_jsonl(self.base_dir / "digests" / "disclosure_digests.jsonl", DisclosureDigest, 1000)
        if symbol: digests = [d for d in digests if symbol in d.symbols_covered]
        if not digests: return None
        digests.sort(key=lambda x: x.created_at, reverse=True)
        return digests[0]

    def save_import_result(self, result: DisclosureImportResult) -> Dict[str, Path]:
        date_str = result.created_at.strftime("%Y%m%d")
        path = self.base_dir / "imports" / date_str / result.import_id / "disclosure_import_result.json"
        self._ensure_file(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))
        return {"result_file": path}

    def save_report(self, markdown_text: str) -> Path:
        date_str = datetime.now().strftime("%Y%m%d")
        path = self.base_dir / "reports" / date_str / f"disclosure_report_{datetime.now().strftime('%H%M%S')}.md"
        self._ensure_file(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
        return path