import json
from pathlib import Path

from bist_signal_bot.data_catalog.models import (
    DataCatalogReport,
    DataLineageEdge,
    DataQualityAssessment,
    DataQualityGateResult,
    DatasetContract,
    DatasetKind,
    DatasetProfile,
    DatasetRecord,
    SchemaDriftFinding,
    SourceProvenance,
)
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.storage.paths import get_data_catalog_dir


class DataCatalogStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or get_settings()
        if base_dir:
             self.catalog_dir = base_dir / "data" / self.settings.DATA_CATALOG_DIR_NAME
             self.catalog_dir.mkdir(parents=True, exist_ok=True)
        else:
             self.catalog_dir = get_data_catalog_dir(self.settings)

    def _get_file(self, subdir: str, filename: str) -> Path:
        d = self.catalog_dir / subdir
        d.mkdir(parents=True, exist_ok=True)
        return d / filename

    def _append_jsonl(self, path: Path, data: dict):
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

    def _load_jsonl(self, path: Path, limit: int = 10000) -> list[dict]:
        if not path.exists():
            return []
        items = []
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= limit:
                    break
                if line.strip():
                    items.append(json.loads(line))
        return items

    def save_contracts(self, contracts: list[DatasetContract]) -> Path:
        path = self._get_file("contracts", "dataset_contracts.json")
        data = [c.model_dump() for c in contracts]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return path

    def load_contracts(self) -> list[DatasetContract]:
        path = self._get_file("contracts", "dataset_contracts.json")
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [DatasetContract(**item) for item in data]

    def append_dataset_record(self, record: DatasetRecord) -> Path:
        path = self._get_file("registry", "dataset_records.jsonl")
        self._append_jsonl(path, record.model_dump(mode="json"))
        return path

    def load_dataset_records(self, kind: DatasetKind | None = None, limit: int = 10000) -> list[DatasetRecord]:
        path = self._get_file("registry", "dataset_records.jsonl")
        items = self._load_jsonl(path, limit)
        records = []
        for item in items:
            record = DatasetRecord(**item)
            if kind and record.dataset_kind != kind:
                continue
            records.append(record)
        return records

    def get_dataset(self, dataset_id: str) -> DatasetRecord | None:
        records = self.load_dataset_records()
        for r in records:
            if r.dataset_id == dataset_id:
                return r
        return None

    def append_profile(self, profile: DatasetProfile) -> Path:
        path = self._get_file("profiles", "dataset_profiles.jsonl")
        self._append_jsonl(path, profile.model_dump(mode="json"))
        return path

    def load_profiles(self, dataset_id: str | None = None, limit: int = 10000) -> list[DatasetProfile]:
        path = self._get_file("profiles", "dataset_profiles.jsonl")
        items = self._load_jsonl(path, limit)
        profiles = []
        for item in items:
            p = DatasetProfile(**item)
            if dataset_id and p.dataset_id != dataset_id:
                 continue
            profiles.append(p)
        return profiles

    def append_quality_assessment(self, assessment: DataQualityAssessment) -> Path:
        path = self._get_file("quality", "data_quality_assessments.jsonl")
        self._append_jsonl(path, assessment.model_dump(mode="json"))
        return path

    def load_quality_assessments(self, dataset_id: str | None = None, limit: int = 10000) -> list[DataQualityAssessment]:
        path = self._get_file("quality", "data_quality_assessments.jsonl")
        items = self._load_jsonl(path, limit)
        assessments = []
        for item in items:
            a = DataQualityAssessment(**item)
            if dataset_id and a.dataset_id != dataset_id:
                 continue
            assessments.append(a)
        return assessments

    def append_drift_findings(self, findings: list[SchemaDriftFinding]) -> Path:
        path = self._get_file("drift", "schema_drift_findings.jsonl")
        for f in findings:
            self._append_jsonl(path, f.model_dump(mode="json"))
        return path

    def load_drift_findings(self, dataset_id: str | None = None, limit: int = 10000) -> list[SchemaDriftFinding]:
        path = self._get_file("drift", "schema_drift_findings.jsonl")
        items = self._load_jsonl(path, limit)
        findings = []
        for item in items:
            f = SchemaDriftFinding(**item)
            if dataset_id and f.dataset_id != dataset_id:
                 continue
            findings.append(f)
        return findings

    def append_lineage_edges(self, edges: list[DataLineageEdge]) -> Path:
        path = self._get_file("lineage", "data_lineage_edges.jsonl")
        for e in edges:
            self._append_jsonl(path, e.model_dump(mode="json"))
        return path

    def load_lineage_edges(self, dataset_id: str | None = None, limit: int = 10000) -> list[DataLineageEdge]:
        path = self._get_file("lineage", "data_lineage_edges.jsonl")
        items = self._load_jsonl(path, limit)
        edges = []
        for item in items:
            e = DataLineageEdge(**item)
            if dataset_id and (e.from_dataset_id != dataset_id and e.to_dataset_id != dataset_id):
                 continue
            edges.append(e)
        return edges

    def append_provenance(self, provenance: SourceProvenance) -> Path:
        path = self._get_file("provenance", "source_provenance.jsonl")
        self._append_jsonl(path, provenance.model_dump(mode="json"))
        return path

    def load_provenance(self, dataset_id: str | None = None, limit: int = 10000) -> list[SourceProvenance]:
        path = self._get_file("provenance", "source_provenance.jsonl")
        items = self._load_jsonl(path, limit)
        prov = []
        for item in items:
            p = SourceProvenance(**item)
            if dataset_id and p.dataset_id != dataset_id:
                 continue
            prov.append(p)
        return prov

    def append_gate_result(self, result: DataQualityGateResult) -> Path:
        path = self._get_file("gates", "data_quality_gate_results.jsonl")
        self._append_jsonl(path, result.model_dump(mode="json"))
        return path

    def load_latest_gate_result(self, dataset_id: str | None = None) -> DataQualityGateResult | None:
        path = self._get_file("gates", "data_quality_gate_results.jsonl")
        items = self._load_jsonl(path, limit=10000)

        # Sort by created_at desc
        valid_items = []
        for item in items:
             res = DataQualityGateResult(**item)
             if dataset_id is None or res.dataset_id == dataset_id:
                 valid_items.append(res)

        if not valid_items:
             return None

        valid_items.sort(key=lambda x: x.created_at, reverse=True)
        return valid_items[0]

    def save_report(self, report: DataCatalogReport, markdown_text: str) -> dict[str, Path]:
        ymd = report.generated_at.strftime("%Y%m%d")
        d = self.catalog_dir / "reports" / ymd
        d.mkdir(parents=True, exist_ok=True)

        json_path = d / f"{report.report_id}.json"
        md_path = d / f"{report.report_id}.md"

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(mode="json"), f, indent=2)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        return {"json": json_path, "markdown": md_path}
