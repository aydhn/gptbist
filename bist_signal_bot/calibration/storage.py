import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_calibration_dir
from bist_signal_bot.core.exceptions import CalibrationStorageError
from bist_signal_bot.calibration.models import (
    OutcomeRecord, CalibrationResult, ReliabilityCurve, CalibratorMapping,
    ThresholdPolicy, ErrorCase, CalibrationReport, CalibrationScoreType, ThresholdPolicyStatus
)

class CalibrationStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or Settings()
        self.base_dir = base_dir or get_calibration_dir(self.settings)

        self.outcomes_dir = self.base_dir / "outcomes"
        self.results_dir = self.base_dir / "results"
        self.reliability_dir = self.base_dir / "reliability"
        self.mappings_dir = self.base_dir / "mappings"
        self.thresholds_dir = self.base_dir / "thresholds"
        self.errors_dir = self.base_dir / "errors"
        self.reports_dir = self.base_dir / "reports"

        for d in [self.outcomes_dir, self.results_dir, self.reliability_dir,
                  self.mappings_dir, self.thresholds_dir, self.errors_dir, self.reports_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.outcomes_file = self.outcomes_dir / "outcome_records.jsonl"
        self.results_file = self.results_dir / "calibration_results.jsonl"
        self.curves_file = self.reliability_dir / "reliability_curves.jsonl"
        self.mappings_file = self.mappings_dir / "calibrator_mappings.jsonl"
        self.thresholds_file = self.thresholds_dir / "threshold_policies.jsonl"
        self.errors_file = self.errors_dir / "error_cases.jsonl"

    def _append_jsonl(self, filepath: Path, items: list | BaseModel) -> Path:
        try:
            if not isinstance(items, list):
                items = [items]
            with filepath.open("a", encoding="utf-8") as f:
                for item in items:
                    f.write(item.model_dump_json() + "\n")
            return filepath
        except Exception as e:
            raise CalibrationStorageError(f"Failed to append to {filepath}: {str(e)}")

    def _load_jsonl(self, filepath: Path, model_cls) -> list:
        if not filepath.exists():
            return []
        results = []
        try:
            with filepath.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        results.append(model_cls.model_validate_json(line))
                    except Exception:
                        pass
        except Exception as e:
            raise CalibrationStorageError(f"Failed to load {filepath}: {str(e)}")
        return results

    def append_outcomes(self, records: list[OutcomeRecord]) -> Path:
        return self._append_jsonl(self.outcomes_file, records)

    def load_outcomes(self, strategy_name: str | None = None, symbol: str | None = None, limit: int = 10000) -> list[OutcomeRecord]:
        records = self._load_jsonl(self.outcomes_file, OutcomeRecord)
        if strategy_name:
            records = [r for r in records if r.strategy_name == strategy_name]
        if symbol:
            symbol = symbol.upper()
            records = [r for r in records if r.symbol == symbol]

        records.sort(key=lambda x: x.generated_at, reverse=True)
        return records[:limit]

    def append_calibration_result(self, result: CalibrationResult) -> Path:
        return self._append_jsonl(self.results_file, result)

    def load_latest_calibration(self, score_type: CalibrationScoreType | None = None, strategy_name: str | None = None) -> CalibrationResult | None:
        results = self._load_jsonl(self.results_file, CalibrationResult)
        if score_type:
            results = [r for r in results if r.score_type == score_type]
        if strategy_name:
            results = [r for r in results if r.strategy_name == strategy_name]

        if not results:
            return None

        results.sort(key=lambda x: x.generated_at, reverse=True)
        return results[0]

    def append_reliability_curve(self, curve: ReliabilityCurve) -> Path:
        return self._append_jsonl(self.curves_file, curve)

    def append_mapping(self, mapping: CalibratorMapping) -> Path:
        return self._append_jsonl(self.mappings_file, mapping)

    def load_latest_mapping(self, score_type: CalibrationScoreType) -> CalibratorMapping | None:
        mappings = self._load_jsonl(self.mappings_file, CalibratorMapping)
        mappings = [m for m in mappings if m.score_type == score_type]
        if not mappings:
            return None
        mappings.sort(key=lambda x: x.created_at, reverse=True)
        return mappings[0]

    def append_threshold_policy(self, policy: ThresholdPolicy) -> Path:
        return self._append_jsonl(self.thresholds_file, policy)

    def load_threshold_policies(self, strategy_name: str | None = None, status: ThresholdPolicyStatus | None = None) -> list[ThresholdPolicy]:
        policies = self._load_jsonl(self.thresholds_file, ThresholdPolicy)

        if strategy_name:
            policies = [p for p in policies if p.strategy_name == strategy_name]
        if status:
            policies = [p for p in policies if p.status == status]

        latest_policies = {}
        for p in sorted(policies, key=lambda x: x.created_at):
            key = f"{p.strategy_name}_{p.score_type.value}"
            latest_policies[key] = p

        return list(latest_policies.values())

    def append_error_cases(self, errors: list[ErrorCase]) -> Path:
        return self._append_jsonl(self.errors_file, errors)

    def load_error_cases(self, strategy_name: str | None = None, symbol: str | None = None, limit: int = 1000) -> list[ErrorCase]:
        errors = self._load_jsonl(self.errors_file, ErrorCase)
        if strategy_name:
            errors = [e for e in errors if e.strategy_name == strategy_name]
        if symbol:
            symbol = symbol.upper()
            errors = [e for e in errors if e.symbol == symbol]
        return errors[-limit:]

    def save_report(self, report: CalibrationReport, markdown_text: str) -> dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        daily_dir = self.reports_dir / date_str
        daily_dir.mkdir(parents=True, exist_ok=True)

        md_file = daily_dir / "calibration_report.md"
        json_file = daily_dir / "calibration_report.json"

        try:
            with md_file.open("w", encoding="utf-8") as f:
                f.write(markdown_text)

            with json_file.open("w", encoding="utf-8") as f:
                f.write(report.model_dump_json(indent=2))

            return {
                "markdown": md_file,
                "json": json_file
            }
        except Exception as e:
            raise CalibrationStorageError(f"Failed to save report: {str(e)}")
