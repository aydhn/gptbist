import json
import logging
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.adaptive.models import AdaptiveRecommendation, AdaptivePolicy
from bist_signal_bot.storage.paths import get_adaptive_dir
from bist_signal_bot.core.exceptions import AdaptiveStorageError

class AdaptiveStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None, logger: logging.Logger | None = None):
        self.settings = settings
        self.logger = logger or logging.getLogger(__name__)
        self.base_dir = base_dir or get_adaptive_dir(settings)

        self.recommendations_dir = self.base_dir / "recommendations"
        self.policy_dir = self.base_dir / "policy"

        self.recommendations_dir.mkdir(parents=True, exist_ok=True)
        self.policy_dir.mkdir(parents=True, exist_ok=True)

    def get_adaptive_dir(self) -> Path:
        return self.base_dir

    def create_recommendation_dir(self, result: AdaptiveRecommendation) -> Path:
        date_str = result.generated_at.strftime("%Y%m%d")
        rec_dir = self.recommendations_dir / date_str / result.recommendation_id
        rec_dir.mkdir(parents=True, exist_ok=True)
        return rec_dir

    def save_recommendation(self, result: AdaptiveRecommendation, output_dir: Path | None = None) -> dict[str, Path]:
        try:
            from bist_signal_bot.security.path_guard import PathGuard
            from bist_signal_bot.adaptive.reporting import (
                format_adaptive_report_markdown,
                adaptive_candidates_to_dataframe,
                refresh_plan_to_dataframe,
                model_refresh_to_dataframe
            )

            out_dir = output_dir or self.create_recommendation_dir(result)
            PathGuard([out_dir]).resolve_safe_path(out_dir)

            saved_files = {}

            json_path = out_dir / "adaptive_recommendation.json"
            def json_serial(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError("Type %s not serializable" % type(obj))

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(result.safe_public_dict(), f, indent=2, default=json_serial)
            saved_files["json"] = json_path

            md_path = out_dir / "adaptive_report.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(format_adaptive_report_markdown(result))
            saved_files["markdown"] = md_path

            if result.candidates:
                cand_df = adaptive_candidates_to_dataframe(result.candidates)
                if not cand_df.empty:
                    csv_path = out_dir / "candidates.csv"
                    cand_df.to_csv(csv_path, index=False)
                    saved_files["candidates_csv"] = csv_path

            if result.refresh_plan and result.refresh_plan.items:
                plan_df = refresh_plan_to_dataframe(result.refresh_plan)
                if not plan_df.empty:
                    csv_path = out_dir / "refresh_plan.csv"
                    plan_df.to_csv(csv_path, index=False)
                    saved_files["refresh_plan_csv"] = csv_path

            if result.model_refresh_recommendations:
                model_df = model_refresh_to_dataframe(result.model_refresh_recommendations)
                if not model_df.empty:
                    csv_path = out_dir / "model_refresh.csv"
                    model_df.to_csv(csv_path, index=False)
                    saved_files["model_refresh_csv"] = csv_path

            self.logger.info(f"Saved adaptive recommendation {result.recommendation_id} to {out_dir}")
            return saved_files

        except Exception as e:
            self.logger.error(f"Failed to save adaptive recommendation: {e}")
            raise AdaptiveStorageError(f"Failed to save recommendation: {e}")

    def save_policy(self, policy: AdaptivePolicy, output_dir: Path | None = None) -> Path:
        try:
            from bist_signal_bot.security.path_guard import PathGuard
            out_dir = output_dir or self.policy_dir
            out_dir.mkdir(parents=True, exist_ok=True)

            policy_path = out_dir / "adaptive_policy.json"
            PathGuard([policy_path]).resolve_safe_path(policy_path)

            with open(policy_path, "w", encoding="utf-8") as f:
                json.dump(policy.model_dump(mode='json'), f, indent=2)

            return policy_path
        except Exception as e:
            raise AdaptiveStorageError(f"Failed to save policy: {e}")

    def load_policy(self, path: Path | None = None) -> AdaptivePolicy:
        policy_path = path or (self.policy_dir / "adaptive_policy.json")
        if not policy_path.exists():
            return AdaptivePolicy()
        try:
            with open(policy_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AdaptivePolicy.model_validate(data)
        except Exception as e:
            self.logger.error(f"Failed to load policy from {policy_path}: {e}")
            return AdaptivePolicy()

    def list_recent_recommendations(self, limit: int = 20) -> list[dict[str, Any]]:
        results = []
        try:
            for date_dir in sorted(self.recommendations_dir.iterdir(), reverse=True):
                if not date_dir.is_dir():
                    continue
                for rec_dir in sorted(date_dir.iterdir(), reverse=True):
                    if not rec_dir.is_dir():
                        continue
                    json_file = rec_dir / "adaptive_recommendation.json"
                    if json_file.exists():
                        try:
                            with open(json_file, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                results.append({
                                    "id": data.get("recommendation_id"),
                                    "date": data.get("generated_at"),
                                    "status": data.get("status"),
                                    "candidates": len(data.get("candidates", [])),
                                    "path": str(rec_dir)
                                })
                                if len(results) >= limit:
                                    return results
                        except Exception:
                            pass
            return results
        except Exception as e:
            self.logger.warning(f"Failed to list recent recommendations: {e}")
            return results
