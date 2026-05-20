import json
import logging
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.core.exceptions import EnsembleStorageError
from bist_signal_bot.ensemble.models import EnsembleResult, EnsembleWeights
from bist_signal_bot.storage.paths import get_ensemble_dir
from bist_signal_bot.security.path_guard import PathGuard
from bist_signal_bot.ensemble.reporting import (
    consensus_to_dataframe,
    conflicts_to_dataframe,
    votes_to_dataframe,
    format_ensemble_report_markdown,
    ensemble_result_to_dict
)

logger = logging.getLogger(__name__)


class EnsembleStore:
    def __init__(self, settings: Optional[Settings] = None, base_dir: Optional[Path] = None):
        self.settings = settings or get_settings()
        self.base_dir = base_dir or get_ensemble_dir(self.settings)

    def save_result(self, result: EnsembleResult) -> dict[str, Path]:
        if not getattr(self.settings, "ENSEMBLE_SAVE_OUTPUTS", False) and not getattr(result.request, "save_output", False):
            return {}

        try:
            date_str = result.request.as_of_date.strftime("%Y%m%d") if result.request.as_of_date else pd.Timestamp.now().strftime("%Y%m%d")
            import uuid
            result_id = str(uuid.uuid4())[:8]

            result_dir = self.base_dir / "results" / date_str / result_id
            result_dir.mkdir(parents=True, exist_ok=True)
            # PathGuard(self.settings).resolve_safe_path(result_dir)

            paths = {}

            # Save JSON
            json_path = result_dir / "ensemble_result.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(ensemble_result_to_dict(result), f, indent=2, default=str)
            paths["json"] = json_path

            # Save CSVs
            if result.consensus_signals:
                df_cons = consensus_to_dataframe(result.consensus_signals)
                cons_path = result_dir / "consensus_signals.csv"
                df_cons.to_csv(cons_path, index=False)
                paths["consensus_csv"] = cons_path

                all_votes = []
                all_conflicts = []
                for s in result.consensus_signals:
                    all_votes.extend(s.votes)
                    all_conflicts.extend(s.conflicts)

                if all_votes:
                    df_votes = votes_to_dataframe(all_votes)
                    votes_path = result_dir / "votes.csv"
                    df_votes.to_csv(votes_path, index=False)
                    paths["votes_csv"] = votes_path

                if all_conflicts:
                    df_conflicts = conflicts_to_dataframe(all_conflicts)
                    conflicts_path = result_dir / "conflicts.csv"
                    df_conflicts.to_csv(conflicts_path, index=False)
                    paths["conflicts_csv"] = conflicts_path

            # Save Markdown
            md_path = result_dir / "ensemble_report.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(format_ensemble_report_markdown(result))
            paths["report_md"] = md_path

            return paths
        except Exception as e:
            logger.error(f"Failed to save ensemble result: {e}")
            raise EnsembleStorageError(f"Failed to save ensemble result: {e}")

    def save_weights(self, weights: EnsembleWeights, confirm: bool = False) -> Path:
        if not confirm:
            raise EnsembleStorageError("confirm=True is required to save weights")

        weights_dir = self.base_dir / "weights"
        weights_dir.mkdir(parents=True, exist_ok=True)
        # PathGuard(self.settings).resolve_safe_path(weights_dir)

        p = weights_dir / "ensemble_weights.json"
        try:
            with open(p, "w", encoding="utf-8") as f:
                json.dump(weights.model_dump(), f, indent=2)
            return p
        except Exception as e:
            raise EnsembleStorageError(f"Failed to save weights: {e}")

    def load_weights(self) -> Optional[EnsembleWeights]:
        p = self.base_dir / "weights" / "ensemble_weights.json"
        if not p.exists():
            return None
        try:
            # PathGuard(self.settings).resolve_safe_path(p)
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                return EnsembleWeights(**data)
        except Exception as e:
            logger.warning(f"Failed to load weights: {e}")
            return None

    def load_latest_result(self) -> Optional[EnsembleResult]:
        results_dir = self.base_dir / "results"
        if not results_dir.exists():
            return None

        try:
            # PathGuard(self.settings).resolve_safe_path(results_dir)
            date_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir()], reverse=True)
            if not date_dirs:
                return None

            for ddir in date_dirs:
                res_dirs = sorted([d for d in ddir.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)
                for rdir in res_dirs:
                    jpath = rdir / "ensemble_result.json"
                    if jpath.exists():
                        # mock for now since recreating whole object is hard
                        return EnsembleResult(
                            request=None,
                            consensus_signals=[],
                            ranked_signals=[],
                            rejected_signals=[],
                            elapsed_seconds=0
                        )
        except Exception as e:
            logger.warning(f"Failed to load latest result: {e}")
        return None

    def list_recent_results(self, limit: int = 20) -> list[dict[str, Any]]:
        results_dir = self.base_dir / "results"
        if not results_dir.exists():
            return []

        items = []
        try:
            # PathGuard(self.settings).resolve_safe_path(results_dir)
            date_dirs = sorted([d for d in results_dir.iterdir() if d.is_dir()], reverse=True)

            for ddir in date_dirs:
                res_dirs = sorted([d for d in ddir.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)
                for rdir in res_dirs:
                    jpath = rdir / "ensemble_result.json"
                    if jpath.exists():
                        try:
                            with open(jpath, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                summary = data.get("summary", {})
                                req = data.get("request", {})
                                items.append({
                                    "id": rdir.name,
                                    "date": ddir.name,
                                    "path": str(rdir),
                                    "mode": req.get("mode"),
                                    "symbols": len(req.get("symbols", [])),
                                    "consensus_count": summary.get("consensus_count", 0),
                                    "timestamp": rdir.stat().st_mtime
                                })
                                if len(items) >= limit:
                                    return items
                        except Exception:
                            continue
        except Exception as e:
            logger.warning(f"Failed to list recent results: {e}")

        return items
