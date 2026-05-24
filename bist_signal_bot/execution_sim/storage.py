import json
from pathlib import Path
from typing import Any
from datetime import datetime

from bist_signal_bot.execution_sim.models import SimulatedFill, LiquiditySnapshot, ExecutionQualityReport
from bist_signal_bot.storage.paths import get_data_dir

def get_execution_sim_dir(settings: Any | None = None) -> Path:
    base = get_data_dir(settings)
    path = base / getattr(settings, "EXECUTION_SIM_DIR_NAME", "execution_sim")
    path.mkdir(parents=True, exist_ok=True)
    return path

class ExecutionSimStore:
    def __init__(self, settings: Any | None = None, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir or get_execution_sim_dir(settings)

        self.fills_dir = self.base_dir / "fills"
        self.quality_dir = self.base_dir / "quality"
        self.liquidity_dir = self.base_dir / "liquidity"
        self.scenarios_dir = self.base_dir / "scenarios"
        self.reports_dir = self.base_dir / "reports"

        for d in [self.fills_dir, self.quality_dir, self.liquidity_dir, self.scenarios_dir, self.reports_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def append_fill(self, fill: SimulatedFill) -> Path:
        p = self.fills_dir / "simulated_fills.jsonl"
        with open(p, "a", encoding="utf-8") as f:
            f.write(fill.model_dump_json() + "\n")
        return p

    def load_fills(self, symbol: str | None = None, limit: int = 1000) -> list[SimulatedFill]:
        p = self.fills_dir / "simulated_fills.jsonl"
        if not p.exists(): return []
        fills = []
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if symbol and data.get("symbol") != symbol:
                        continue
                    fills.append(SimulatedFill.model_validate(data))
                except Exception:
                    pass
        return fills[-limit:]

    def append_liquidity_snapshot(self, snapshot: LiquiditySnapshot) -> Path:
        p = self.liquidity_dir / "liquidity_snapshots.jsonl"
        with open(p, "a", encoding="utf-8") as f:
            f.write(snapshot.model_dump_json() + "\n")
        return p

    def load_liquidity_snapshots(self, symbol: str | None = None, limit: int = 1000) -> list[LiquiditySnapshot]:
        p = self.liquidity_dir / "liquidity_snapshots.jsonl"
        if not p.exists(): return []
        snaps = []
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if symbol and data.get("symbol") != symbol:
                        continue
                    snaps.append(LiquiditySnapshot.model_validate(data))
                except Exception:
                    pass
        return snaps[-limit:]

    def append_quality_report(self, report: ExecutionQualityReport) -> Path:
        p = self.quality_dir / "execution_quality_reports.jsonl"
        with open(p, "a", encoding="utf-8") as f:
            f.write(report.model_dump_json() + "\n")
        return p

    def load_latest_quality_report(self, symbol: str | None = None) -> ExecutionQualityReport | None:
        p = self.quality_dir / "execution_quality_reports.jsonl"
        if not p.exists(): return None
        reports = []
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if symbol and data.get("symbol") != symbol:
                        continue
                    reports.append(ExecutionQualityReport.model_validate(data))
                except Exception:
                    pass
        return reports[-1] if reports else None

    def save_scenario_result(self, result: dict[str, Any]) -> dict[str, Path]:
        date_str = datetime.now().strftime("%Y%m%d")
        scen_id = result.get("scenario_id", "default")
        d = self.scenarios_dir / date_str / scen_id
        d.mkdir(parents=True, exist_ok=True)
        p = d / "scenario_result.json"
        with open(p, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        return {"result": p}
