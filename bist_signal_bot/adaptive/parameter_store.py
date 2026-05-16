import json
import logging
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.adaptive.models import AdaptiveParameterSet, AdaptiveEvidence
from bist_signal_bot.core.exceptions import AdaptiveParameterStoreError

class AdaptiveParameterStore:
    def __init__(self, data_dir: Path, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.settings = settings
        self.logger = logger or logging.getLogger(__name__)
        self.data_dir = data_dir

        self.params_dir = self.data_dir / "parameters"
        self.params_dir.mkdir(parents=True, exist_ok=True)

        self.active_file = self.params_dir / "active_parameters.json"
        self.history_file = self.params_dir / "history.jsonl"

    def load_active_parameters(self) -> list[AdaptiveParameterSet]:
        if not self.active_file.exists():
            return []

        try:
            with open(self.active_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [AdaptiveParameterSet.model_validate(item) for item in data]
        except Exception as e:
            self.logger.error(f"Failed to load active parameters: {e}")
            return []

    def save_active_parameters(self, parameter_sets: list[AdaptiveParameterSet], confirm: bool = False) -> Path:
        if not confirm:
            raise AdaptiveParameterStoreError("Explicit confirmation required to save active parameters")

        try:
            from bist_signal_bot.security.path_guard import PathGuard
            PathGuard([self.active_file]).resolve_safe_path(self.active_file)

            data = [p.model_dump(mode='json') for p in parameter_sets if p.active]
            with open(self.active_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            self.logger.info(f"Saved {len(data)} active parameter sets")
            return self.active_file
        except Exception as e:
            raise AdaptiveParameterStoreError(f"Failed to save parameters: {e}")

    def upsert_parameter_set(self, parameter_set: AdaptiveParameterSet, confirm: bool = False) -> AdaptiveParameterSet:
        if not confirm:
            raise AdaptiveParameterStoreError("Explicit confirmation required to upsert parameters")

        try:
            active_sets = self.load_active_parameters()

            updated = False
            for i, p in enumerate(active_sets):
                if p.strategy_name == parameter_set.strategy_name and p.symbol == parameter_set.symbol:
                    active_sets[i] = parameter_set
                    updated = True
                    break

            if not updated:
                active_sets.append(parameter_set)

            self.save_active_parameters(active_sets, confirm=True)
            self._append_to_history(parameter_set, action="upsert")
            return parameter_set

        except Exception as e:
            raise AdaptiveParameterStoreError(f"Failed to upsert parameter set: {e}")

    def deactivate_parameter_set(self, parameter_set_id: str, confirm: bool = False) -> AdaptiveParameterSet:
        if not confirm:
            raise AdaptiveParameterStoreError("Explicit confirmation required to deactivate parameters")

        try:
            active_sets = self.load_active_parameters()
            target = None

            for p in active_sets:
                if p.parameter_set_id == parameter_set_id:
                    p.active = False
                    p.updated_at = datetime.now(timezone.utc)
                    target = p
                    break

            if not target:
                raise AdaptiveParameterStoreError(f"Parameter set {parameter_set_id} not found")

            self.save_active_parameters(active_sets, confirm=True)
            self._append_to_history(target, action="deactivate")
            return target

        except Exception as e:
            raise AdaptiveParameterStoreError(f"Failed to deactivate parameter set: {e}")

    def parameter_set_for(self, strategy_name: str, symbol: str | None = None) -> AdaptiveParameterSet | None:
        active_sets = self.load_active_parameters()
        for p in active_sets:
            if p.strategy_name == strategy_name and p.symbol == symbol:
                return p
        if symbol is not None:
            for p in active_sets:
                if p.strategy_name == strategy_name and p.symbol is None:
                    return p
        return None

    def history(self, limit: int = 100) -> list[dict[str, Any]]:
        if not self.history_file.exists():
            return []

        try:
            records = []
            with open(self.history_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
            return records[-limit:][::-1]
        except Exception as e:
            self.logger.error(f"Failed to read parameter history: {e}")
            return []

    def build_parameter_set_from_optimization(self, evidence: AdaptiveEvidence) -> AdaptiveParameterSet | None:
        from bist_signal_bot.adaptive.models import AdaptiveEvidenceType
        import uuid

        if evidence.evidence_type != AdaptiveEvidenceType.OPTIMIZATION:
            return None

        if not evidence.params:
            return None

        now = datetime.now(timezone.utc)

        return AdaptiveParameterSet(
            parameter_set_id=f"param_{uuid.uuid4().hex[:8]}",
            strategy_name=evidence.strategy_name or "unknown",
            symbol=evidence.symbol,
            params=evidence.params,
            source=f"optimization_{evidence.evidence_id}",
            score=evidence.score or 0.0,
            active=True,
            created_at=now,
            updated_at=now
        )

    def _append_to_history(self, parameter_set: AdaptiveParameterSet, action: str) -> None:
        try:
            from bist_signal_bot.security.path_guard import PathGuard
            PathGuard([self.history_file]).resolve_safe_path(self.history_file)

            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": action,
                "parameter_set": parameter_set.model_dump(mode='json')
            }

            with open(self.history_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            self.logger.warning(f"Failed to append to parameter history: {e}")
