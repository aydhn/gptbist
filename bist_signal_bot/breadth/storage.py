import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from bist_signal_bot.breadth.models import (
    BreadthSnapshot, RelativeStrengthScore, SectorRotationScore, CrossSectionalRankItem, BreadthAnalysisResult
)
from bist_signal_bot.core.exceptions import BreadthStorageError
from bist_signal_bot.storage.paths import get_data_dir

class BreadthStore:
    def __init__(self, base_dir: Path | None = None, settings=None):
        self.settings = settings
        if base_dir:
            self.base_dir = base_dir
        else:
            data_dir = get_data_dir() if hasattr(settings, "get_data_dir") else Path("data")
            self.base_dir = data_dir / "breadth"

    def _get_daily_dir(self, sub_dir: str, as_of_date: datetime) -> Path:
        date_str = as_of_date.strftime("%Y%m%d")
        dir_path = self.base_dir / sub_dir / date_str
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def save_result(self, result: BreadthAnalysisResult) -> dict[str, Path]:
        paths = {}
        try:
            paths["snapshot"] = self.save_snapshot(result.snapshot)
            if result.relative_strength_scores:
                paths["relative_strength"] = self.save_relative_strength(result.relative_strength_scores, result.snapshot.as_of_date)
            if result.sector_rotation_scores:
                paths["sector_rotation"] = self.save_sector_rotation(result.sector_rotation_scores, result.snapshot.as_of_date)
            if result.cross_sectional_ranking:
                paths["ranking"] = self.save_ranking(result.cross_sectional_ranking, result.snapshot.as_of_date)
        except Exception as e:
            raise BreadthStorageError(f"Failed to save breadth result: {str(e)}")
        return paths

    def save_snapshot(self, snapshot: BreadthSnapshot) -> Path:
        dir_path = self._get_daily_dir("snapshots", snapshot.as_of_date)
        file_path = dir_path / "breadth_snapshot.json"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(snapshot.model_dump(mode='json'), f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise BreadthStorageError(f"Failed to save breadth snapshot: {str(e)}")
        return file_path

    def save_relative_strength(self, scores: list[RelativeStrengthScore], as_of_date: datetime) -> Path:
        dir_path = self._get_daily_dir("relative_strength", as_of_date)
        file_path = dir_path / "relative_strength.csv"

        try:
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["symbol", "benchmark_symbol", "sector", "rs_20", "rs_50", "rs_100", "rs_200", "absolute_momentum_score", "percentile_rank", "composite_score"])
                writer.writeheader()
                for s in scores:
                    d = s.model_dump(mode='json')
                    writer.writerow({k: d.get(k) for k in writer.fieldnames})
        except Exception as e:
            raise BreadthStorageError(f"Failed to save relative strength: {str(e)}")
        return file_path

    def save_sector_rotation(self, scores: list[SectorRotationScore], as_of_date: datetime) -> Path:
        dir_path = self._get_daily_dir("sector_rotation", as_of_date)
        file_path = dir_path / "sector_rotation.csv"

        try:
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["sector", "symbol_count", "average_return_20", "average_return_50", "average_rs_score", "breadth_score", "momentum_score", "rotation_status", "rank"])
                writer.writeheader()
                for s in scores:
                    d = s.model_dump(mode='json')
                    writer.writerow({k: d.get(k) for k in writer.fieldnames})
        except Exception as e:
            raise BreadthStorageError(f"Failed to save sector rotation: {str(e)}")
        return file_path

    def save_ranking(self, items: list[CrossSectionalRankItem], as_of_date: datetime) -> Path:
        dir_path = self._get_daily_dir("ranking", as_of_date)
        file_path = dir_path / "cross_sectional_ranking.csv"

        try:
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["symbol", "rank", "percentile", "composite_score", "sector"])
                writer.writeheader()
                for i in items:
                    d = i.model_dump(mode='json')
                    writer.writerow({k: d.get(k) for k in writer.fieldnames})
        except Exception as e:
            raise BreadthStorageError(f"Failed to save ranking: {str(e)}")
        return file_path

    def load_latest_snapshot(self) -> BreadthSnapshot | None:
        snap_dir = self.base_dir / "snapshots"
        if not snap_dir.exists():
            return None

        dirs = sorted([d for d in snap_dir.iterdir() if d.is_dir()], reverse=True)
        for d in dirs:
            f = d / "breadth_snapshot.json"
            if f.exists():
                try:
                    with open(f, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        return BreadthSnapshot(**data)
                except Exception:
                    pass
        return None

    def load_latest_ranking(self, limit: int | None = None) -> list[CrossSectionalRankItem]:
        rank_dir = self.base_dir / "ranking"
        if not rank_dir.exists():
            return []

        dirs = sorted([d for d in rank_dir.iterdir() if d.is_dir()], reverse=True)
        for d in dirs:
            f = d / "cross_sectional_ranking.csv"
            if f.exists():
                items = []
                try:
                    with open(f, "r", encoding="utf-8") as file:
                        reader = csv.DictReader(file)
                        for row in reader:
                            items.append(CrossSectionalRankItem(
                                symbol=row["symbol"],
                                as_of_date=datetime.strptime(d.name, "%Y%m%d"),
                                rank=int(row["rank"]),
                                percentile=float(row["percentile"]),
                                composite_score=float(row["composite_score"]),
                                sector=row.get("sector")
                            ))
                            if limit and len(items) >= limit:
                                break
                    return items
                except Exception:
                    pass
        return []

    def list_recent_snapshots(self, limit: int = 20) -> list[dict[str, Any]]:
        snap_dir = self.base_dir / "snapshots"
        if not snap_dir.exists():
            return []

        dirs = sorted([d for d in snap_dir.iterdir() if d.is_dir()], reverse=True)
        res = []
        for d in dirs[:limit]:
            f = d / "breadth_snapshot.json"
            if f.exists():
                try:
                    with open(f, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        res.append({
                            "snapshot_id": data.get("snapshot_id"),
                            "as_of_date": data.get("as_of_date"),
                            "universe_name": data.get("universe_name"),
                            "composite_score": data.get("composite_score"),
                            "status": data.get("status")
                        })
                except Exception:
                    pass
        return res
