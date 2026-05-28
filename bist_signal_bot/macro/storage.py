import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from bist_signal_bot.macro.models import (
    MacroSeriesPoint, MacroReturn, MacroCorrelation,
    MacroSensitivityAssessment, MacroRegimeSnapshot,
    MacroStressAssessment, IntermarketDivergence,
    MacroImportResult, MacroReport, MacroProxyName
)
from bist_signal_bot.storage.paths import get_macro_dir

class MacroStore:
    def __init__(self, settings=None, base_dir: Optional[Path] = None):
        self.settings = settings
        self.base_dir = base_dir or get_macro_dir(settings)
        self.series_path = self.base_dir / "series" / "macro_series_points.jsonl"
        self.returns_path = self.base_dir / "returns" / "macro_returns.jsonl"
        self.correlations_path = self.base_dir / "correlations" / "macro_correlations.jsonl"
        self.sensitivity_path = self.base_dir / "sensitivity" / "macro_sensitivity_assessments.jsonl"
        self.regime_path = self.base_dir / "regime" / "macro_regime_snapshots.jsonl"
        self.stress_path = self.base_dir / "stress" / "macro_stress_assessments.jsonl"
        self.intermarket_path = self.base_dir / "intermarket" / "intermarket_divergences.jsonl"
        self.imports_dir = self.base_dir / "imports"
        self.reports_dir = self.base_dir / "reports"

        for p in [self.series_path, self.returns_path, self.correlations_path,
                  self.sensitivity_path, self.regime_path, self.stress_path, self.intermarket_path]:
            p.parent.mkdir(parents=True, exist_ok=True)

    def _append_jsonl(self, path: Path, items: List[any]) -> Path:
        with open(path, "a", encoding="utf-8") as f:
            for item in items:
                f.write(item.model_dump_json() + "\n")
        return path

    def _load_jsonl(self, path: Path, model_class, limit: int = 10000, filter_fn=None) -> List[any]:
        if not path.exists():
            return []

        results = []
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if not line.strip(): continue
                try:
                    obj = model_class.model_validate_json(line)
                    if filter_fn is None or filter_fn(obj):
                        results.append(obj)
                        if len(results) >= limit:
                            break
                except Exception:
                    pass
        return results

    def append_points(self, points: List[MacroSeriesPoint]) -> Path:
        return self._append_jsonl(self.series_path, points)

    def load_points(self, proxy_name: Optional[MacroProxyName] = None, limit: int = 10000) -> List[MacroSeriesPoint]:
        filter_fn = (lambda p: p.proxy_name == proxy_name) if proxy_name else None
        return self._load_jsonl(self.series_path, MacroSeriesPoint, limit, filter_fn)

    def append_returns(self, returns: List[MacroReturn]) -> Path:
        return self._append_jsonl(self.returns_path, returns)

    def load_returns(self, proxy_name: Optional[MacroProxyName] = None, limit: int = 10000) -> List[MacroReturn]:
        filter_fn = (lambda r: r.proxy_name == proxy_name) if proxy_name else None
        return self._load_jsonl(self.returns_path, MacroReturn, limit, filter_fn)

    def append_correlations(self, correlations: List[MacroCorrelation]) -> Path:
        return self._append_jsonl(self.correlations_path, correlations)

    def load_correlations(self, symbol: Optional[str] = None, limit: int = 10000) -> List[MacroCorrelation]:
        filter_fn = (lambda c: c.subject_symbol == symbol) if symbol else None
        return self._load_jsonl(self.correlations_path, MacroCorrelation, limit, filter_fn)

    def append_sensitivity(self, assessment: MacroSensitivityAssessment) -> Path:
        return self._append_jsonl(self.sensitivity_path, [assessment])

    def load_latest_sensitivity(self, object_type: str, object_id: str) -> Optional[MacroSensitivityAssessment]:
        def filter_fn(a): return a.object_type == object_type and a.object_id == object_id
        results = self._load_jsonl(self.sensitivity_path, MacroSensitivityAssessment, limit=1, filter_fn=filter_fn)
        return results[0] if results else None

    def append_regime(self, snapshot: MacroRegimeSnapshot) -> Path:
        return self._append_jsonl(self.regime_path, [snapshot])

    def load_latest_regime(self) -> Optional[MacroRegimeSnapshot]:
        results = self._load_jsonl(self.regime_path, MacroRegimeSnapshot, limit=1)
        return results[0] if results else None

    def append_stress(self, assessment: MacroStressAssessment) -> Path:
        return self._append_jsonl(self.stress_path, [assessment])

    def append_divergences(self, divergences: List[IntermarketDivergence]) -> Path:
        return self._append_jsonl(self.intermarket_path, divergences)

    def load_latest_divergences(self, limit: int = 100) -> List[IntermarketDivergence]:
        return self._load_jsonl(self.intermarket_path, IntermarketDivergence, limit)

    def save_import_result(self, result: MacroImportResult) -> Dict[str, Path]:
        date_str = result.created_at.strftime("%Y%m%d")
        import_dir = self.imports_dir / date_str / result.import_id
        import_dir.mkdir(parents=True, exist_ok=True)
        path = import_dir / "macro_import_result.json"
        with open(path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))
        return {"import_result": path}

    def save_report(self, report: MacroReport, markdown_text: str) -> Dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        report_dir = self.reports_dir / date_str
        report_dir.mkdir(parents=True, exist_ok=True)
        md_path = report_dir / f"macro_report_{report.report_id}.md"
        json_path = report_dir / f"macro_report_{report.report_id}.json"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        with open(json_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

        return {"markdown": md_path, "json": json_path}
