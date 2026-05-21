import argparse
import sys
import json
from pathlib import Path
from bist_signal_bot.app.maintenance_app import (
    create_backup_manager, create_restore_manager, create_cleanup_manager,
    create_migration_manager, create_maintenance_doctor, create_maintenance_store
)
from bist_signal_bot.maintenance.models import BackupRequest, RestoreRequest, BackupScope, BackupFormat, RetentionTarget
from bist_signal_bot.maintenance.retention import RetentionPolicyManager

def handle_backup_create(args):
    mgr = create_backup_manager()
    scopes = [BackupScope(s) for s in args.scope] if args.scope else [BackupScope.ALL_SAFE]
    req = BackupRequest(
        scopes=scopes,
        backup_format=BackupFormat(args.format),
        dry_run=args.dry_run,
        verify_after_create=args.verify
    )
    res = mgr.create_backup(req)
    if not args.dry_run:
        store = create_maintenance_store()
        store.save_backup_result(res)

    if args.json:
        print(res.model_dump_json(indent=2))
    else:
        print(f"Backup Result: {res.status.value}")
        print(f"Included Files: {res.manifest.included_files}")
        if res.output_path:
             print(f"Path: {res.output_path}")

def handle_restore(args):
    mgr = create_restore_manager()
    scopes = [BackupScope(s) for s in args.scope] if getattr(args, 'scope', None) else [BackupScope.ALL_SAFE]
    req = RestoreRequest(
        backup_path=args.backup,
        scopes=scopes,
        dry_run=not args.confirm
    )

    try:
        res = mgr.restore(req, confirm=args.confirm)
        if not req.dry_run:
             store = create_maintenance_store()
             store.save_restore_result(res)

        if args.json:
            print(res.model_dump_json(indent=2))
        else:
            print(f"Restore Result: {res.status.value}")
            print(f"Restored: {res.restored_files}, Skipped: {res.skipped_files}, Blocked: {res.blocked_files}")
    except Exception as e:
        print(f"Restore failed: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Maintenance Operations")
    subparsers = parser.add_subparsers(dest="command")

    bc = subparsers.add_parser("backup-create")
    bc.add_argument("--scope", nargs="+")
    bc.add_argument("--format", default="ZIP")
    bc.add_argument("--verify", action="store_true")
    bc.add_argument("--dry-run", action="store_true")
    bc.add_argument("--json", action="store_true")

    r = subparsers.add_parser("restore")
    r.add_argument("--backup", required=True)
    r.add_argument("--scope", nargs="+")
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--confirm", action="store_true")
    r.add_argument("--json", action="store_true")

    # Add other parsers...
    args, _ = parser.parse_known_args()

    if args.command == "backup-create":
        handle_backup_create(args)
    elif args.command == "restore":
        handle_restore(args)
    else:
        # MVP: Default to doctor
        doc = create_maintenance_doctor()
        res = doc.run_doctor()
        if getattr(args, 'json', False):
             print(res.model_dump_json(indent=2))
        else:
             print(f"Doctor Status: {res.status.value}")
             print(f"Missing Dirs: {len(res.missing_dirs)}")
             print(f"Corrupted: {len(res.corrupted_files)}")

if __name__ == "__main__":
    main()
