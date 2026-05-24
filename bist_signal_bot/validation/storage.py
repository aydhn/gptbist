import json
from pathlib import Path
from typing import List, Dict, Any
import datetime

from bist_signal_bot.validation.models import StrategyValidationResult
from bist_signal_bot.core.exceptions import ValidationStorageError

class ValidationStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.results_dir = self.base_dir / "results"
        self.recent_dir = self.base_dir / "recent"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.recent_dir.mkdir(parents=True, exist_ok=True)

    def save_result(self, result: StrategyValidationResult) -> Dict[str, Path]:
        date_str = result.generated_at.strftime("%Y%m%d")
        out_dir = self.results_dir / date_str / result.validation_id
        out_dir.mkdir(parents=True, exist_ok=True)
        main_path = out_dir / "strategy_validation_result.json"
        with open(main_path, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))
        return {"main": main_path}

    def load_result(self, validation_id: str) -> StrategyValidationResult | None:
        for date_dir in self.results_dir.iterdir():
            if date_dir.is_dir():
                res_dir = date_dir / validation_id
                if res_dir.exists():
                    main_path = res_dir / "strategy_validation_result.json"
                    if main_path.exists():
                        with open(main_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            return StrategyValidationResult(**data)
        return None

    def load_latest_result(self, strategy_name: str | None = None) -> StrategyValidationResult | None:
        # Mock load latest
        return self.load_result("1")
