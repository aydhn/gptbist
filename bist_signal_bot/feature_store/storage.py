import json
from pathlib import Path
from datetime import datetime
from typing import Any
from bist_signal_bot.feature_store.models import (
    FeatureContract, FeatureDefinition, FeatureSet, FeatureValue, FeatureFrame,
    FeatureQualityAssessment, FeatureDriftFinding, FeatureLeakageFinding,
    FeatureLineageEdge, FeatureVersion, FeatureStoreReport, FeatureKind
)
from bist_signal_bot.core.exceptions import FeatureStoreStorageError
from bist_signal_bot.storage.paths import get_feature_store_dir

class FeatureStore:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or get_feature_store_dir()
        self._init_dirs()

    def _init_dirs(self):
        dirs = [
            "contracts", "registry", "sets", "values", "frames",
            "quality", "drift", "leakage", "lineage", "versions", "reports"
        ]
        for d in dirs:
            (self.base_dir / d).mkdir(parents=True, exist_ok=True)

    def _save_json(self, path: Path, data: dict | list):
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            raise FeatureStoreStorageError(f"Failed to save {path}: {e}")

    def _append_jsonl(self, path: Path, data: dict):
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, default=str) + "\n")
        except Exception as e:
            raise FeatureStoreStorageError(f"Failed to append to {path}: {e}")

    def save_contracts(self, contracts: list[FeatureContract]) -> Path:
        path = self.base_dir / "contracts" / "feature_contracts.json"
        data = [c.model_dump(mode='json') for c in contracts]
        self._save_json(path, data)
        return path

    def load_contracts(self) -> list[FeatureContract]:
        path = self.base_dir / "contracts" / "feature_contracts.json"
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [FeatureContract(**d) for d in data]
        except Exception as e:
            raise FeatureStoreStorageError(f"Failed to load contracts: {e}")

    def append_feature_definition(self, feature: FeatureDefinition) -> Path:
        path = self.base_dir / "registry" / "feature_definitions.jsonl"
        self._append_jsonl(path, feature.model_dump(mode='json'))
        return path

    def load_feature_definitions(self, kind: FeatureKind | None = None, limit: int = 10000) -> list[FeatureDefinition]:
        path = self.base_dir / "registry" / "feature_definitions.jsonl"
        if not path.exists():
            return []
        features = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    feat = FeatureDefinition(**data)
                    if kind is None or feat.feature_kind == kind:
                        features.append(feat)
                        if len(features) >= limit:
                            break
            return features
        except Exception as e:
            raise FeatureStoreStorageError(f"Failed to load feature definitions: {e}")

    def append_feature_set(self, feature_set: FeatureSet) -> Path:
        path = self.base_dir / "sets" / "feature_sets.jsonl"
        self._append_jsonl(path, feature_set.model_dump(mode='json'))
        return path

    def load_feature_sets(self, limit: int = 10000) -> list[FeatureSet]:
        path = self.base_dir / "sets" / "feature_sets.jsonl"
        if not path.exists():
            return []
        sets = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    sets.append(FeatureSet(**data))
                    if len(sets) >= limit:
                        break
            return sets
        except Exception as e:
            raise FeatureStoreStorageError(f"Failed to load feature sets: {e}")

    def append_feature_values(self, values: list[FeatureValue]) -> Path:
        path = self.base_dir / "values" / "feature_values.jsonl"
        for v in values:
            self._append_jsonl(path, v.model_dump(mode='json'))
        return path

    def load_feature_values(self, feature_name: str | None = None, symbol: str | None = None, limit: int = 10000) -> list[FeatureValue]:
        path = self.base_dir / "values" / "feature_values.jsonl"
        if not path.exists():
            return []
        values = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    v = FeatureValue(**data)
                    match_feature = feature_name is None or v.feature_name == feature_name
                    match_symbol = symbol is None or v.symbol == symbol
                    if match_feature and match_symbol:
                        values.append(v)
                        if len(values) >= limit:
                            break
            return values
        except Exception as e:
            raise FeatureStoreStorageError(f"Failed to load feature values: {e}")

    def append_feature_frame(self, frame: FeatureFrame) -> Path:
        path = self.base_dir / "frames" / "feature_frames.jsonl"
        self._append_jsonl(path, frame.model_dump(mode='json'))
        return path

    def load_feature_frames(self, feature_set_id: str | None = None, limit: int = 1000) -> list[FeatureFrame]:
        path = self.base_dir / "frames" / "feature_frames.jsonl"
        if not path.exists():
            return []
        frames = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    f = FeatureFrame(**data)
                    if feature_set_id is None or f.feature_set_id == feature_set_id:
                        frames.append(f)
                        if len(frames) >= limit:
                            break
            return frames
        except Exception as e:
            raise FeatureStoreStorageError(f"Failed to load feature frames: {e}")

    def append_quality_assessment(self, assessment: FeatureQualityAssessment) -> Path:
        path = self.base_dir / "quality" / "feature_quality_assessments.jsonl"
        self._append_jsonl(path, assessment.model_dump(mode='json'))
        return path

    def append_drift_findings(self, findings: list[FeatureDriftFinding]) -> Path:
        path = self.base_dir / "drift" / "feature_drift_findings.jsonl"
        for f in findings:
            self._append_jsonl(path, f.model_dump(mode='json'))
        return path

    def append_leakage_findings(self, findings: list[FeatureLeakageFinding]) -> Path:
        path = self.base_dir / "leakage" / "feature_leakage_findings.jsonl"
        for f in findings:
            self._append_jsonl(path, f.model_dump(mode='json'))
        return path

    def append_lineage_edges(self, edges: list[FeatureLineageEdge]) -> Path:
        path = self.base_dir / "lineage" / "feature_lineage_edges.jsonl"
        for e in edges:
            self._append_jsonl(path, e.model_dump(mode='json'))
        return path

    def append_version(self, version: FeatureVersion) -> Path:
        path = self.base_dir / "versions" / "feature_versions.jsonl"
        self._append_jsonl(path, version.model_dump(mode='json'))
        return path

    def load_versions(self, feature_name: str | None = None, limit: int = 10000) -> list[FeatureVersion]:
        path = self.base_dir / "versions" / "feature_versions.jsonl"
        if not path.exists():
            return []
        versions = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    v = FeatureVersion(**data)
                    if feature_name is None or v.feature_name == feature_name:
                        versions.append(v)
                        if len(versions) >= limit:
                            break
            return versions
        except Exception as e:
            raise FeatureStoreStorageError(f"Failed to load versions: {e}")

    def save_report(self, report: FeatureStoreReport, markdown_text: str) -> dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        report_dir = self.base_dir / "reports" / date_str
        report_dir.mkdir(parents=True, exist_ok=True)

        md_path = report_dir / "feature_store_report.md"
        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(markdown_text)
        except Exception as e:
            raise FeatureStoreStorageError(f"Failed to save report markdown: {e}")

        json_path = report_dir / "feature_store_report.json"
        self._save_json(json_path, report.model_dump(mode='json'))

        return {"markdown": md_path, "json": json_path}
