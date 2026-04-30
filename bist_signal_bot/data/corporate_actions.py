import csv
import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import CorporateActionStoreError
from bist_signal_bot.data.models import (
    CorporateAction,
    CorporateActionType,
    CorporateActionValidationIssue,
    CorporateActionValidationReport,
)
from bist_signal_bot.storage.paths import (
    get_corporate_actions_dir,
    get_corporate_actions_file_path,
)

logger = logging.getLogger("bist_signal_bot.data.corporate_actions")


class CorporateActionStore:
    def __init__(self, settings: Settings, base_dir: Path | None = None):
        self.settings = settings
        # base_dir override is mostly for testing if needed
        if base_dir:
            self._actions_dir = base_dir / settings.CORPORATE_ACTIONS_DIR_NAME
            self._actions_file_path = self._actions_dir / settings.CORPORATE_ACTIONS_FILE_NAME
        else:
            self._actions_dir = get_corporate_actions_dir(settings)
            self._actions_file_path = get_corporate_actions_file_path(settings)

    def get_actions_dir(self) -> Path:
        return self._actions_dir

    def get_actions_file_path(self) -> Path:
        return self._actions_file_path

    def exists(self) -> bool:
        return self._actions_file_path.exists()

    def load_actions(self) -> list[CorporateAction]:
        if not self.exists():
            return []
        try:
            with open(self._actions_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "actions" not in data:
                raise CorporateActionStoreError("Invalid corporate actions file format: missing 'actions' key")

            actions = []
            for item in data["actions"]:
                actions.append(CorporateAction(**item))
            return actions
        except json.JSONDecodeError as e:
            raise CorporateActionStoreError(f"Failed to parse corporate actions file as JSON: {e}")
        except ValidationError as e:
            raise CorporateActionStoreError(f"Invalid corporate action data in file: {e}")
        except Exception as e:
            raise CorporateActionStoreError(f"Failed to load corporate actions: {e}")

    def save_actions(self, actions: list[CorporateAction]) -> Path:
        self._actions_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "schema_version": "1.0",
            "updated_at": datetime.now().astimezone().isoformat(),
            "actions": [a.model_dump(mode="json") for a in actions]
        }

        try:
            with open(self._actions_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return self._actions_file_path
        except Exception as e:
            raise CorporateActionStoreError(f"Failed to save corporate actions: {e}")

    def initialize_empty(self, overwrite: bool = False) -> Path:
        if self.exists() and not overwrite:
            return self._actions_file_path

        return self.save_actions([])

    def validate_actions(self, actions: list[CorporateAction]) -> CorporateActionValidationReport:
        valid_actions = 0
        invalid_actions = 0
        duplicate_actions = 0
        issues = []

        seen = set()

        for action in actions:
            try:
                # Validation rules covered by Pydantic model implicitly (symbol format, ratio limits, etc.)
                # Here we just check duplicates
                key = f"{action.symbol}_{action.action_date.isoformat()}_{action.action_type.value}"

                if key in seen:
                    duplicate_actions += 1
                    issues.append(
                        CorporateActionValidationIssue(
                            symbol=action.symbol,
                            action_date=action.action_date,
                            issue_type="DUPLICATE_ACTION",
                            message=f"Duplicate action found for {action.symbol} on {action.action_date} ({action.action_type.value})",
                            severity="WARNING"
                        )
                    )
                else:
                    seen.add(key)
                    valid_actions += 1
            except Exception as e:
                invalid_actions += 1
                issues.append(
                    CorporateActionValidationIssue(
                        symbol=getattr(action, "symbol", None),
                        action_date=getattr(action, "action_date", None),
                        issue_type="VALIDATION_ERROR",
                        message=f"Validation error: {e}",
                        severity="ERROR"
                    )
                )

        passed = invalid_actions == 0

        return CorporateActionValidationReport(
            total_actions=len(actions),
            valid_actions=valid_actions,
            invalid_actions=invalid_actions,
            duplicate_actions=duplicate_actions,
            issues=issues,
            passed=passed
        )

    def get_actions_for_symbol(self, symbol: str) -> list[CorporateAction]:
        from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol
        internal_symbol = ensure_valid_internal_symbol(symbol)

        actions = self.load_actions()
        return [a for a in actions if a.symbol == internal_symbol]

    def add_action(self, action: CorporateAction) -> None:
        actions = self.load_actions()

        # Check duplicate
        for existing in actions:
            if (existing.symbol == action.symbol and
                existing.action_date == action.action_date and
                existing.action_type == action.action_type):
                raise CorporateActionStoreError(
                    f"Action already exists for {action.symbol} on {action.action_date} of type {action.action_type.value}"
                )

        actions.append(action)
        self.save_actions(actions)

    def remove_action(self, symbol: str, action_date: date, action_type: CorporateActionType) -> bool:
        from bist_signal_bot.data.symbol_utils import ensure_valid_internal_symbol
        internal_symbol = ensure_valid_internal_symbol(symbol)

        actions = self.load_actions()
        original_count = len(actions)

        actions = [
            a for a in actions
            if not (a.symbol == internal_symbol and a.action_date == action_date and a.action_type == action_type)
        ]

        if len(actions) < original_count:
            self.save_actions(actions)
            return True

        return False

    def import_actions(self, path: Path, merge: bool = True) -> CorporateActionValidationReport:
        if not path.exists():
            raise CorporateActionStoreError(f"Import file not found: {path}")

        new_actions = []
        issues = []

        ext = path.suffix.lower()
        if ext == ".json":
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Support direct list or schema format
                items = data.get("actions", data) if isinstance(data, dict) else data

                for i, item in enumerate(items):
                    try:
                        new_actions.append(CorporateAction(**item))
                    except ValidationError as e:
                        issues.append(
                            CorporateActionValidationIssue(
                                symbol=item.get("symbol"),
                                issue_type="IMPORT_PARSE_ERROR",
                                message=f"Row {i}: Invalid JSON data: {e}",
                                severity="ERROR"
                            )
                        )
            except Exception as e:
                raise CorporateActionStoreError(f"Failed to import JSON: {e}")

        elif ext == ".csv":
            try:
                with open(path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for i, row in enumerate(reader):
                        try:
                            # Handle clean row dict to convert empty strings to None
                            clean_row = {}
                            for k, v in row.items():
                                if k == "metadata":
                                    if v is not None and str(v).strip() != "":
                                        try:
                                            clean_row[k] = json.loads(v)
                                        except:
                                            clean_row[k] = {}
                                            issues.append(
                                                CorporateActionValidationIssue(
                                                    symbol=row.get("symbol"),
                                                    issue_type="METADATA_PARSE_ERROR",
                                                    message=f"Row {i+2}: Failed to parse metadata JSON",
                                                    severity="WARNING"
                                                )
                                            )
                                    else:
                                        clean_row[k] = {}
                                elif not v or str(v).strip() == "":
                                    clean_row[k] = None
                                elif k in ["ratio", "cash_amount"] and v is not None:
                                    clean_row[k] = float(v)
                                elif k == "verified" and v is not None:
                                    clean_row[k] = str(v).lower() in ("true", "1", "yes", "y")
                                else:
                                    clean_row[k] = v

                            new_actions.append(CorporateAction(**clean_row))
                        except Exception as e:
                            issues.append(
                                CorporateActionValidationIssue(
                                    symbol=row.get("symbol"),
                                    issue_type="IMPORT_PARSE_ERROR",
                                    message=f"Row {i+2}: Invalid CSV data: {e}",
                                    severity="ERROR"
                                )
                            )
            except Exception as e:
                raise CorporateActionStoreError(f"Failed to import CSV: {e}")
        else:
            raise CorporateActionStoreError(f"Unsupported import format: {ext}")

        existing_actions = self.load_actions() if merge else []

        # Merge, preferring new actions on duplicate
        merged_actions = []
        seen = set()

        for action in new_actions:
            key = f"{action.symbol}_{action.action_date.isoformat()}_{action.action_type.value}"
            if key not in seen:
                merged_actions.append(action)
                seen.add(key)

        for action in existing_actions:
            key = f"{action.symbol}_{action.action_date.isoformat()}_{action.action_type.value}"
            if key not in seen:
                merged_actions.append(action)
                seen.add(key)

        # Validate final set
        report = self.validate_actions(merged_actions)

        # Prepend import issues to the report
        report.issues = issues + report.issues
        if issues:
            report.invalid_actions += len(issues)
            report.passed = False

        if report.passed:
            self.save_actions(merged_actions)

        return report

    def export_actions(self, path: Path | None = None, format: str = "json") -> Path:
        actions = self.load_actions()

        if not path:
            dir_path = self.get_actions_dir()
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = dir_path / f"corporate_actions_export_{ts}.{format}"

        fmt = format.lower()
        if fmt == "json":
            self.save_actions(actions) # Save to main
            # To output path:
            data = {
                "schema_version": "1.0",
                "updated_at": datetime.now().astimezone().isoformat(),
                "actions": [a.model_dump(mode="json") for a in actions]
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        elif fmt == "csv":
            if not actions:
                # Write headers only
                with open(path, "w", encoding="utf-8", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["symbol", "action_date", "action_type", "ratio", "cash_amount", "currency", "description", "source", "verified", "metadata"])
            else:
                with open(path, "w", encoding="utf-8", newline='') as f:
                    fieldnames = list(actions[0].model_dump(mode="json").keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for action in actions:
                        row = action.model_dump(mode="json")
                        row["metadata"] = json.dumps(row["metadata"]) if row["metadata"] else ""
                        writer.writerow(row)
        else:
            raise CorporateActionStoreError(f"Unsupported export format: {fmt}")

        return path
