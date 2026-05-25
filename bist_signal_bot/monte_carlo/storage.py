import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_monte_carlo_dir
from bist_signal_bot.core.exceptions import MonteCarloStorageError
from .models import MonteCarloResult

class MonteCarloStore:
    def __init__(self, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.settings = settings or Settings()
        self.logger = logger or logging.getLogger("bist_signal_bot.monte_carlo.storage")
        self.base_dir = get_monte_carlo_dir(self.settings)

    def save_result(self, result: MonteCarloResult) -> dict[str, Path]:
        try:
            date_str = result.generated_at.strftime("%Y%m%d")
            out_dir = self.base_dir / "results" / date_str / result.monte_carlo_id
            out_dir.mkdir(parents=True, exist_ok=True)

            files = {}

            json_path = out_dir / "monte_carlo_result.json"
            from .reporting import monte_carlo_result_to_dict
            data = monte_carlo_result_to_dict(result)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            files["result_json"] = json_path

            recent_dir = self.base_dir / "recent"
            recent_dir.mkdir(parents=True, exist_ok=True)
            recent_path = recent_dir / f"{result.monte_carlo_id}.json"
            with open(recent_path, "w", encoding="utf-8") as f:
                json.dump(result.summary(), f, indent=2, ensure_ascii=False)

            self._cleanup_recent(recent_dir)

            return files
        except Exception as e:
            self.logger.error(f"Failed to save Monte Carlo result {result.monte_carlo_id}: {e}")
            raise MonteCarloStorageError(f"Failed to save Monte Carlo result: {e}") from e

    def load_result(self, monte_carlo_id: str) -> MonteCarloResult | None:
        results_dir = self.base_dir / "results"
        if not results_dir.exists():
            return None

        matches = list(results_dir.rglob(f"{monte_carlo_id}/monte_carlo_result.json"))
        if not matches:
            return None

        try:
            with open(matches[0], "r", encoding="utf-8") as f:
                data = json.load(f)
            from .models import MonteCarloStatus, MonteCarloRequest, MonteCarloTarget, ResamplingMethod

            req = MonteCarloRequest(
                request_id=data.get("request", {}).get("request_id", "req-1"),
                target=MonteCarloTarget(data.get("request", {}).get("target", "CUSTOM")),
                method=ResamplingMethod(data.get("request", {}).get("method", "CUSTOM")),
                simulations=data.get("request", {}).get("simulations", 10),
                seed=data.get("request", {}).get("seed", 42),
                initial_equity=data.get("request", {}).get("initial_equity", 100000.0),
                ruin_threshold_pct=data.get("request", {}).get("ruin_threshold_pct", 30.0)
            )

            return MonteCarloResult(
                monte_carlo_id=data.get("monte_carlo_id", monte_carlo_id),
                request=req,
                status=MonteCarloStatus(data.get("status", "UNKNOWN")),
                elapsed_seconds=data.get("elapsed_seconds", 0.0),
                paths=[],
                metrics=[],
                distributions=[]
            )
        except Exception as e:
            self.logger.error(f"Failed to load result {monte_carlo_id}: {e}")
            return None

    def load_latest_result(self, strategy_name: str | None = None, symbol: str | None = None) -> MonteCarloResult | None:
        recent = self.list_recent_results(limit=50)
        for r in recent:
            if strategy_name and r.get("strategy_name") != strategy_name:
                continue
            if symbol and r.get("symbol") != symbol:
                continue
            return self.load_result(r.get("monte_carlo_id", ""))
        return None

    def list_recent_results(self, limit: int = 20) -> list[dict[str, Any]]:
        recent_dir = self.base_dir / "recent"
        if not recent_dir.exists():
            return []

        files = sorted(list(recent_dir.glob("*.json")), key=lambda p: p.stat().st_mtime, reverse=True)
        results = []

        for f in files[:limit]:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    results.append(json.load(fp))
            except Exception:
                continue

        return results

    def save_paths(self, result: MonteCarloResult, output_dir: Path) -> Path:
        path = output_dir / "paths.csv"
        path.touch()
        return path

    def save_metrics(self, result: MonteCarloResult, output_dir: Path) -> Path:
        path = output_dir / "metrics.csv"
        path.touch()
        return path

    def save_distributions(self, result: MonteCarloResult, output_dir: Path) -> Path:
        path = output_dir / "distributions.csv"
        path.touch()
        return path

    def _cleanup_recent(self, recent_dir: Path) -> None:
        try:
            files = sorted(list(recent_dir.glob("*.json")), key=lambda p: p.stat().st_mtime, reverse=True)
            for f in files[100:]:
                f.unlink(missing_ok=True)
        except Exception:
            pass
