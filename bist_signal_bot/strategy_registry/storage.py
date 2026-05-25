import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime, UTC
from typing import Any
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_strategy_registry_dir
from bist_signal_bot.strategy_registry.models import (
    StrategyDefinition,
    StrategyEvidenceRef,
    StrategyScorecard,
    StrategyLifecycleEvent,
    StrategyPromotionResult,
    StrategyRegistrySnapshot,
    StrategyRegistryStatus,
    StrategyFamily,
    StrategyEvidenceType,
    StrategyGateDecision,
    StrategyLifecycleEventType,
    StrategyScoreComponent
)
from bist_signal_bot.core.exceptions import StrategyRegistryStorageError

class StrategyRegistryStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or Settings()
        self.base_dir = base_dir or get_strategy_registry_dir(self.settings)

        self.definitions_dir = self.base_dir / "definitions"
        self.evidence_dir = self.base_dir / "evidence"
        self.scorecards_dir = self.base_dir / "scorecards"
        self.lifecycle_dir = self.base_dir / "lifecycle"
        self.promotions_dir = self.base_dir / "promotions"
        self.snapshots_dir = self.base_dir / "snapshots"
        self.reports_dir = self.base_dir / "reports"

        self.definitions_file = self.definitions_dir / "strategy_definitions.jsonl"
        self.evidence_file = self.evidence_dir / "strategy_evidence.jsonl"
        self.scorecards_file = self.scorecards_dir / "strategy_scorecards.jsonl"
        self.lifecycle_file = self.lifecycle_dir / "strategy_lifecycle_events.jsonl"
        self.promotions_file = self.promotions_dir / "strategy_promotion_results.jsonl"

        self._ensure_dirs()

    def _ensure_dirs(self):
        for d in [self.definitions_dir, self.evidence_dir, self.scorecards_dir,
                  self.lifecycle_dir, self.promotions_dir, self.snapshots_dir, self.reports_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _read_jsonl(self, file_path: Path, limit: int = 1000) -> list[dict]:
        if not file_path.exists():
            return []

        results = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    if not line.strip():
                        continue
                    results.append(json.loads(line))
                    if len(results) >= limit:
                        break
        except Exception as e:
            raise StrategyRegistryStorageError(f"Failed to read {file_path}: {e}")

        return results

    def _append_jsonl(self, file_path: Path, data: dict) -> Path:
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, default=str) + "\n")
            return file_path
        except Exception as e:
            raise StrategyRegistryStorageError(f"Failed to append to {file_path}: {e}")

    # Definitions
    def append_definition(self, definition: StrategyDefinition) -> Path:
        from bist_signal_bot.strategy_registry.reporting import strategy_definition_to_dict
        data = strategy_definition_to_dict(definition)
        return self._append_jsonl(self.definitions_file, data)

    def load_definitions(self, limit: int = 1000) -> list[StrategyDefinition]:
        raw_data = self._read_jsonl(self.definitions_file, limit=limit)
        definitions = []
        seen_ids = set()

        for item in raw_data:
            if item.get("strategy_id") in seen_ids:
                continue

            seen_ids.add(item.get("strategy_id"))

            try:
                definition = StrategyDefinition(
                    strategy_id=item["strategy_id"],
                    strategy_name=item["strategy_name"],
                    display_name=item.get("display_name", ""),
                    version=item["version"],
                    family=StrategyFamily(item["family"]),
                    status=StrategyRegistryStatus(item["status"]),
                    module_path=item.get("module_path"),
                    class_name=item.get("class_name"),
                    default_parameters=item.get("default_parameters", {}),
                    parameter_schema=item.get("parameter_schema", {}),
                    supported_timeframes=item.get("supported_timeframes", []),
                    supported_order_sides=item.get("supported_order_sides", []),
                    supported_universes=item.get("supported_universes", []),
                    requires_adjusted_prices=item.get("requires_adjusted_prices", False),
                    supports_short=item.get("supports_short", False),
                    supports_cost_model=item.get("supports_cost_model", False),
                    created_at=datetime.fromisoformat(item["created_at"]) if "created_at" in item else datetime.now(UTC),
                    updated_at=datetime.fromisoformat(item["updated_at"]) if "updated_at" in item else datetime.now(UTC),
                    owner=item.get("owner"),
                    tags=item.get("tags", []),
                    warnings=item.get("warnings", []),
                    disclaimer=item.get("disclaimer", "Strategy definition is research metadata only. Not investment advice. No real order was sent."),
                    metadata=item.get("metadata", {})
                )
                definitions.append(definition)
            except Exception as e:
                print(f"Warning: Failed to parse StrategyDefinition: {e}")

        return definitions

    def get_definition(self, strategy_id_or_name: str) -> StrategyDefinition | None:
        definitions = self.load_definitions()
        for d in definitions:
            if d.strategy_id == strategy_id_or_name or d.strategy_name == strategy_id_or_name:
                return d
        return None

    # Evidence
    def append_evidence(self, evidence: StrategyEvidenceRef) -> Path:
        from bist_signal_bot.strategy_registry.reporting import strategy_evidence_to_dict
        data = strategy_evidence_to_dict(evidence)
        return self._append_jsonl(self.evidence_file, data)

    def load_evidence(self, strategy_id_or_name: str | None = None, limit: int = 10000) -> list[StrategyEvidenceRef]:
        raw_data = self._read_jsonl(self.evidence_file, limit=limit)

        strategy_id = None
        if strategy_id_or_name:
            definition = self.get_definition(strategy_id_or_name)
            if definition:
                strategy_id = definition.strategy_id
            else:
                strategy_id = strategy_id_or_name

        evidence_list = []
        for item in raw_data:
            if strategy_id and item.get("strategy_id") != strategy_id:
                continue

            try:
                evidence = StrategyEvidenceRef(
                    evidence_id=item["evidence_id"],
                    strategy_id=item["strategy_id"],
                    evidence_type=StrategyEvidenceType(item["evidence_type"]),
                    source_ref=item.get("source_ref"),
                    symbol=item.get("symbol"),
                    created_at=datetime.fromisoformat(item["created_at"]) if "created_at" in item else datetime.now(UTC),
                    title=item.get("title", ""),
                    summary=item.get("summary", ""),
                    score=item.get("score"),
                    status=item.get("status"),
                    warnings=item.get("warnings", []),
                    metadata=item.get("metadata", {})
                )
                evidence_list.append(evidence)
            except Exception as e:
                print(f"Warning: Failed to parse StrategyEvidenceRef: {e}")

        return evidence_list

    # Scorecards
    def append_scorecard(self, scorecard: StrategyScorecard) -> Path:
        from bist_signal_bot.strategy_registry.reporting import scorecard_to_dict
        data = scorecard_to_dict(scorecard)
        return self._append_jsonl(self.scorecards_file, data)

    def load_latest_scorecard(self, strategy_id_or_name: str) -> StrategyScorecard | None:
        raw_data = self._read_jsonl(self.scorecards_file, limit=100)

        strategy_id = None
        definition = self.get_definition(strategy_id_or_name)
        if definition:
            strategy_id = definition.strategy_id
        else:
            strategy_id = strategy_id_or_name

        for item in raw_data:
            if item.get("strategy_id") == strategy_id or item.get("strategy_name") == strategy_id_or_name:
                try:
                    components = []
                    for c_data in item.get("components", []):
                        components.append(StrategyScoreComponent(
                            component_id=c_data["component_id"],
                            name=c_data["name"],
                            evidence_type=StrategyEvidenceType(c_data["evidence_type"]),
                            score=c_data.get("score"),
                            weight=c_data.get("weight", 0.0),
                            status=StrategyRegistryStatus(c_data["status"]) if c_data.get("status") else None,
                            message=c_data.get("message", ""),
                            evidence_refs=c_data.get("evidence_refs", []),
                            warnings=c_data.get("warnings", []),
                            metadata=c_data.get("metadata", {})
                        ))

                    return StrategyScorecard(
                        scorecard_id=item["scorecard_id"],
                        strategy_id=item["strategy_id"],
                        strategy_name=item["strategy_name"],
                        version=item["version"],
                        generated_at=datetime.fromisoformat(item["generated_at"]) if "generated_at" in item else datetime.now(UTC),
                        components=components,
                        aggregate_score=item.get("aggregate_score"),
                        confidence_score=item.get("confidence_score"),
                        robustness_score=item.get("robustness_score"),
                        overfit_risk_score=item.get("overfit_risk_score"),
                        execution_penalty_score=item.get("execution_penalty_score"),
                        drift_risk_score=item.get("drift_risk_score"),
                        status=StrategyRegistryStatus(item["status"]) if item.get("status") else StrategyRegistryStatus.UNKNOWN,
                        gate_decision=StrategyGateDecision(item["gate_decision"]) if item.get("gate_decision") else StrategyGateDecision.UNKNOWN,
                        recommended_actions=item.get("recommended_actions", []),
                        warnings=item.get("warnings", []),
                        disclaimer=item.get("disclaimer", "Strategy scorecard is research-only. It does not approve real trading. No real order was sent."),
                        metadata=item.get("metadata", {})
                    )
                except Exception as e:
                    print(f"Warning: Failed to parse StrategyScorecard: {e}")

        return None

    # Lifecycle Events
    def append_lifecycle_event(self, event: StrategyLifecycleEvent) -> Path:
        from bist_signal_bot.strategy_registry.reporting import lifecycle_event_to_dict
        data = lifecycle_event_to_dict(event)
        return self._append_jsonl(self.lifecycle_file, data)

    def load_lifecycle_events(self, strategy_id_or_name: str | None = None, limit: int = 1000) -> list[StrategyLifecycleEvent]:
        raw_data = self._read_jsonl(self.lifecycle_file, limit=limit)

        strategy_id = None
        if strategy_id_or_name:
            definition = self.get_definition(strategy_id_or_name)
            if definition:
                strategy_id = definition.strategy_id
            else:
                strategy_id = strategy_id_or_name

        events = []
        for item in raw_data:
            if strategy_id and item.get("strategy_id") != strategy_id and item.get("strategy_name") != strategy_id_or_name:
                continue

            try:
                event = StrategyLifecycleEvent(
                    event_id=item["event_id"],
                    strategy_id=item["strategy_id"],
                    strategy_name=item["strategy_name"],
                    event_type=StrategyLifecycleEventType(item["event_type"]),
                    previous_status=StrategyRegistryStatus(item["previous_status"]) if item.get("previous_status") else None,
                    new_status=StrategyRegistryStatus(item["new_status"]) if item.get("new_status") else None,
                    created_at=datetime.fromisoformat(item["created_at"]) if "created_at" in item else datetime.now(UTC),
                    reason=item.get("reason", ""),
                    actor=item.get("actor"),
                    evidence_refs=item.get("evidence_refs", []),
                    warnings=item.get("warnings", []),
                    disclaimer=item.get("disclaimer", "Strategy lifecycle event is research metadata only. No real order was sent."),
                    metadata=item.get("metadata", {})
                )
                events.append(event)
            except Exception as e:
                print(f"Warning: Failed to parse StrategyLifecycleEvent: {e}")

        return events

    # Promotions
    def append_promotion_result(self, result: StrategyPromotionResult) -> Path:
        from bist_signal_bot.strategy_registry.reporting import promotion_result_to_dict
        data = promotion_result_to_dict(result)
        return self._append_jsonl(self.promotions_file, data)

    # Snapshots
    def save_snapshot(self, snapshot: StrategyRegistrySnapshot) -> dict[str, Path]:
        from bist_signal_bot.strategy_registry.reporting import snapshot_to_dict
        date_str = snapshot.created_at.strftime("%Y%m%d")
        snapshot_dir = self.snapshots_dir / date_str / snapshot.snapshot_id
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        file_path = snapshot_dir / "strategy_registry_snapshot.json"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(snapshot_to_dict(snapshot), f, indent=2, default=str)
        except Exception as e:
            raise StrategyRegistryStorageError(f"Failed to save snapshot to {file_path}: {e}")

        return {"json": file_path}

    def load_latest_snapshot(self) -> StrategyRegistrySnapshot | None:
        if not self.snapshots_dir.exists():
            return None

        date_dirs = sorted([d for d in self.snapshots_dir.iterdir() if d.is_dir()], reverse=True)
        for date_dir in date_dirs:
            snapshot_dirs = sorted([d for d in date_dir.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)
            for snapshot_dir in snapshot_dirs:
                file_path = snapshot_dir / "strategy_registry_snapshot.json"
                if file_path.exists():
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            item = json.load(f)

                        return StrategyRegistrySnapshot(
                            snapshot_id=item["snapshot_id"],
                            created_at=datetime.fromisoformat(item["created_at"]) if "created_at" in item else datetime.now(UTC),
                            strategies_count=item.get("strategies_count", 0),
                            status_counts=item.get("status_counts", {}),
                            scorecards_count=item.get("scorecards_count", 0),
                            blocked_strategies=item.get("blocked_strategies", []),
                            candidate_strategies=item.get("candidate_strategies", []),
                            validated_research_strategies=item.get("validated_research_strategies", []),
                            warnings=item.get("warnings", []),
                            checksum_sha256=item.get("checksum_sha256"),
                            disclaimer=item.get("disclaimer", "Strategy registry snapshot is operational research metadata only. No real order was sent."),
                            metadata=item.get("metadata", {})
                        )
                    except Exception as e:
                        print(f"Warning: Failed to parse StrategyRegistrySnapshot: {e}")

        return None
