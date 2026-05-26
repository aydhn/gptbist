import json
import logging
from pathlib import Path
from typing import Any, List, Optional, Dict
from datetime import datetime
import pandas as pd

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.portfolio_construction.models import PortfolioConstructionResult, RebalanceSimulation
from bist_signal_bot.portfolio_construction.reporting import (
    construction_result_to_dict, rebalance_to_dict, positions_to_dataframe,
    candidates_to_dataframe, format_portfolio_construction_report_markdown
)
from bist_signal_bot.storage.paths import get_portfolio_construction_dir

logger = logging.getLogger(__name__)

class PortfolioConstructionStore:
    def __init__(self, settings: Settings, base_dir: Optional[Path] = None):
        self.settings = settings
        self.base_dir = base_dir or get_portfolio_construction_dir(settings)

    def _get_result_dir(self, date_str: str, result_id: str) -> Path:
        d = self.base_dir / "results" / date_str / result_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_result(self, result: PortfolioConstructionResult) -> Dict[str, Path]:
        if not self.settings.PORTFOLIO_CONSTRUCTION_SAVE_RESULTS:
            return {}

        date_str = result.generated_at.strftime("%Y%m%d")
        result_dir = self._get_result_dir(date_str, result.result_id)

        output_files = {}

        json_path = result_dir / "portfolio_construction_result.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(construction_result_to_dict(result), f, indent=2, ensure_ascii=False)
        output_files["json"] = json_path

        if result.positions:
            pos_df = positions_to_dataframe(result.positions)
            pos_path = result_dir / "positions.csv"
            pos_df.to_csv(pos_path, index=False)
            output_files["positions"] = pos_path

        if result.candidates:
            cand_df = candidates_to_dataframe(result.candidates)
            cand_path = result_dir / "candidates.csv"
            cand_df.to_csv(cand_path, index=False)
            output_files["candidates"] = cand_path

        md_content = format_portfolio_construction_report_markdown(result)
        md_path = result_dir / "portfolio_construction_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        output_files["markdown"] = md_path

        recent_dir = self.base_dir / "recent"
        recent_dir.mkdir(exist_ok=True)
        latest_json = recent_dir / "latest_result.json"
        with open(latest_json, "w", encoding="utf-8") as f:
            json.dump(construction_result_to_dict(result), f, indent=2, ensure_ascii=False)

        return output_files

    def load_result(self, result_id: str) -> Optional[PortfolioConstructionResult]:
        results_dir = self.base_dir / "results"
        if not results_dir.exists():
            return None

        for date_dir in results_dir.iterdir():
            if date_dir.is_dir():
                target_dir = date_dir / result_id
                if target_dir.exists():
                    json_path = target_dir / "portfolio_construction_result.json"
                    if json_path.exists():
                        with open(json_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            return PortfolioConstructionResult(**data)
        return None

    def load_latest_result(self) -> Optional[PortfolioConstructionResult]:
        latest_json = self.base_dir / "recent" / "latest_result.json"
        if latest_json.exists():
            with open(latest_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                return PortfolioConstructionResult(**data)
        return None

    def list_recent_results(self, limit: int = 20) -> List[Dict[str, Any]]:
        results_dir = self.base_dir / "results"
        if not results_dir.exists():
            return []

        all_results = []
        for date_dir in results_dir.iterdir():
            if date_dir.is_dir():
                for res_dir in date_dir.iterdir():
                    json_path = res_dir / "portfolio_construction_result.json"
                    if json_path.exists():
                        with open(json_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            summary = {
                                "result_id": data.get("result_id"),
                                "generated_at": data.get("generated_at"),
                                "status": data.get("status"),
                                "weighting_method": data.get("weighting_method"),
                                "portfolio_score": data.get("portfolio_score")
                            }
                            all_results.append(summary)

        all_results.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
        return all_results[:limit]

    def append_rebalance(self, simulation: RebalanceSimulation) -> Path:
        rebalance_dir = self.base_dir / "rebalance"
        rebalance_dir.mkdir(exist_ok=True)
        jsonl_path = rebalance_dir / "rebalance_simulations.jsonl"

        with open(jsonl_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rebalance_to_dict(simulation), ensure_ascii=False) + "\n")

        latest_json = self.base_dir / "recent" / "latest_rebalance.json"
        with open(latest_json, "w", encoding="utf-8") as f:
            json.dump(rebalance_to_dict(simulation), f, indent=2, ensure_ascii=False)

        return jsonl_path

    def load_latest_rebalance(self) -> Optional[RebalanceSimulation]:
        latest_json = self.base_dir / "recent" / "latest_rebalance.json"
        if latest_json.exists():
            with open(latest_json, "r", encoding="utf-8") as f:
                data = json.load(f)
                return RebalanceSimulation(**data)
        return None
