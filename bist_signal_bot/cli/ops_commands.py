import json
import sys
from pathlib import Path

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.app.ops_app import (
    create_ops_observability_engine,
    create_store_integrity_checker,
    create_staleness_checker,
    create_ops_incident_manager,
    create_ops_runbook_registry,
    create_backup_manager,
    create_restore_planner,
    create_retention_policy_engine,
    create_migration_checker,
    create_operational_readiness_gate,
    create_ops_store,
)
from bist_signal_bot.ops.models import OpsIncidentType, BackupScope, OpsReport
from bist_signal_bot.ops.reporting import (
    ops_report_to_dict,
    format_ops_report_markdown,
    health_snapshot_to_dict,
    store_integrity_to_dict,
    staleness_finding_to_dict,
    incident_to_dict,
    runbook_to_dict,
    backup_manifest_to_dict,
    restore_plan_to_dict,
    retention_finding_to_dict,
    migration_check_to_dict,
    readiness_to_dict,
    format_health_snapshot_text,
    format_store_integrity_text,
    format_incident_text,
    format_runbook_text,
    format_backup_manifest_text,
    format_readiness_text,
)
import datetime


def add_ops_subparsers(subparsers):
    ops_parser = subparsers.add_parser("ops", help="Local Ops / Reliability commands")
    ops_sub = ops_parser.add_subparsers(dest="ops_command", help="Ops subcommands")

    p_status = ops_sub.add_parser("status", help="Show ops health snapshot")
    p_status.add_argument("--json", action="store_true", help="JSON output")

    p_doctor = ops_sub.add_parser("doctor", help="Run ops doctor (checks)")
    p_doctor.add_argument("--json", action="store_true", help="JSON output")

    p_store = ops_sub.add_parser("store-check", help="Check store integrity")
    p_store.add_argument("--json", action="store_true", help="JSON output")

    p_stale = ops_sub.add_parser("staleness", help="Check data staleness")
    p_stale.add_argument("--module", help="Specific module to check")
    p_stale.add_argument("--json", action="store_true", help="JSON output")

    p_inc = ops_sub.add_parser("incident", help="Incident management")
    inc_sub = p_inc.add_subparsers(dest="inc_command")

    p_inc_list = inc_sub.add_parser("list")
    p_inc_list.add_argument("--json", action="store_true")

    p_inc_show = inc_sub.add_parser("show")
    p_inc_show.add_argument("id")
    p_inc_show.add_argument("--json", action="store_true")

    p_inc_create = inc_sub.add_parser("create")
    p_inc_create.add_argument("--type", required=True, help="Incident Type (e.g. STALE_DATA)")
    p_inc_create.add_argument("--title", required=True)
    p_inc_create.add_argument("--description", required=True)
    p_inc_create.add_argument("--save", action="store_true")

    p_inc_res = inc_sub.add_parser("resolve")
    p_inc_res.add_argument("id")
    p_inc_res.add_argument("--note", required=True)
    p_inc_res.add_argument("--confirm", action="store_true")

    p_rb = ops_sub.add_parser("runbook", help="Runbook management")
    rb_sub = p_rb.add_subparsers(dest="rb_command")

    p_rb_list = rb_sub.add_parser("list")
    p_rb_show = rb_sub.add_parser("show")
    p_rb_show.add_argument("type")

    p_rb_for = rb_sub.add_parser("for-incident")
    p_rb_for.add_argument("id")
    p_rb_for.add_argument("--json", action="store_true")

    p_bkp = ops_sub.add_parser("backup", help="Backup management")
    p_bkp.add_argument("--dry-run", action="store_true")
    p_bkp.add_argument("--scope", nargs="+", help="Scopes (e.g. DATA CONFIG)")
    p_bkp.add_argument("--confirm", action="store_true")
    p_bkp.add_argument("--json", action="store_true")

    p_rst = ops_sub.add_parser("restore", help="Restore management")
    p_rst.add_argument("--backup-path", required=True)
    p_rst.add_argument("--target")
    p_rst.add_argument("--dry-run", action="store_true")
    p_rst.add_argument("--confirm", action="store_true")
    p_rst.add_argument("--json", action="store_true")

    p_ret = ops_sub.add_parser("retention", help="Retention management")
    p_ret.add_argument("--dry-run", action="store_true")
    p_ret.add_argument("--apply", action="store_true")
    p_ret.add_argument("--confirm", action="store_true")
    p_ret.add_argument("--json", action="store_true")

    p_mig = ops_sub.add_parser("migration-check", help="Check schema migrations")
    p_mig.add_argument("--json", action="store_true")

    p_rdy = ops_sub.add_parser("readiness", help="Operational readiness")
    p_rdy.add_argument("--json", action="store_true")

    p_rep = ops_sub.add_parser("report", help="Ops report")
    p_rep.add_argument("--latest", action="store_true")
    p_rep.add_argument("--json", action="store_true")

    p_rec = ops_sub.add_parser("recent", help="Recent ops activity")
    p_rec.add_argument("--limit", type=int, default=10)
    p_rec.add_argument("--json", action="store_true")

    p_cfg = ops_sub.add_parser("config", help="Show ops config")
    p_cfg.add_argument("--json", action="store_true")


def _handle_status(args, s):
    obs = create_ops_observability_engine(s)
    snap = obs.build_health_snapshot()
    if getattr(args, "json", False):
        print(json.dumps(health_snapshot_to_dict(snap), indent=2))
    else:
        print(format_health_snapshot_text(snap))


def _handle_doctor(args, s):
    obs = create_ops_observability_engine(s)
    snap = obs.build_health_snapshot()
    store = create_store_integrity_checker(s).check_store_integrity()
    if getattr(args, "json", False):
        print(
            json.dumps(
                {
                    "health": health_snapshot_to_dict(snap),
                    "store_integrity": store_integrity_to_dict(store),
                },
                indent=2,
            )
        )
    else:
        print("Ops Doctor Summary")
        print("=" * 20)
        print(format_health_snapshot_text(snap))
        print("-" * 20)
        print(format_store_integrity_text(store))


def _handle_store_check(args, s):
    chk = create_store_integrity_checker(s)
    res = chk.check_store_integrity()
    if getattr(args, "json", False):
        print(json.dumps(store_integrity_to_dict(res), indent=2))
    else:
        print(format_store_integrity_text(res))


def _handle_staleness(args, s):
    chk = create_staleness_checker(s)
    if hasattr(args, "module") and args.module:
        from bist_signal_bot.storage.paths import get_data_dir

        p = get_data_dir() / args.module
        f = chk.check_module(args.module, p, chk.threshold_for_module(args.module))
        res = [f]
    else:
        res = chk.check_all()
    if getattr(args, "json", False):
        print(json.dumps([staleness_finding_to_dict(r) for r in res], indent=2))
    else:
        for r in res:
            print(f"Module: {r.module_name} | Status: {r.status.value} | Message: {r.message}")


def _handle_incident(args, s):
    mgr = create_ops_incident_manager(s)
    if args.inc_command == "list":
        incs = mgr.list_incidents()
        if getattr(args, "json", False):
            print(json.dumps([incident_to_dict(i) for i in incs], indent=2))
        else:
            for i in incs:
                print(format_incident_text(i))
                print("---")
    elif args.inc_command == "show":
        inc = mgr.get_incident(args.id)
        if not inc:
            print(f"Incident {args.id} not found.")
            sys.exit(1)
        if getattr(args, "json", False):
            print(json.dumps(incident_to_dict(inc), indent=2))
        else:
            print(format_incident_text(inc))
    elif args.inc_command == "create":
        inc = mgr.create_incident(
            incident_type=OpsIncidentType(args.type),
            title=args.title,
            description=args.description,
            save=args.save,
        )
        print(f"Created Incident: {inc.incident_id}")
    elif args.inc_command == "resolve":
        try:
            inc = mgr.resolve_incident(args.id, args.note, confirm=args.confirm)
            print(f"Resolved Incident: {inc.incident_id}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)


def _handle_runbook(args, s):
    reg = create_ops_runbook_registry(s)
    if args.rb_command == "list":
        for rb in reg.default_runbooks():
            print(f"{rb.runbook_type.value}: {rb.title}")
    elif args.rb_command == "show":
        rb = reg.get_runbook(args.type)
        if rb:
            print(format_runbook_text(rb))
    elif args.rb_command == "for-incident":
        mgr = create_ops_incident_manager(s)
        inc = mgr.get_incident(args.id)
        if inc:
            rb = reg.runbook_for_incident(inc)
            if getattr(args, "json", False):
                print(json.dumps(runbook_to_dict(rb), indent=2))
            else:
                print(format_runbook_text(rb))


def _handle_backup(args, s):
    mgr = create_backup_manager(s)
    scopes = (
        [BackupScope(sc.upper()) for sc in args.scope]
        if getattr(args, "scope", None)
        else [BackupScope.DATA]
    )
    manifest = mgr.create_backup(
        scopes=scopes,
        confirm=not getattr(args, "dry_run", False) and getattr(args, "confirm", False),
    )
    if getattr(args, "json", False):
        print(json.dumps(backup_manifest_to_dict(manifest), indent=2))
    else:
        print(format_backup_manifest_text(manifest))


def _handle_restore(args, s):
    planner = create_restore_planner(s)
    plan = planner.plan_restore(
        Path(args.backup_path),
        Path(args.target) if getattr(args, "target", None) else None,
        dry_run=getattr(args, "dry_run", False),
    )
    if not getattr(args, "dry_run", False) and getattr(args, "confirm", False):
        plan = planner.execute_restore(plan, confirm=True)
    if getattr(args, "json", False):
        print(json.dumps(restore_plan_to_dict(plan), indent=2))
    else:
        for ln in planner.summarize_restore_plan(plan):
            print(ln)


def _handle_retention(args, s):
    eng = create_retention_policy_engine(s)
    findings = eng.analyze_retention(dry_run=not getattr(args, "apply", False))
    if getattr(args, "apply", False) and getattr(args, "confirm", False):
        findings = eng.apply_retention(eng.archive_candidates(findings), confirm=True)
    if getattr(args, "json", False):
        print(json.dumps([retention_finding_to_dict(f) for f in findings], indent=2))
    else:
        print(f"Found {len(findings)} retention candidates.")


def _handle_migration_check(args, s):
    chk = create_migration_checker(s)
    res = chk.check_migrations()
    if getattr(args, "json", False):
        print(json.dumps(migration_check_to_dict(res), indent=2))
    else:
        print(f"Migration Status: {res.status.value}")
        print(f"Incompatible items: {res.incompatible_items}")


def _handle_readiness(args, s):
    gate = create_operational_readiness_gate(s)
    res = gate.evaluate()
    if getattr(args, "json", False):
        print(json.dumps(readiness_to_dict(res), indent=2))
    else:
        print(format_readiness_text(res))


def _handle_report(args, s):
    gate = create_operational_readiness_gate(s)
    rdy = gate.evaluate()
    now = datetime.datetime.now()
    rep = OpsReport(
        report_id=f"rep_{now.strftime('%Y%m%d%H%M%S')}",
        generated_at=now,
        health_snapshot=rdy.health_snapshot,
        store_integrity=rdy.store_integrity,
        readiness=rdy,
    )
    if getattr(args, "json", False):
        print(json.dumps(ops_report_to_dict(rep), indent=2))
    else:
        print(format_ops_report_markdown(rep))


def _handle_recent(args, s):
    store = create_ops_store(s)
    incs = store.load_incidents(limit=getattr(args, "limit", 10))
    if getattr(args, "json", False):
        print(json.dumps([incident_to_dict(i) for i in incs], indent=2))
    else:
        for i in incs:
            print(format_incident_text(i))


def _handle_config(args, s):
    keys = [k for k in s.model_dump().keys() if k.startswith("OPS_")]
    cfg = {k: getattr(s, k) for k in keys}
    if getattr(args, "json", False):
        print(json.dumps(cfg, indent=2))
    else:
        for k, v in cfg.items():
            print(f"{k}: {v}")


def handle_ops_command(args, settings=None):
    s = settings or Settings()

    handlers = {
        "status": _handle_status,
        "doctor": _handle_doctor,
        "store-check": _handle_store_check,
        "staleness": _handle_staleness,
        "incident": _handle_incident,
        "runbook": _handle_runbook,
        "backup": _handle_backup,
        "restore": _handle_restore,
        "retention": _handle_retention,
        "migration-check": _handle_migration_check,
        "readiness": _handle_readiness,
        "report": _handle_report,
        "recent": _handle_recent,
        "config": _handle_config,
    }

    handler = handlers.get(args.ops_command)
    if handler:
        handler(args, s)
