# File to manage command routing (if existing commands.py is too big to patch easily)
from bist_signal_bot.cli.config_registry_commands import (
    list_records,
    show_record,
    validate_config,
    show_flags,
    show_profiles,
    profile_preview,
    profile_apply,
    create_snapshot,
    run_diff,
    run_drift,
    run_gate,
    show_recent,
    show_config
)

def run_config_registry_command(args, settings):
    cmd = args.config_command
    if cmd == "list":
        list_records(args, settings)
    elif cmd == "show":
        show_record(args, settings)
    elif cmd == "validate":
        validate_config(args, settings)
    elif cmd == "flags":
        show_flags(args, settings)
    elif cmd == "profiles":
        show_profiles(args, settings)
    elif cmd == "profile-preview":
        profile_preview(args, settings)
    elif cmd == "profile-apply":
        profile_apply(args, settings)
    elif cmd == "snapshot":
        create_snapshot(args, settings)
    elif cmd == "diff":
        run_diff(args, settings)
    elif cmd == "drift":
        run_drift(args, settings)
    elif cmd == "gate":
        run_gate(args, settings)
    elif cmd == "recent":
        show_recent(args, settings)
    elif cmd == "config":
        show_config(args, settings)
