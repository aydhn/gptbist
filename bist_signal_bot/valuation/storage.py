import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_valuation_dir
from bist_signal_bot.valuation.models import (
    ValuationMarketInput, ValuationMultiple, ValuationBand,
    PeerValuationComparison, ValuationRiskAssessment, ValuationReport, ValuationMetricType
)

class ValuationStore:
    def __init__(self, settings: Optional[Settings] = None, base_dir: Optional[Path] = None):
        self.settings = settings or Settings()
        self.base_dir = base_dir or get_valuation_dir(self.settings)

        self.market_inputs_dir = self.base_dir / "market_inputs"
        self.multiples_dir = self.base_dir / "multiples"
        self.bands_dir = self.base_dir / "bands"
        self.peers_dir = self.base_dir / "peers"
        self.risk_dir = self.base_dir / "risk"
        self.reports_dir = self.base_dir / "reports"

        for d in [self.market_inputs_dir, self.multiples_dir, self.bands_dir, self.peers_dir, self.risk_dir, self.reports_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _append_jsonl(self, file_path: Path, item: dict):
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(item, default=str) + "\n")

    def _load_jsonl(self, file_path: Path, limit: int = 10000) -> List[dict]:
        if not file_path.exists():
            return []
        items = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))
        # returning last N elements
        return items[-limit:] if limit else items

    def append_market_input(self, input: ValuationMarketInput) -> Path:
        p = self.market_inputs_dir / "valuation_market_inputs.jsonl"
        self._append_jsonl(p, input.model_dump(mode="json"))
        return p

    def load_market_inputs(self, symbol: Optional[str] = None, limit: int = 10000) -> List[ValuationMarketInput]:
        p = self.market_inputs_dir / "valuation_market_inputs.jsonl"
        raw = self._load_jsonl(p, limit)
        if symbol:
            raw = [r for r in raw if r["symbol"] == symbol.upper()]
        return [ValuationMarketInput(**r) for r in raw]

    def append_multiples(self, multiples: List[ValuationMultiple]) -> Path:
        p = self.multiples_dir / "valuation_multiples.jsonl"
        for m in multiples:
            self._append_jsonl(p, m.model_dump(mode="json"))
        return p

    def load_multiples(self, symbol: Optional[str] = None, metric_type: Optional[ValuationMetricType] = None, limit: int = 10000) -> List[ValuationMultiple]:
        p = self.multiples_dir / "valuation_multiples.jsonl"
        raw = self._load_jsonl(p, limit)
        if symbol:
            raw = [r for r in raw if r["symbol"] == symbol.upper()]
        if metric_type:
            raw = [r for r in raw if r["metric_type"] == metric_type.value]
        return [ValuationMultiple(**r) for r in raw]

    def append_bands(self, bands: List[ValuationBand]) -> Path:
        p = self.bands_dir / "valuation_bands.jsonl"
        for b in bands:
            self._append_jsonl(p, b.model_dump(mode="json"))
        return p

    def load_bands(self, symbol: Optional[str] = None, limit: int = 10000) -> List[ValuationBand]:
        p = self.bands_dir / "valuation_bands.jsonl"
        raw = self._load_jsonl(p, limit)
        if symbol:
            raw = [r for r in raw if r["symbol"] == symbol.upper()]
        return [ValuationBand(**r) for r in raw]

    def append_peer_comparisons(self, comparisons: List[PeerValuationComparison]) -> Path:
        p = self.peers_dir / "peer_valuation_comparisons.jsonl"
        for c in comparisons:
            self._append_jsonl(p, c.model_dump(mode="json"))
        return p

    def append_risk_assessment(self, assessment: ValuationRiskAssessment) -> Path:
        p = self.risk_dir / "valuation_risk_assessments.jsonl"
        self._append_jsonl(p, assessment.model_dump(mode="json"))
        return p

    def load_latest_risk(self, symbol: str) -> Optional[ValuationRiskAssessment]:
        p = self.risk_dir / "valuation_risk_assessments.jsonl"
        raw = self._load_jsonl(p, 10000) # Load a chunk
        raw = [r for r in raw if r["symbol"] == symbol.upper()]
        if not raw:
            return None
        # Sort by as_of date desc and take the first
        raw.sort(key=lambda x: x["as_of"])
        return ValuationRiskAssessment(**raw[-1])

    def save_report(self, report: ValuationReport, markdown_text: str) -> Dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        daily_dir = self.reports_dir / date_str
        daily_dir.mkdir(exist_ok=True)

        prefix = f"{report.symbol}_" if report.symbol else ""

        md_path = daily_dir / f"{prefix}valuation_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        json_path = daily_dir / f"{prefix}valuation_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(report.model_dump(mode="json"), default=str, indent=2))

        return {"markdown": md_path, "json": json_path}
