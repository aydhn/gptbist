from enum import Enum

import json
import os
from pathlib import Path
from .models import SyntheticScenarioSpec, SyntheticDataset, SyntheticScenarioManifest, SyntheticScenarioValidationResult, SyntheticStressCase, SyntheticEdgeCase, SyntheticScenarioReport, SyntheticOutputKind, SyntheticScenarioKind, SyntheticFrequency, SyntheticScenarioStatus

def _serialize(obj):
    if isinstance(obj, Enum): return obj.value
    if hasattr(obj, '__dict__'): return {k: _serialize(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, list): return [_serialize(v) for v in obj]
    if isinstance(obj, dict): return {k: _serialize(v) for k, v in obj.items()}
    from datetime import datetime
    if isinstance(obj, datetime): return obj.isoformat()
    return obj

class SyntheticScenarioStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.specs_file = self.base_dir / "specs" / "synthetic_specs.json"
        self.datasets_file = self.base_dir / "datasets" / "synthetic_datasets.jsonl"
        self.manifests_file = self.base_dir / "manifests" / "synthetic_manifests.jsonl"
        self.validations_file = self.base_dir / "validations" / "synthetic_validations.jsonl"
        self.stress_file = self.base_dir / "stress" / "synthetic_stress_cases.jsonl"
        self.edge_file = self.base_dir / "edge_cases" / "synthetic_edge_cases.jsonl"

    def _ensure_dirs(self):
        for f in [self.specs_file, self.datasets_file, self.manifests_file, self.validations_file, self.stress_file, self.edge_file]:
            f.parent.mkdir(parents=True, exist_ok=True)

    def save_specs(self, specs: list[SyntheticScenarioSpec]) -> Path:
        self._ensure_dirs()
        data = [_serialize(s) for s in specs]
        with open(self.specs_file, "w", encoding="utf-8") as f:
             json.dump(data, f, indent=2)
        return self.specs_file

    def load_specs(self) -> list[SyntheticScenarioSpec]:
        if not self.specs_file.exists(): return []
        with open(self.specs_file, "r", encoding="utf-8") as f:
             data = json.load(f)
             # simple stub load
             return []

    def append_dataset(self, dataset: SyntheticDataset) -> Path:
        self._ensure_dirs()
        with open(self.datasets_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(_serialize(dataset)) + "\n")
        return self.datasets_file

    def load_datasets(self, scenario_id: str | None = None, limit: int = 10000) -> list[SyntheticDataset]:
        return []

    def append_manifest(self, manifest: SyntheticScenarioManifest) -> Path:
        self._ensure_dirs()
        with open(self.manifests_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(_serialize(manifest)) + "\n")
        return self.manifests_file

    def load_latest_manifest(self, scenario_id: str | None = None) -> SyntheticScenarioManifest | None:
        return None

    def append_validation(self, result: SyntheticScenarioValidationResult) -> Path:
        self._ensure_dirs()
        with open(self.validations_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(_serialize(result)) + "\n")
        return self.validations_file

    def append_stress_cases(self, cases: list[SyntheticStressCase]) -> Path:
        self._ensure_dirs()
        with open(self.stress_file, "a", encoding="utf-8") as f:
             for c in cases:
                 f.write(json.dumps(_serialize(c)) + "\n")
        return self.stress_file

    def append_edge_cases(self, cases: list[SyntheticEdgeCase]) -> Path:
        self._ensure_dirs()
        with open(self.edge_file, "a", encoding="utf-8") as f:
             for c in cases:
                 f.write(json.dumps(_serialize(c)) + "\n")
        return self.edge_file

    def export_dataset(self, dataset: SyntheticDataset, output_dir: Path, format: str = "jsonl", confirm: bool = False) -> Path | None:
        if not confirm:
            print("Export requires confirmation")
            return None
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{dataset.dataset_id}.{format}"
        if format == "jsonl":
            with open(path, "w", encoding="utf-8") as f:
                 for row in dataset.rows:
                      f.write(json.dumps(row) + "\n")
        return path

    def save_report(self, report: SyntheticScenarioReport, markdown_text: str) -> dict[str, Path]:
        from datetime import datetime
        dstr = datetime.now().strftime("%Y%m%d")
        rdir = self.base_dir / "reports" / dstr
        rdir.mkdir(parents=True, exist_ok=True)
        md_path = rdir / "synthetic_scenario_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
             f.write(markdown_text)
        return {"markdown": md_path}
