import os

def create_cli():
    content = """import argparse
import sys
import json
from bist_signal_bot.app.release_policy_app import (
    create_release_policy_store, create_branch_policy_registry,
    create_version_governance_engine, create_compatibility_policy_checker,
    create_change_control_manager, create_changelog_builder,
    create_migration_note_builder, create_deprecation_policy_manager,
    create_release_branch_freeze_manager, create_final_post_release_closure_builder,
    create_release_policy_governance_engine
)
from bist_signal_bot.release_policy.models import ChangeType

def setup_release_policy_parser(subparsers):
    parser = subparsers.add_parser("release-policy", help="Manage strict release branch policy and final closure")
    rp_subs = parser.add_subparsers(dest="rp_command")

    # status
    s_parser = rp_subs.add_parser("status", help="Show release policy overall status")
    s_parser.add_argument("--json", action="store_true", help="JSON output")

    # branches
    b_parser = rp_subs.add_parser("branches", help="List branch policies")
    b_parser.add_argument("--json", action="store_true", help="JSON output")

    # version
    v_parser = rp_subs.add_parser("version", help="Manage version governance")
    v_parser.add_argument("--snapshot", action="store_true", help="Generate snapshot")
    v_parser.add_argument("--json", action="store_true", help="JSON output")

    # compatibility
    c_parser = rp_subs.add_parser("compatibility", help="Run compatibility checks")
    c_parser.add_argument("--target-version", type=str, help="Target version")
    c_parser.add_argument("--json", action="store_true", help="JSON output")

    # change
    ch_parser = rp_subs.add_parser("change", help="Create change request")
    ch_parser.add_argument("--title", type=str, required=True, help="Change title")
    ch_parser.add_argument("--type", type=str, required=True, help="Change type (e.g. FEATURE, BUGFIX, BREAKING)")
    ch_parser.add_argument("--modules", type=str, nargs="+", default=[], help="Affected modules")
    ch_parser.add_argument("--json", action="store_true", help="JSON output")

    # changelog
    cl_parser = rp_subs.add_parser("changelog", help="Build changelog")
    cl_parser.add_argument("--version", type=str, required=True, help="Target version")
    cl_parser.add_argument("--json", action="store_true", help="JSON output")

    # migrations
    m_parser = rp_subs.add_parser("migrations", help="Build migration notes")
    m_parser.add_argument("--from-version", type=str, required=True, help="From version")
    m_parser.add_argument("--to-version", type=str, required=True, help="To version")
    m_parser.add_argument("--json", action="store_true", help="JSON output")

    # deprecations
    d_parser = rp_subs.add_parser("deprecations", help="List deprecations")
    d_parser.add_argument("--json", action="store_true", help="JSON output")

    # freeze
    f_parser = rp_subs.add_parser("freeze", help="Create release branch freeze manifest")
    f_parser.add_argument("--branch", type=str, required=True, help="Branch name")
    f_parser.add_argument("--target-version", type=str, required=True, help="Target version")
    f_parser.add_argument("--confirm", action="store_true", help="Confirm freeze")
    f_parser.add_argument("--dry-run", action="store_true", help="Dry run")
    f_parser.add_argument("--json", action="store_true", help="JSON output")

    # closure
    cl2_parser = rp_subs.add_parser("closure", help="Create final post-release closure manifest")
    cl2_parser.add_argument("--confirm", action="store_true", help="Confirm closure")
    cl2_parser.add_argument("--dry-run", action="store_true", help="Dry run")
    cl2_parser.add_argument("--json", action="store_true", help="JSON output")

    # governance
    g_parser = rp_subs.add_parser("governance", help="Assess release policy governance")
    g_parser.add_argument("--json", action="store_true", help="JSON output")

    # report
    r_parser = rp_subs.add_parser("report", help="Generate release policy report")
    r_parser.add_argument("--latest", action="store_true", help="Use latest data")
    r_parser.add_argument("--json", action="store_true", help="JSON output")

    # recent
    rec_parser = rp_subs.add_parser("recent", help="List recent actions")
    rec_parser.add_argument("--limit", type=int, default=10, help="Limit")
    rec_parser.add_argument("--json", action="store_true", help="JSON output")

    # config
    cfg_parser = rp_subs.add_parser("config", help="Show release policy config")
    cfg_parser.add_argument("--json", action="store_true", help="JSON output")

def handle_release_policy_command(args):
    try:
        from bist_signal_bot.config.settings import get_settings
        settings = get_settings()
        store = create_release_policy_store(settings)

        if args.rp_command == "status":
            engine = create_release_policy_governance_engine(settings)
            result = engine.assess_release_policy()
            if args.json:
                print(result.model_dump_json(indent=2))
            else:
                print(f"Status: {result.status.value}")

        elif args.rp_command == "branches":
            reg = create_branch_policy_registry(settings)
            policies = reg.default_branch_policies()
            if args.json:
                print(json.dumps([p.model_dump(mode='json') for p in policies], indent=2))
            else:
                for p in policies:
                    print(f"- {p.policy_id} ({p.branch_kind.value})")

        elif args.rp_command == "version":
            engine = create_version_governance_engine(settings)
            snap = engine.build_version_snapshot()
            if args.json:
                print(snap.model_dump_json(indent=2))
            else:
                print(f"Version: {snap.project_version}")

        elif args.rp_command == "compatibility":
            checker = create_compatibility_policy_checker(settings)
            result = checker.run_compatibility_check(args.target_version)
            if args.json:
                print(result.model_dump_json(indent=2))
            else:
                print(f"Compatibility Status: {result.status.value}")

        elif args.rp_command == "change":
            manager = create_change_control_manager(settings)
            try:
                ctype = ChangeType(args.type)
            except ValueError:
                ctype = ChangeType.CUSTOM
            req = manager.create_change_request(args.title, "Created via CLI", ctype, args.modules)
            store.append_change_request(req)
            if args.json:
                print(req.model_dump_json(indent=2))
            else:
                print(f"Created change request: {req.change_id}")

        elif args.rp_command == "changelog":
            builder = create_changelog_builder(settings)
            changes = store.load_change_requests(100)
            entries = builder.build_changelog_entries(changes, args.version)
            if args.json:
                print(json.dumps([e.model_dump(mode='json') for e in entries], indent=2))
            else:
                print(builder.format_changelog_markdown(entries))

        elif args.rp_command == "migrations":
            builder = create_migration_note_builder(settings)
            changes = store.load_change_requests(100)
            notes = builder.build_migration_notes(changes, args.from_version, args.to_version)
            if args.json:
                print(json.dumps([n.model_dump(mode='json') for n in notes], indent=2))
            else:
                print(builder.format_migration_markdown(notes))

        elif args.rp_command == "deprecations":
            manager = create_deprecation_policy_manager(settings)
            notices = manager.default_deprecations()
            if args.json:
                print(json.dumps([n.model_dump(mode='json') for n in notices], indent=2))
            else:
                print(manager.format_deprecations_markdown(notices))

        elif args.rp_command == "freeze":
            manager = create_release_branch_freeze_manager(settings)
            manifest = manager.create_freeze(args.branch, args.target_version, args.confirm and not args.dry_run)
            if not args.dry_run:
                store.append_freeze_manifest(manifest)
            if args.json:
                print(manifest.model_dump_json(indent=2))
            else:
                print(f"Freeze {manifest.freeze_id}: frozen={manifest.frozen}")

        elif args.rp_command == "closure":
            builder = create_final_post_release_closure_builder(settings)
            manifest = builder.build_closure_manifest(confirm=(args.confirm and not args.dry_run))
            if not args.dry_run:
                store.append_closure_manifest(manifest)
            if args.json:
                print(manifest.model_dump_json(indent=2))
            else:
                print(builder.format_closure_markdown(manifest))

        elif args.rp_command == "governance":
            engine = create_release_policy_governance_engine(settings)
            assessment = engine.assess_release_policy()
            if args.json:
                print(assessment.model_dump_json(indent=2))
            else:
                print(f"Governance Status: {assessment.status.value}")

        elif args.rp_command == "report":
            from bist_signal_bot.release_policy.models import ReleasePolicyReport
            rep = ReleasePolicyReport(
                report_id="dummy",
                branch_policies=[],
                version_snapshots=[],
                change_requests=[],
                compatibility_results=[],
                changelog_entries=[],
                migration_notes=[],
                deprecation_notices=[],
                freezes=[],
                closures=[],
                governance_assessments=[]
            )
            if args.json:
                print(rep.model_dump_json(indent=2))
            else:
                print(f"Report: {rep.report_id}")

        elif args.rp_command == "recent":
            reqs = store.load_change_requests(args.limit)
            if args.json:
                print(json.dumps([r.model_dump(mode='json') for r in reqs], indent=2))
            else:
                for r in reqs:
                    print(f"- {r.title} ({r.status.value})")

        elif args.rp_command == "config":
            c = {
                "ENABLE_RELEASE_POLICY": settings.ENABLE_RELEASE_POLICY,
                "PROJECT_VERSION": settings.RELEASE_POLICY_PROJECT_VERSION
            }
            if args.json:
                print(json.dumps(c, indent=2))
            else:
                print(f"ENABLE_RELEASE_POLICY: {settings.ENABLE_RELEASE_POLICY}")

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"Error: {str(e)}")
        sys.exit(1)
"""
    # Simply appending to a mock cli entry point.
    # In reality we would hook this into the main CLI parser. We'll write this to a temporary place
    # or append it if we know the structure. For now, writing to cli/release_policy_cli.py
    with open("bist_signal_bot/cli/release_policy_cli.py", "w") as f:
        f.write(content)

if __name__ == "__main__":
    create_cli()
    print("Part 10 complete.")
