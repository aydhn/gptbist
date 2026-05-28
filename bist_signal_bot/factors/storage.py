
import json
from pathlib import Path
from typing import List, Optional, Dict
from bist_signal_bot.factors.models import (
    FactorInputSnapshot, FactorScore, FactorExposure, SectorRotationScore,
    ThemeDefinition, ThemeExposure, FactorCrowdingAssessment, FactorAttributionItem, FactorReport, FactorType
)

class FactorStore:
    def __init__(self, settings=None, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path("data/factors")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _append_jsonl(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, default=str) + "\n")
        return path

    def append_inputs(self, inputs: List[FactorInputSnapshot]) -> Path:
        p = self.base_dir / "inputs" / "factor_inputs.jsonl"
        for i in inputs:
            self._append_jsonl(p, i.__dict__)
        return p

    def load_inputs(self, symbol: Optional[str] = None, limit: int = 10000) -> List[FactorInputSnapshot]:
        return []

    def append_scores(self, scores: List[FactorScore]) -> Path:
        p = self.base_dir / "scores" / "factor_scores.jsonl"
        for s in scores:
            d = s.__dict__.copy()
            d["factor_type"] = s.factor_type.value
            d["status"] = s.status.value
            d["direction"] = s.direction.value
            self._append_jsonl(p, d)
        return p

    def load_scores(self, symbol: Optional[str] = None, factor_type: Optional[FactorType] = None, limit: int = 10000) -> List[FactorScore]:
        return []

    def append_exposure(self, exposure: FactorExposure) -> Path:
        p = self.base_dir / "exposures" / "factor_exposures.jsonl"
        d = exposure.__dict__.copy()
        d["status"] = exposure.status.value
        d.pop("factor_scores", None)
        return self._append_jsonl(p, d)

    def load_latest_exposure(self, object_type: str, object_id: str) -> Optional[FactorExposure]:
        return None

    def append_sector_rotation(self, scores: List[SectorRotationScore]) -> Path:
        p = self.base_dir / "sector_rotation" / "sector_rotation_scores.jsonl"
        for s in scores:
            d = s.__dict__.copy()
            d["status"] = s.status.value
            self._append_jsonl(p, d)
        return p

    def load_latest_sector_rotation(self) -> List[SectorRotationScore]:
        return []

    def append_theme_definition(self, theme: ThemeDefinition) -> Path:
        p = self.base_dir / "themes" / "theme_definitions.jsonl"
        d = theme.__dict__.copy()
        d["status"] = theme.status.value
        return self._append_jsonl(p, d)

    def load_theme_definitions(self) -> List[ThemeDefinition]:
        return []

    def append_theme_exposures(self, exposures: List[ThemeExposure]) -> Path:
        p = self.base_dir / "themes" / "theme_exposures.jsonl"
        for e in exposures:
            d = e.__dict__.copy()
            d["status"] = e.status.value
            self._append_jsonl(p, d)
        return p

    def append_crowding(self, assessment: FactorCrowdingAssessment) -> Path:
        p = self.base_dir / "crowding" / "factor_crowding.jsonl"
        return self._append_jsonl(p, assessment.__dict__)

    def append_attribution(self, items: List[FactorAttributionItem]) -> Path:
        p = self.base_dir / "attribution" / "factor_attribution.jsonl"
        for i in items:
            d = i.__dict__.copy()
            d["factor_type"] = i.factor_type.value
            d["contribution_type"] = i.contribution_type.value
            self._append_jsonl(p, d)
        return p

    def save_report(self, report: FactorReport, markdown_text: str) -> Dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        md_path = self.base_dir / "reports" / date_str / f"factor_report_{report.report_id}.md"
        json_path = self.base_dir / "reports" / date_str / f"factor_report_{report.report_id}.json"

        md_path.parent.mkdir(parents=True, exist_ok=True)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"report_id": report.report_id}, default=str))

        return {"markdown": md_path, "json": json_path}
