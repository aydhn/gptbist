import json
import uuid
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.portfolio_research.models import (
    ResearchPortfolioSnapshot,
    RebalancePlan,
    BasketSimulationResult
)
from bist_signal_bot.portfolio_research.reporting import (
    snapshot_to_dict,
    rebalance_plan_to_dict,
    basket_simulation_to_dict,
    items_to_dataframe,
    exposures_to_dataframe,
    constraints_to_dataframe,
    correlations_to_dataframe,
    format_portfolio_report_markdown
)

class PortfolioResearchStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.snapshots_dir = self.base_dir / "snapshots"
        self.rebalance_dir = self.base_dir / "rebalance"
        self.simulations_dir = self.base_dir / "simulations"

        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.rebalance_dir.mkdir(parents=True, exist_ok=True)
        self.simulations_dir.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, snapshot: ResearchPortfolioSnapshot) -> dict[str, Path]:
        date_str = snapshot.created_at.strftime("%Y%m%d")
        snapshot_dir = self.snapshots_dir / date_str / snapshot.snapshot_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON
        json_path = snapshot_dir / "portfolio_snapshot.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(snapshot_to_dict(snapshot), f, indent=2, ensure_ascii=False)

        # Save CSVs
        paths = {"json": json_path}

        df_items = items_to_dataframe(snapshot.items)
        if not df_items.empty:
            p = snapshot_dir / "items.csv"
            df_items.to_csv(p, index=False)
            paths["items_csv"] = p

        df_exp = exposures_to_dataframe(snapshot.exposures)
        if not df_exp.empty:
            p = snapshot_dir / "exposures.csv"
            df_exp.to_csv(p, index=False)
            paths["exposures_csv"] = p

        df_cons = constraints_to_dataframe(snapshot.constraints)
        if not df_cons.empty:
            p = snapshot_dir / "constraints.csv"
            df_cons.to_csv(p, index=False)
            paths["constraints_csv"] = p

        df_corr = correlations_to_dataframe(snapshot.correlations)
        if not df_corr.empty:
            p = snapshot_dir / "correlations.csv"
            df_corr.to_csv(p, index=False)
            paths["correlations_csv"] = p

        md_path = snapshot_dir / "portfolio_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(format_portfolio_report_markdown(snapshot))
        paths["markdown"] = md_path

        return paths

    def load_snapshot(self, snapshot_id: str) -> ResearchPortfolioSnapshot | None:
        for date_dir in sorted(self.snapshots_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            target_dir = date_dir / snapshot_id
            if target_dir.exists():
                json_path = target_dir / "portfolio_snapshot.json"
                if json_path.exists():
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        return ResearchPortfolioSnapshot(**data)
        return None

    def load_latest_snapshot(self) -> ResearchPortfolioSnapshot | None:
        snapshots = self.list_recent_snapshots(limit=1)
        if snapshots:
            return self.load_snapshot(snapshots[0]["snapshot_id"])
        return None

    def list_recent_snapshots(self, limit: int = 20) -> list[dict[str, Any]]:
        results = []
        for date_dir in sorted(self.snapshots_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            for snap_dir in sorted(date_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                if not snap_dir.is_dir():
                    continue
                json_path = snap_dir / "portfolio_snapshot.json"
                if json_path.exists():
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        results.append({
                            "snapshot_id": data.get("snapshot_id"),
                            "created_at": data.get("created_at"),
                            "total_weight": data.get("total_weight"),
                            "item_count": data.get("item_count")
                        })
                        if len(results) >= limit:
                            return results
        return results

    def save_rebalance_plan(self, plan: RebalancePlan) -> dict[str, Path]:
        date_str = plan.created_at.strftime("%Y%m%d")
        plan_dir = self.rebalance_dir / date_str / plan.plan_id
        plan_dir.mkdir(parents=True, exist_ok=True)

        json_path = plan_dir / "rebalance_plan.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(rebalance_plan_to_dict(plan), f, indent=2, ensure_ascii=False)

        return {"json": json_path}

    def load_rebalance_plan(self, plan_id: str) -> RebalancePlan | None:
        for date_dir in sorted(self.rebalance_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            target_dir = date_dir / plan_id
            if target_dir.exists():
                json_path = target_dir / "rebalance_plan.json"
                if json_path.exists():
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        return RebalancePlan(**data)
        return None

    def save_simulation(self, result: BasketSimulationResult) -> dict[str, Path]:
        date_str = result.created_at.strftime("%Y%m%d")
        sim_dir = self.simulations_dir / date_str / result.simulation_id
        sim_dir.mkdir(parents=True, exist_ok=True)

        json_path = sim_dir / "basket_simulation.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(basket_simulation_to_dict(result), f, indent=2, ensure_ascii=False)

        return {"json": json_path}

    def list_recent_simulations(self, limit: int = 20) -> list[dict[str, Any]]:
        results = []
        for date_dir in sorted(self.simulations_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            for sim_dir in sorted(date_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                if not sim_dir.is_dir():
                    continue
                json_path = sim_dir / "basket_simulation.json"
                if json_path.exists():
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        results.append({
                            "simulation_id": data.get("simulation_id"),
                            "created_at": data.get("created_at"),
                            "simulated_return_pct": data.get("simulated_return_pct")
                        })
                        if len(results) >= limit:
                            return results
        return results
