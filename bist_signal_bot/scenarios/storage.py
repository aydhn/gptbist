import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.scenarios.models import ScenarioResult
from bist_signal_bot.storage.paths import (
    get_scenarios_dir,
    get_scenario_runs_dir,
    get_scenario_golden_dir,
)


class ScenarioStore:
    def __init__(self, settings: Optional[Settings] = None, base_dir: Optional[Path] = None):
        self.settings = settings or Settings()
        self.base_dir = base_dir  # Can override for tests

    def get_scenarios_dir(self) -> Path:
        if self.base_dir:
            p = self.base_dir / "scenarios"
            p.mkdir(parents=True, exist_ok=True)
            return p
        return get_scenarios_dir(self.settings)

    def get_scenario_runs_dir(self) -> Path:
        if self.base_dir:
            p = self.base_dir / "scenarios" / "runs"
            p.mkdir(parents=True, exist_ok=True)
            return p
        return get_scenario_runs_dir(self.settings)

    def get_golden_dir(self) -> Path:
        if self.base_dir:
            p = self.base_dir / "scenarios" / "golden"
            p.mkdir(parents=True, exist_ok=True)
            return p
        return get_scenario_golden_dir(self.settings)

    def create_run_dir(self, result_or_run_id: Any) -> Path:
        run_id = result_or_run_id if isinstance(result_or_run_id, str) else result_or_run_id.run_id
        date_str = datetime.utcnow().strftime("%Y%m%d")
        p = self.get_scenario_runs_dir() / date_str / run_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    def save_result(
        self, result: ScenarioResult, output_dir: Optional[Path] = None
    ) -> Dict[str, Path]:
        from bist_signal_bot.scenarios.reporting import (
            format_scenario_markdown,
        )

        dir_path = output_dir or self.create_run_dir(result)

        json_path = dir_path / "scenario_result.json"
        with open(json_path, "w") as f:
            json.dump(result.model_dump(mode="json"), f, indent=2)

        md_path = dir_path / "scenario_report.md"
        with open(md_path, "w") as f:
            f.write(format_scenario_markdown(result))

        csv_path = self.save_steps_csv(result, dir_path)

        result.output_files = {
            "json": str(json_path),
            "markdown": str(md_path),
            "csv": str(csv_path),
        }

        return {"json": json_path, "markdown": md_path, "csv": csv_path}

    def load_result(self, run_id: str) -> Optional[ScenarioResult]:
        runs_dir = self.get_scenario_runs_dir()
        for date_dir in runs_dir.iterdir():
            if date_dir.is_dir():
                target = date_dir / run_id / "scenario_result.json"
                if target.exists():
                    try:
                        with open(target, "r") as f:
                            return ScenarioResult(**json.load(f))
                    except Exception:
                        pass
        return None

    def list_recent_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        runs_dir = self.get_scenario_runs_dir()
        runs = []
        if not runs_dir.exists():
            return runs

        for date_dir in sorted(runs_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            for run_dir in date_dir.iterdir():
                if not run_dir.is_dir():
                    continue
                json_path = run_dir / "scenario_result.json"
                if json_path.exists():
                    try:
                        with open(json_path, "r") as f:
                            data = json.load(f)
                            runs.append(
                                {
                                    "run_id": data.get("run_id"),
                                    "scenario_id": data.get("scenario", {}).get("scenario_id"),
                                    "status": data.get("status"),
                                    "elapsed_seconds": data.get("elapsed_seconds", 0),
                                    "started_at": data.get("started_at"),
                                }
                            )
                    except Exception:
                        pass

        runs.sort(key=lambda x: x["started_at"] or "", reverse=True)
        return runs[:limit]

    def save_steps_csv(self, result: ScenarioResult, output_dir: Path) -> Path:
        from bist_signal_bot.scenarios.reporting import scenario_step_results_to_dataframe

        df = scenario_step_results_to_dataframe(result.step_results)
        csv_path = output_dir / "steps.csv"
        df.to_csv(csv_path, index=False)
        return csv_path
