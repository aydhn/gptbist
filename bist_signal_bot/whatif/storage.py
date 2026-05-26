import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_whatif_dir
from bist_signal_bot.whatif.models import WhatIfRunResult, SensitivityFinding

class WhatIfStore:
    def __init__(self, settings: Settings, base_dir: Path | None = None):
        self.settings = settings
        if base_dir:
            self.base_dir = base_dir
        else:
            self.base_dir = get_whatif_dir(settings)

        self.runs_dir = self.base_dir / "runs"
        self.recent_dir = self.base_dir / "recent"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.recent_dir.mkdir(parents=True, exist_ok=True)

    def save_run(self, result: WhatIfRunResult) -> dict[str, Path]:
        date_str = result.generated_at.strftime("%Y%m%d")
        run_dir = self.runs_dir / date_str / result.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        paths = {}

        # Main result
        main_path = run_dir / "whatif_run_result.json"
        with open(main_path, "w", encoding="utf-8") as f:
            json.dump(result.safe_public_dict(), f, indent=2, default=str)
        paths["run_result"] = main_path

        # Scenarios
        sc_path = self.save_scenario_results(result, run_dir)
        paths["scenario_results"] = sc_path

        # Comparison
        if result.comparison:
            comp_path = run_dir / "comparison.json"
            with open(comp_path, "w", encoding="utf-8") as f:
                json.dump(result.comparison.model_dump(), f, indent=2, default=str)
            paths["comparison"] = comp_path

            # Sensitivity
            if result.comparison.sensitivity_findings:
                sens_path = self.save_sensitivity_findings(result.comparison.sensitivity_findings, run_dir)
                paths["sensitivity_findings"] = sens_path

        # Update recent symlink
        recent_link = self.recent_dir / "latest.json"
        if recent_link.exists() or recent_link.is_symlink():
            try:
                recent_link.unlink()
            except OSError:
                pass
        try:
            shutil.copy2(main_path, recent_link)
        except OSError:
            pass

        return paths

    def save_scenario_results(self, result: WhatIfRunResult, output_dir: Path) -> Path:
        sc_path = output_dir / "scenario_results.json"
        data = [r.model_dump() for r in result.scenario_results]
        with open(sc_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return sc_path

    def save_sensitivity_findings(self, findings: list[SensitivityFinding], output_dir: Path) -> Path:
        csv_path = output_dir / "sensitivity_findings.csv"
        if not findings:
            return csv_path

        import csv
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["finding_id", "assumption_type", "metric_name", "baseline_value", "scenario_value", "delta_abs", "delta_pct", "direction", "severity", "message"])
            for fn in findings:
                writer.writerow([
                    fn.finding_id,
                    fn.assumption_type.value,
                    fn.metric_name,
                    fn.baseline_value,
                    fn.scenario_value,
                    fn.delta_abs,
                    fn.delta_pct,
                    fn.direction.value,
                    fn.severity,
                    fn.message
                ])
        return csv_path

    def save_report(self, result: WhatIfRunResult, markdown_text: str) -> Path:
        date_str = result.generated_at.strftime("%Y%m%d")
        run_dir = self.runs_dir / date_str / result.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        report_path = run_dir / "whatif_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
        return report_path

    def load_run(self, run_id: str) -> WhatIfRunResult | None:
        # A simple search through date directories to find the run_id
        if not self.runs_dir.exists():
            return None
        for date_dir in self.runs_dir.iterdir():
            if not date_dir.is_dir():
                continue
            run_dir = date_dir / run_id
            if run_dir.exists():
                main_path = run_dir / "whatif_run_result.json"
                if main_path.exists():
                    try:
                        with open(main_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            return WhatIfRunResult(**data)
                    except Exception:
                        return None
        return None

    def load_latest_run(self) -> WhatIfRunResult | None:
        recent_link = self.recent_dir / "latest.json"
        if not recent_link.exists():
            return None
        try:
            with open(recent_link, "r", encoding="utf-8") as f:
                data = json.load(f)
                return WhatIfRunResult(**data)
        except Exception:
            return None

    def list_recent_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        runs = []
        if not self.runs_dir.exists():
            return runs

        # Gather all run JSON paths
        paths = []
        for date_dir in self.runs_dir.iterdir():
            if not date_dir.is_dir():
                continue
            for run_dir in date_dir.iterdir():
                if not run_dir.is_dir():
                    continue
                main_path = run_dir / "whatif_run_result.json"
                if main_path.exists():
                    paths.append(main_path)

        # Sort by modification time descending
        paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        for p in paths[:limit]:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    runs.append({
                        "run_id": data.get("run_id"),
                        "generated_at": data.get("generated_at"),
                        "status": data.get("status"),
                        "source_type": data.get("request", {}).get("source_type")
                    })
            except Exception:
                continue
        return runs
