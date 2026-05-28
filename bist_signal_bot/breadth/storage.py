import json
from pathlib import Path
from datetime import datetime
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_breadth_dir
from bist_signal_bot.breadth.models import (
    AdvanceDeclineSummary, BreadthDivergence, BreadthInputRow, BreadthMetric, BreadthRegimeSnapshot,
    BreadthReport, BreadthUniverseSnapshot, HighLowBreadthSummary, ParticipationSummary,
    SectorBreadthSummary, VolumeBreadthSummary
)
from bist_signal_bot.breadth.reporting import (
    universe_to_dict, input_row_to_dict, metric_to_dict, advance_decline_to_dict,
    participation_to_dict, high_low_to_dict, volume_breadth_to_dict, sector_breadth_to_dict,
    divergence_to_dict, regime_to_dict, breadth_report_to_dict
)

class BreadthStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or Settings()
        self.base_dir = base_dir or get_breadth_dir(self.settings)

        self.universe_dir = self.base_dir / "universe"
        self.inputs_dir = self.base_dir / "inputs"
        self.metrics_dir = self.base_dir / "metrics"
        self.ad_dir = self.base_dir / "advance_decline"
        self.part_dir = self.base_dir / "participation"
        self.hl_dir = self.base_dir / "high_low"
        self.vol_dir = self.base_dir / "volume"
        self.sec_dir = self.base_dir / "sector"
        self.div_dir = self.base_dir / "divergence"
        self.regime_dir = self.base_dir / "regime"
        self.reports_dir = self.base_dir / "reports"

        for d in [self.universe_dir, self.inputs_dir, self.metrics_dir, self.ad_dir,
                 self.part_dir, self.hl_dir, self.vol_dir, self.sec_dir, self.div_dir,
                 self.regime_dir, self.reports_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _append_jsonl(self, file_path: Path, data: dict[str, Any]) -> Path:
        with file_path.open('a', encoding='utf-8') as f:
            f.write(json.dumps(data, default=str) + "\n")
        return file_path

    def _append_many_jsonl(self, file_path: Path, data_list: list[dict[str, Any]]) -> Path:
        with file_path.open('a', encoding='utf-8') as f:
            for item in data_list:
                f.write(json.dumps(item, default=str) + "\n")
        return file_path

    def append_universe(self, snapshot: BreadthUniverseSnapshot) -> Path:
        file_path = self.universe_dir / "breadth_universe_snapshots.jsonl"
        return self._append_jsonl(file_path, universe_to_dict(snapshot))

    def append_inputs(self, inputs: list[BreadthInputRow]) -> Path:
        file_path = self.inputs_dir / "breadth_inputs.jsonl"
        dicts = [input_row_to_dict(r) for r in inputs]
        return self._append_many_jsonl(file_path, dicts)

    def append_metrics(self, metrics: list[BreadthMetric]) -> Path:
        file_path = self.metrics_dir / "breadth_metrics.jsonl"
        dicts = [metric_to_dict(m) for m in metrics]
        return self._append_many_jsonl(file_path, dicts)

    def append_advance_decline(self, summary: AdvanceDeclineSummary) -> Path:
        file_path = self.ad_dir / "advance_decline_summaries.jsonl"
        return self._append_jsonl(file_path, advance_decline_to_dict(summary))

    def append_participation(self, summary: ParticipationSummary) -> Path:
        file_path = self.part_dir / "participation_summaries.jsonl"
        return self._append_jsonl(file_path, participation_to_dict(summary))

    def append_high_low(self, summary: HighLowBreadthSummary) -> Path:
        file_path = self.hl_dir / "high_low_summaries.jsonl"
        return self._append_jsonl(file_path, high_low_to_dict(summary))

    def append_volume_breadth(self, summary: VolumeBreadthSummary) -> Path:
        file_path = self.vol_dir / "volume_breadth_summaries.jsonl"
        return self._append_jsonl(file_path, volume_breadth_to_dict(summary))

    def append_sector_breadth(self, summaries: list[SectorBreadthSummary]) -> Path:
        file_path = self.sec_dir / "sector_breadth_summaries.jsonl"
        dicts = [sector_breadth_to_dict(s) for s in summaries]
        return self._append_many_jsonl(file_path, dicts)

    def append_divergences(self, divergences: list[BreadthDivergence]) -> Path:
        file_path = self.div_dir / "breadth_divergences.jsonl"
        dicts = [divergence_to_dict(d) for d in divergences]
        return self._append_many_jsonl(file_path, dicts)

    def append_regime(self, snapshot: BreadthRegimeSnapshot) -> Path:
        file_path = self.regime_dir / "breadth_regime_snapshots.jsonl"
        return self._append_jsonl(file_path, regime_to_dict(snapshot))

    def save_report(self, report: BreadthReport, markdown_text: str) -> dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        daily_dir = self.reports_dir / date_str
        daily_dir.mkdir(exist_ok=True)

        md_path = daily_dir / "breadth_report.md"
        json_path = daily_dir / "breadth_report.json"

        with md_path.open('w', encoding='utf-8') as f:
            f.write(markdown_text)

        with json_path.open('w', encoding='utf-8') as f:
            json.dump(breadth_report_to_dict(report), f, default=str, indent=2)

        return {"markdown": md_path, "json": json_path}

    def load_latest_regime(self, scope_name: str | None = None) -> BreadthRegimeSnapshot | None:
        # Simplistic implementation
        return None

    def load_latest_report(self) -> BreadthReport | None:
        # Simplistic implementation
        return None
