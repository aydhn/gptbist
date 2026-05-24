import json
import argparse
from pathlib import Path

from bist_signal_bot.app.config_registry_app import (
    create_config_diff_engine,
    create_config_drift_detector,
    create_config_gate,
    create_config_registry,
    create_config_snapshot_manager,
    create_config_validator,
    create_feature_flag_manager,
    create_runtime_profile_manager,
)
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.config_registry.models import ConfigModule, RuntimeProfileType
from bist_signal_bot.config_registry.reporting import (
    diff_to_dict,
    drift_to_dict,
    format_config_records_text,
    format_diff_text,
    format_drift_text,
    format_feature_flags_text,
    format_runtime_profile_text,
    format_snapshot_text,
    format_validation_result_text,
    gate_to_dict,
    snapshot_to_dict,
    validation_result_to_dict,
)


def list_records(args, settings: Settings):
    registry = create_config_registry(settings)
    module = None
    if args.module:
        try:
            module = ConfigModule(args.module)
        except ValueError:
            print(f"Unknown module: {args.module}")
            return

    records = registry.list_records(module=module)
    if args.json:
        print(json.dumps([r.value_redacted for r in records], indent=2))
    else:
        print(format_config_records_text(records))


def show_record(args, settings: Settings):
    registry = create_config_registry(settings)
    record = registry.get_record(args.key)
    if not record:
        print(f"Unknown config key: {args.key}")
        return

    if args.json:
        from bist_signal_bot.config_registry.reporting import config_record_to_dict
        print(json.dumps(config_record_to_dict(record), indent=2))
    else:
        print(f"{record.key}: {record.value_redacted} ({record.safety_level.value})")


def validate_config(args, settings: Settings):
    registry = create_config_registry(settings)
    validator = create_config_validator(settings)

    records = registry.list_records()
    res = validator.validate_all(records)

    if args.json:
        print(json.dumps(validation_result_to_dict(res), indent=2))
    else:
        print(format_validation_result_text(res))


def show_flags(args, settings: Settings):
    manager = create_feature_flag_manager(settings)
    flags = manager.load_flags()

    if args.module:
        flags = [f for f in flags if f.module.value == args.module]

    if args.json:
        from bist_signal_bot.config_registry.reporting import feature_flag_to_dict
        print(json.dumps([feature_flag_to_dict(f) for f in flags], indent=2))
    else:
        print(format_feature_flags_text(flags))


def show_profiles(args, settings: Settings):
    manager = create_runtime_profile_manager(settings)
    profiles = manager.default_profiles()

    if args.json:
        from bist_signal_bot.config_registry.reporting import runtime_profile_to_dict
        print(json.dumps([runtime_profile_to_dict(p) for p in profiles], indent=2))
    else:
        for p in profiles:
            print(f"- {p.profile_type.value}: {p.name}")


def profile_preview(args, settings: Settings):
    manager = create_runtime_profile_manager(settings)
    try:
        ptype = RuntimeProfileType(args.profile_type)
        diff = manager.preview_profile(ptype)
        if args.json:
            print(json.dumps(diff_to_dict(diff), indent=2))
        else:
            print(format_diff_text(diff))
    except ValueError as e:
        print(f"Error: {e}")


def profile_apply(args, settings: Settings):
    manager = create_runtime_profile_manager(settings)
    try:
        ptype = RuntimeProfileType(args.profile_type)
        if not args.confirm:
            print("Profile apply requires --confirm flag.")
            return
        profile = manager.apply_profile(ptype, confirm=True)
        print(f"Applied profile: {profile.name}")
    except ValueError as e:
        print(f"Error: {e}")


def create_snapshot(args, settings: Settings):
    manager = create_config_snapshot_manager(settings)
    ptype = None
    if args.profile:
        try:
            ptype = RuntimeProfileType(args.profile)
        except ValueError:
            pass

    snapshot = manager.create_snapshot(profile_type=ptype, save=True)
    if args.json:
        print(json.dumps(snapshot_to_dict(snapshot), indent=2))
    else:
        print(format_snapshot_text(snapshot))


def run_diff(args, settings: Settings):
    manager = create_config_snapshot_manager(settings)
    engine = create_config_diff_engine(settings)

    if args.old and args.new:
        old = manager.load_snapshot(args.old)
        new = manager.load_snapshot(args.new)
        if not old or not new:
            print("Snapshot not found.")
            return
        res = engine.diff_snapshots(old, new)
    elif args.current_against:
        old = manager.load_snapshot(args.current_against)
        if not old:
             print("Snapshot not found.")
             return
        current = manager.create_snapshot(save=False)
        res = engine.diff_snapshots(old, current)
    else:
        print("Must specify --old and --new OR --current-against")
        return

    if args.json:
        print(json.dumps(diff_to_dict(res), indent=2))
    else:
        print(format_diff_text(res))


def run_drift(args, settings: Settings):
    manager = create_config_snapshot_manager(settings)
    detector = create_config_drift_detector(settings)

    baseline = None
    if args.baseline:
        baseline = manager.load_snapshot(args.baseline)
        if not baseline:
            print("Baseline snapshot not found.")
            return

    current = manager.create_snapshot(save=False)
    res = detector.detect_drift(current, baseline)

    if args.json:
        print(json.dumps(drift_to_dict(res), indent=2))
    else:
        print(format_drift_text(res))


def run_gate(args, settings: Settings):
    gate = create_config_gate(settings)

    if args.gate_type == "runtime":
        res = gate.runtime_gate()
    elif args.gate_type == "release":
        res = gate.release_gate()
    elif args.gate_type == "scheduler":
        res = gate.scheduler_gate()
    else:
        print(f"Unknown gate type: {args.gate_type}")
        return

    if args.json:
        print(json.dumps(gate_to_dict(res), indent=2))
    else:
        print(f"Gate {res.request.gate_name} Result: {res.decision.value} (Blocked: {res.blocked})")
        if res.warnings:
            print("Warnings:")
            for w in res.warnings:
                print(f" - {w}")


def show_recent(args, settings: Settings):
    manager = create_config_snapshot_manager(settings)
    snapshots = manager.list_snapshots(limit=args.limit)
    if args.json:
        print(json.dumps(snapshots, indent=2))
    else:
        for s in snapshots:
            print(f"- {s['snapshot_id']} ({s['created_at']}) Profile: {s.get('profile_type')} Checksum: {s.get('checksum')}")


def show_config(args, settings: Settings):
    registry = create_config_registry(settings)
    summary = registry.redacted_summary()
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        for k, v in summary.items():
            print(f"{k}: {v}")
