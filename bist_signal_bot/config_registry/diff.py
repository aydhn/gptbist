import uuid
from typing import Any
from datetime import datetime, UTC

from bist_signal_bot.config_registry.models import (
    ConfigChangeDecision,
    ConfigDefinition,
    ConfigDiffItem,
    ConfigDiffResult,
    ConfigSafetyLevel,
    ConfigSnapshot,
)
from bist_signal_bot.config_registry.schema import ConfigSchemaBuilder


class ConfigDiffEngine:
    def __init__(self, schema_builder: ConfigSchemaBuilder | None = None, store=None):
        self.schema_builder = schema_builder or ConfigSchemaBuilder()
        self.store = store

    def diff_snapshots(self, old: ConfigSnapshot, new: ConfigSnapshot) -> ConfigDiffResult:
        old_dict = {r.key: r for r in old.records}
        new_dict = {r.key: r for r in new.records}

        items = []
        all_keys = set(old_dict.keys()).union(set(new_dict.keys()))

        for k in all_keys:
            old_r = old_dict.get(k)
            new_r = new_dict.get(k)

            definition = self.schema_builder.definition_for_key(k)

            if not old_r and new_r:
                decision = self.classify_change(k, None, new_r.value_redacted, definition)
                items.append(ConfigDiffItem(
                    key=k,
                    module=new_r.module,
                    change_type="ADDED",
                    old_value_redacted=None,
                    new_value_redacted=new_r.value_redacted,
                    safety_level=new_r.safety_level,
                    decision=decision
                ))
            elif old_r and not new_r:
                decision = self.classify_change(k, old_r.value_redacted, None, definition)
                items.append(ConfigDiffItem(
                    key=k,
                    module=old_r.module,
                    change_type="REMOVED",
                    old_value_redacted=old_r.value_redacted,
                    new_value_redacted=None,
                    safety_level=old_r.safety_level,
                    decision=decision
                ))
            elif old_r and new_r and str(old_r.value_redacted) != str(new_r.value_redacted):
                decision = self.classify_change(k, old_r.value_redacted, new_r.value_redacted, definition)
                items.append(ConfigDiffItem(
                    key=k,
                    module=new_r.module,
                    change_type="CHANGED",
                    old_value_redacted=old_r.value_redacted,
                    new_value_redacted=new_r.value_redacted,
                    safety_level=new_r.safety_level,
                    decision=decision
                ))

        # Check flags too
        old_flags = {f.key: f for f in old.flags}
        new_flags = {f.key: f for f in new.flags}

        flag_keys = set(old_flags.keys()).union(set(new_flags.keys()))
        for k in flag_keys:
             old_f = old_flags.get(k)
             new_f = new_flags.get(k)
             if old_f and new_f and old_f.state != new_f.state:
                 items.append(ConfigDiffItem(
                    key=k,
                    module=new_f.module,
                    change_type="CHANGED_FLAG",
                    old_value_redacted=old_f.state.value,
                    new_value_redacted=new_f.state.value,
                    safety_level=new_f.safety_level,
                    decision=ConfigChangeDecision.REQUIRE_CONFIRM if new_f.requires_confirm else ConfigChangeDecision.ALLOW
                 ))

        blocked = sum(1 for i in items if i.decision.name.startswith("BLOCK"))
        dangerous = sum(1 for i in items if i.safety_level in [ConfigSafetyLevel.DANGEROUS, ConfigSafetyLevel.FORBIDDEN])

        return ConfigDiffResult(
            diff_id=str(uuid.uuid4()),
            created_at=datetime.now(UTC),
            old_snapshot_id=old.snapshot_id,
            new_snapshot_id=new.snapshot_id,
            items=items,
            added_count=sum(1 for i in items if i.change_type == "ADDED"),
            removed_count=sum(1 for i in items if i.change_type == "REMOVED"),
            changed_count=sum(1 for i in items if i.change_type.startswith("CHANGED")),
            dangerous_count=dangerous,
            blocked_count=blocked
        )

    def diff_current_against_snapshot(self, snapshot_id: str) -> ConfigDiffResult:
        if not self.store:
             raise ValueError("Store not configured")
        old = self.store.load_snapshot(snapshot_id)
        if not old:
             raise ValueError(f"Snapshot not found: {snapshot_id}")

        # In a real impl, we'd take a new snapshot here.
        # This requires circular dependency resolution or passing current snapshot explicitly.
        # We will mock the current snapshot fetch in the caller or app level.
        raise NotImplementedError("Use diff_snapshots with a freshly created snapshot")

    def classify_change(self, key: str, old_value: Any, new_value: Any, definition: ConfigDefinition | None = None) -> ConfigChangeDecision:
        if not definition:
            return ConfigChangeDecision.WARN

        if definition.safety_level == ConfigSafetyLevel.FORBIDDEN:
            return ConfigChangeDecision.BLOCK_FORBIDDEN

        if definition.safety_level in [ConfigSafetyLevel.DANGEROUS, ConfigSafetyLevel.SENSITIVE]:
            return ConfigChangeDecision.REQUIRE_CONFIRM

        return ConfigChangeDecision.ALLOW

    def summarize_diff(self, diff: ConfigDiffResult) -> dict[str, Any]:
        return {
            "diff_id": diff.diff_id,
            "created_at": diff.created_at.isoformat(),
            "items_count": len(diff.items),
            "blocked": diff.blocked_count,
            "dangerous": diff.dangerous_count
        }
