import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import ensure_dir
from bist_signal_bot.optimization.models import OptimizationResult, WalkForwardOptimizationResult
from bist_signal_bot.optimization.reporting import (
    optimization_result_to_dict, walk_forward_optimization_to_dict,
    trials_to_dataframe, top_trials_to_dataframe,
    format_optimization_markdown, format_walk_forward_optimization_markdown
)
from bist_signal_bot.core.exceptions import OptimizationStorageError

def get_optimization_dir(settings: Settings | None = None) -> Path:
    s = settings or Settings()
    from bist_signal_bot.storage.paths import get_data_dir
    return ensure_dir(get_data_dir(s) / getattr(s, "OPTIMIZATION_RESULTS_DIR_NAME", "optimization"))

class OptimizationResultStore:
    def __init__(self, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger("bist_signal_bot.optimization.storage")

    def get_optimization_dir(self) -> Path:
        return get_optimization_dir(self.settings)

    def create_output_dir(self, result: OptimizationResult | WalkForwardOptimizationResult) -> Path:
        base_dir = self.get_optimization_dir()
        date_str = result.started_at.strftime("%Y%m%d")

        # Build unique ID
        import uuid
        opt_id = str(uuid.uuid4())[:8]

        dir_name = f"{result.strategy_name}_{result.symbol}_{date_str}_{opt_id}"
        out_dir = base_dir / date_str / dir_name
        ensure_dir(out_dir)
        return out_dir

    def save_json(self, result: OptimizationResult | WalkForwardOptimizationResult, output_dir: Path | None = None) -> Path:
        if output_dir is None:
            output_dir = self.create_output_dir(result)

        file_path = output_dir / "optimization_result.json"

        if isinstance(result, OptimizationResult):
            data = optimization_result_to_dict(result)
        else:
            data = walk_forward_optimization_to_dict(result)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            raise OptimizationStorageError(f"Failed to save JSON result: {e}")

        return file_path

    def save_trials_csv(self, result: OptimizationResult, output_dir: Path | None = None) -> Path:
        if output_dir is None:
            output_dir = self.create_output_dir(result)

        file_path = output_dir / "trials.csv"
        df = trials_to_dataframe(result.trials)

        try:
            df.to_csv(file_path, index=False)
        except Exception as e:
            raise OptimizationStorageError(f"Failed to save trials CSV: {e}")

        return file_path

    def save_top_trials_csv(self, result: OptimizationResult, output_dir: Path | None = None) -> Path:
        if output_dir is None:
            output_dir = self.create_output_dir(result)

        file_path = output_dir / "top_trials.csv"
        df = top_trials_to_dataframe(result)

        try:
            df.to_csv(file_path, index=False)
        except Exception as e:
            raise OptimizationStorageError(f"Failed to save top trials CSV: {e}")

        return file_path

    def save_walk_forward_csv(self, result: WalkForwardOptimizationResult, output_dir: Path | None = None) -> dict[str, Path]:
        if output_dir is None:
            output_dir = self.create_output_dir(result)

        paths = {}

        try:
            # Splits CSV
            splits_data = []
            for sr in result.split_results:
                 splits_data.append({
                     "split_id": sr.split_id,
                     "train_start": sr.train_start.isoformat(),
                     "train_end": sr.train_end.isoformat(),
                     "test_start": sr.test_start.isoformat(),
                     "test_end": sr.test_end.isoformat(),
                     "train_best_score": sr.train_best_trial.objective_score if sr.train_best_trial else None,
                     "test_score": sr.test_trial.objective_score if sr.test_trial else None
                 })
            if splits_data:
                 import pandas as pd
                 df = pd.DataFrame(splits_data)
                 splits_path = output_dir / "wf_splits.csv"
                 df.to_csv(splits_path, index=False)
                 paths["splits"] = splits_path
        except Exception as e:
             self.logger.error(f"Failed to save WF splits CSV: {e}")

        return paths

    def save_markdown(self, result: OptimizationResult | WalkForwardOptimizationResult, output_dir: Path | None = None) -> Path:
        if output_dir is None:
            output_dir = self.create_output_dir(result)

        file_path = output_dir / "optimization_report.md"

        if isinstance(result, OptimizationResult):
            md_content = format_optimization_markdown(result)
        else:
            md_content = format_walk_forward_optimization_markdown(result)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(md_content)
        except Exception as e:
            raise OptimizationStorageError(f"Failed to save Markdown report: {e}")

        return file_path

    def save_result(self, result: OptimizationResult | WalkForwardOptimizationResult, formats: list[str] | None = None, output_dir: Path | None = None) -> dict[str, Path]:
        if not formats:
            raw_formats = getattr(self.settings, "OPTIMIZATION_REPORT_FORMATS", "json,csv,markdown")
            formats = [f.strip().lower() for f in raw_formats.split(",")]

        if output_dir is None:
            output_dir = self.create_output_dir(result)

        saved_paths = {}

        if "json" in formats or "all" in formats:
            saved_paths["json"] = self.save_json(result, output_dir)

        if "markdown" in formats or "all" in formats:
            saved_paths["markdown"] = self.save_markdown(result, output_dir)

        if "csv" in formats or "all" in formats:
            if isinstance(result, OptimizationResult):
                 saved_paths["trials_csv"] = self.save_trials_csv(result, output_dir)
                 saved_paths["top_trials_csv"] = self.save_top_trials_csv(result, output_dir)
            elif isinstance(result, WalkForwardOptimizationResult):
                 wf_paths = self.save_walk_forward_csv(result, output_dir)
                 saved_paths.update(wf_paths)

        return saved_paths

    def list_recent_optimizations(self, limit: int = 20) -> list[dict[str, Any]]:
        base_dir = self.get_optimization_dir()
        if not base_dir.exists():
             return []

        recent = []

        # Date dirs
        for date_dir in sorted([d for d in base_dir.iterdir() if d.is_dir()], reverse=True):
             # Run dirs
             for run_dir in sorted([d for d in date_dir.iterdir() if d.is_dir()], reverse=True):
                 json_path = run_dir / "optimization_result.json"
                 if json_path.exists():
                     try:
                         with open(json_path, "r", encoding="utf-8") as f:
                             data = json.load(f)
                             summary = data.get("summary", {})
                             recent.append({
                                 "dir": str(run_dir.name),
                                 "date": date_dir.name,
                                 "strategy": summary.get("strategy"),
                                 "symbol": summary.get("symbol"),
                                 "method": summary.get("method"),
                                 "status": summary.get("status"),
                                 "best_score": summary.get("best_score"),
                                 "started_at": summary.get("started_at")
                             })
                     except Exception as e:
                         self.logger.warning(f"Could not read {json_path}: {e}")

                 if len(recent) >= limit:
                     return recent

        return recent
