from typing import Any
import pandas as pd

from bist_signal_bot.config_registry.models import (
    ConfigDefinition,
    ConfigValueRecord,
    FeatureFlag,
    RuntimeProfile,
    ConfigValidationResult,
    ConfigSnapshot,
    ConfigDiffResult,
    ConfigDriftResult,
    ConfigGateResult,
    ConfigDiffItem
)

def config_definition_to_dict(defn: ConfigDefinition) -> dict[str, Any]:
    return {
        "key": defn.key,
        "module": defn.module.value,
        "value_type": defn.value_type.value,
        "default_value": defn.default_value,
        "description": defn.description,
        "safety_level": defn.safety_level.value,
        "required": defn.required,
        "secret": defn.secret,
        "enum_values": defn.enum_values,
        "min_value": defn.min_value,
        "max_value": defn.max_value,
        "deprecated": defn.deprecated,
        "replacement_key": defn.replacement_key,
        "metadata": defn.metadata
    }

def config_record_to_dict(record: ConfigValueRecord) -> dict[str, Any]:
    return {
        "key": record.key,
        "value_redacted": record.value_redacted,
        "source": record.source,
        "module": record.module.value,
        "value_type": record.value_type.value,
        "safety_level": record.safety_level.value,
        "is_default": record.is_default,
        "is_secret": record.is_secret,
        "valid": record.valid,
        "warnings": record.warnings,
        "metadata": record.metadata
    }

def feature_flag_to_dict(flag: FeatureFlag) -> dict[str, Any]:
    return {
        "flag_id": flag.flag_id,
        "key": flag.key,
        "module": flag.module.value,
        "state": flag.state.value,
        "default_state": flag.default_state.value,
        "safety_level": flag.safety_level.value,
        "description": flag.description,
        "dependencies": flag.dependencies,
        "conflicts": flag.conflicts,
        "requires_confirm": flag.requires_confirm,
        "metadata": flag.metadata
    }

def runtime_profile_to_dict(profile: RuntimeProfile) -> dict[str, Any]:
    return {
        "profile_id": profile.profile_id,
        "profile_type": profile.profile_type.value,
        "name": profile.name,
        "description": profile.description,
        "overrides": profile.overrides,
        "feature_flags": {k: v.value for k, v in profile.feature_flags.items()},
        "force_research_only": profile.force_research_only,
        "broker_enabled": profile.broker_enabled,
        "real_order_enabled": profile.real_order_enabled,
        "telegram_send_enabled": profile.telegram_send_enabled,
        "scheduler_dry_run": profile.scheduler_dry_run,
        "warnings": profile.warnings,
        "metadata": profile.metadata
    }

def validation_result_to_dict(result: ConfigValidationResult) -> dict[str, Any]:
    return {
        "validation_id": result.validation_id,
        "generated_at": result.generated_at.isoformat(),
        "status": result.status.value,
        "records_checked": result.records_checked,
        "findings": [
            {
                "finding_id": f.finding_id,
                "title": f.title,
                "message": f.message,
                "status": f.status.value,
                "decision": f.decision.value,
                "key": f.key,
                "module": f.module.value if f.module else None
            } for f in result.findings
        ],
        "blocked_count": result.blocked_count,
        "warning_count": result.warning_count,
        "pass_count": result.pass_count,
        "disclaimer": result.disclaimer,
        "metadata": result.metadata
    }

def snapshot_to_dict(snapshot: ConfigSnapshot) -> dict[str, Any]:
    return {
        "snapshot_id": snapshot.snapshot_id,
        "created_at": snapshot.created_at.isoformat(),
        "profile_type": snapshot.profile_type.value if snapshot.profile_type else None,
        "app_version": snapshot.app_version,
        "schema_version": snapshot.schema_version,
        "records": [config_record_to_dict(r) for r in snapshot.records],
        "flags": [feature_flag_to_dict(f) for f in snapshot.flags],
        "redacted": snapshot.redacted,
        "checksum_sha256": snapshot.checksum_sha256,
        "warnings": snapshot.warnings,
        "disclaimer": snapshot.disclaimer,
        "metadata": snapshot.metadata
    }

def diff_to_dict(diff: ConfigDiffResult) -> dict[str, Any]:
    return {
        "diff_id": diff.diff_id,
        "old_snapshot_id": diff.old_snapshot_id,
        "new_snapshot_id": diff.new_snapshot_id,
        "created_at": diff.created_at.isoformat(),
        "items": [
            {
                "key": i.key,
                "change_type": i.change_type,
                "old_value_redacted": i.old_value_redacted,
                "new_value_redacted": i.new_value_redacted,
                "safety_level": i.safety_level.value,
                "decision": i.decision.value,
                "module": i.module.value if i.module else None
            } for i in diff.items
        ],
        "added_count": diff.added_count,
        "removed_count": diff.removed_count,
        "changed_count": diff.changed_count,
        "dangerous_count": diff.dangerous_count,
        "blocked_count": diff.blocked_count,
        "warnings": diff.warnings,
        "disclaimer": diff.disclaimer,
        "metadata": diff.metadata
    }

def drift_to_dict(result: ConfigDriftResult) -> dict[str, Any]:
    return {
        "drift_id": result.drift_id,
        "baseline_snapshot_id": result.baseline_snapshot_id,
        "current_snapshot_id": result.current_snapshot_id,
        "created_at": result.created_at.isoformat(),
        "status": result.status.value,
        "drift_score": result.drift_score,
        "drift_items": [
            {
                "key": i.key,
                "change_type": i.change_type,
                "old_value_redacted": i.old_value_redacted,
                "new_value_redacted": i.new_value_redacted,
                "safety_level": i.safety_level.value,
                "decision": i.decision.value
            } for i in result.drift_items
        ],
        "unexpected_enabled_flags": result.unexpected_enabled_flags,
        "missing_required_keys": result.missing_required_keys,
        "unsafe_changes": result.unsafe_changes,
        "warnings": result.warnings,
        "disclaimer": result.disclaimer,
        "metadata": result.metadata
    }

def gate_to_dict(result: ConfigGateResult) -> dict[str, Any]:
    return {
        "gate_id": result.gate_id,
        "request": {
            "gate_name": result.request.gate_name,
            "profile_type": result.request.profile_type.value if result.request.profile_type else None,
            "require_research_only": result.request.require_research_only,
            "allow_warnings": result.request.allow_warnings,
        },
        "status": result.status.value,
        "decision": result.decision.value,
        "validation_result_id": result.validation_result.validation_id,
        "blocked": result.blocked,
        "warnings": result.warnings,
        "disclaimer": result.disclaimer,
        "metadata": result.metadata
    }

def records_to_dataframe(records: list[ConfigValueRecord]) -> pd.DataFrame:
    data = [config_record_to_dict(r) for r in records]
    return pd.DataFrame(data)

def flags_to_dataframe(flags: list[FeatureFlag]) -> pd.DataFrame:
    data = [feature_flag_to_dict(f) for f in flags]
    return pd.DataFrame(data)

def diff_items_to_dataframe(items: list[ConfigDiffItem]) -> pd.DataFrame:
    data = [
        {
            "key": i.key,
            "change_type": i.change_type,
            "old_value": i.old_value_redacted,
            "new_value": i.new_value_redacted,
            "safety": i.safety_level.value,
            "decision": i.decision.value
        } for i in items
    ]
    return pd.DataFrame(data)

def format_config_records_text(records: list[ConfigValueRecord]) -> str:
    lines = ["Config Records:"]
    for r in records:
        lines.append(f"  {r.key}: {r.value_redacted} ({r.safety_level.value})")
    return "\n".join(lines)

def format_feature_flags_text(flags: list[FeatureFlag]) -> str:
    lines = ["Feature Flags:"]
    for f in flags:
        lines.append(f"  {f.key}: {f.state.value}")
    return "\n".join(lines)

def format_runtime_profile_text(profile: RuntimeProfile) -> str:
    lines = [f"Profile: {profile.name}"]
    lines.append(f"Description: {profile.description}")
    lines.append(f"Force Research Only: {profile.force_research_only}")
    return "\n".join(lines)

def format_validation_result_text(result: ConfigValidationResult) -> str:
    lines = [f"Validation Result: {result.status.value}"]
    lines.append(f"Checked: {result.records_checked}, Passed: {result.pass_count}, Warns: {result.warning_count}, Blocked: {result.blocked_count}")
    for f in result.findings:
        lines.append(f"  - [{f.status.value}] {f.title}: {f.message}")
    lines.append(f"\nDisclaimer: {result.disclaimer}")
    return "\n".join(lines)

def format_snapshot_text(snapshot: ConfigSnapshot) -> str:
    lines = [f"Snapshot ID: {snapshot.snapshot_id} ({snapshot.created_at})"]
    lines.append(f"Records: {len(snapshot.records)}, Flags: {len(snapshot.flags)}")
    lines.append(f"Checksum: {snapshot.checksum_sha256}")
    lines.append(f"\nDisclaimer: {snapshot.disclaimer}")
    return "\n".join(lines)

def format_diff_text(diff: ConfigDiffResult) -> str:
    lines = [f"Diff ID: {diff.diff_id}"]
    lines.append(f"Added: {diff.added_count}, Removed: {diff.removed_count}, Changed: {diff.changed_count}, Dangerous: {diff.dangerous_count}, Blocked: {diff.blocked_count}")
    for i in diff.items:
        lines.append(f"  {i.change_type} {i.key}: {i.old_value_redacted} -> {i.new_value_redacted} ({i.decision.value})")
    lines.append(f"\nDisclaimer: {diff.disclaimer}")
    return "\n".join(lines)

def format_drift_text(result: ConfigDriftResult) -> str:
    lines = [f"Drift Status: {result.status.value} (Score: {result.drift_score})"]
    if result.unsafe_changes:
        lines.append(f"Unsafe changes: {', '.join(result.unsafe_changes)}")
    lines.append(f"\nDisclaimer: {result.disclaimer}")
    return "\n".join(lines)

def format_config_registry_report_markdown(snapshot: ConfigSnapshot, validation: ConfigValidationResult | None = None) -> str:
    lines = [
        "# Config Registry Report",
        f"Snapshot ID: {snapshot.snapshot_id}",
        f"Date: {snapshot.created_at.isoformat()}",
        f"Checksum: {snapshot.checksum_sha256}",
        f"Profile: {snapshot.profile_type.value if snapshot.profile_type else 'None'}",
        ""
    ]

    if validation:
        lines.append("## Validation")
        lines.append(f"Status: **{validation.status.value}**")
        lines.append(f"Blocked: {validation.blocked_count}, Warnings: {validation.warning_count}")
        lines.append("")

    lines.append("## Flags")
    for f in snapshot.flags:
        lines.append(f"- `{f.key}`: {f.state.value}")

    lines.append("")
    lines.append("*" + snapshot.disclaimer + "*")

    return "\n".join(lines)
