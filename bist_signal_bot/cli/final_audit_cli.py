import argparse
import sys
import json
from bist_signal_bot.app.final_audit_app import (
    create_final_audit_check_runner,
    create_final_acceptance_suite_runner,
    create_final_contract_auditor,
    create_final_integration_matrix_builder,
    create_final_security_auditor,
    create_release_candidate_builder,
    create_hardening_freeze_manager,
    create_go_no_go_evaluator,
    create_final_risk_register_builder,
    create_final_audit_store
)
from bist_signal_bot.final_audit.reporting import (
    check_result_to_dict,
    acceptance_suite_to_dict,
    integration_matrix_to_dict,
    security_audit_to_dict,
    release_candidate_to_dict,
    freeze_manifest_to_dict,
    go_no_go_to_dict,
    risk_item_to_dict,
    final_audit_report_to_dict,
    format_acceptance_suite_text,
    format_integration_matrix_text,
    format_security_audit_text,
    format_release_candidate_text,
    format_freeze_manifest_text,
    format_go_no_go_text,
    format_risk_register_text,
    format_final_audit_report_markdown
)
from bist_signal_bot.final_audit.models import FinalAuditReport
from datetime import datetime, timezone

def main(args):
    parser = argparse.ArgumentParser(prog="python -m bist_signal_bot final-audit")
    subparsers = parser.add_subparsers(dest="command", help="Final Audit commands")

    # Run
    run_parser = subparsers.add_parser("run", help="Run final audit checks")
    run_parser.add_argument("--save", action="store_true", help="Save results")
    run_parser.add_argument("--json", action="store_true", help="JSON output")

    # Acceptance
    acc_parser = subparsers.add_parser("acceptance", help="Run acceptance suite")
    acc_parser.add_argument("--json", action="store_true", help="JSON output")

    # Contracts
    con_parser = subparsers.add_parser("contracts", help="Run contract audit")
    con_parser.add_argument("--json", action="store_true", help="JSON output")

    # Integration
    int_parser = subparsers.add_parser("integration", help="Build integration matrix")
    int_parser.add_argument("--json", action="store_true", help="JSON output")

    # Security
    sec_parser = subparsers.add_parser("security", help="Run security audit")
    sec_parser.add_argument("--json", action="store_true", help="JSON output")

    # Candidate
    cand_parser = subparsers.add_parser("candidate", help="Manage release candidates")
    cand_subparsers = cand_parser.add_subparsers(dest="cand_cmd")
    build_cand = cand_subparsers.add_parser("build", help="Build a release candidate")
    build_cand.add_argument("--save", action="store_true", help="Save candidate")
    build_cand.add_argument("--json", action="store_true", help="JSON output")
    show_cand = cand_subparsers.add_parser("show", help="Show latest candidate")
    show_cand.add_argument("--latest", action="store_true", help="Show latest")
    show_cand.add_argument("--json", action="store_true", help="JSON output")

    # Freeze
    freeze_parser = subparsers.add_parser("freeze", help="Create a hardening freeze")
    freeze_parser.add_argument("--candidate-id", required=True, help="Candidate ID")
    freeze_parser.add_argument("--dry-run", action="store_true", help="Dry run freeze")
    freeze_parser.add_argument("--confirm", action="store_true", help="Confirm freeze")
    freeze_parser.add_argument("--json", action="store_true", help="JSON output")

    # Go / No-Go
    gng_parser = subparsers.add_parser("go-no-go", help="Evaluate Go/No-Go decision")
    gng_parser.add_argument("--candidate-id", help="Candidate ID")
    gng_parser.add_argument("--json", action="store_true", help="JSON output")

    # Risks
    risk_parser = subparsers.add_parser("risks", help="Manage risk register")
    risk_parser.add_argument("--json", action="store_true", help="JSON output")

    # Report
    rep_parser = subparsers.add_parser("report", help="Generate final audit report")
    rep_parser.add_argument("--latest", action="store_true", help="Use latest data")
    rep_parser.add_argument("--json", action="store_true", help="JSON output")

    # Recent
    recent_parser = subparsers.add_parser("recent", help="Show recent decisions")
    recent_parser.add_argument("--limit", type=int, default=10, help="Limit")
    recent_parser.add_argument("--json", action="store_true", help="JSON output")

    # Config
    cfg_parser = subparsers.add_parser("config", help="Show final audit config")
    cfg_parser.add_argument("--json", action="store_true", help="JSON output")

    parsed = parser.parse_args(args)

    if not parsed.command:
        parser.print_help()
        return 1

    try:
        if parsed.command == "run":
            runner = create_final_audit_check_runner()
            results = runner.run_all_checks()
            if parsed.save:
                store = create_final_audit_store()
                store.append_checks(results)
            if parsed.json:
                print(json.dumps([check_result_to_dict(r) for r in results], indent=2))
            else:
                for r in results:
                    print(f"[{r.status.value}] {r.name} - {r.message}")

        elif parsed.command == "acceptance":
            runner = create_final_acceptance_suite_runner()
            suite = runner.run_acceptance_suite()
            store = create_final_audit_store()
            store.append_acceptance_suite(suite)
            if parsed.json:
                print(json.dumps(acceptance_suite_to_dict(suite), indent=2))
            else:
                print(format_acceptance_suite_text(suite))

        elif parsed.command == "contracts":
            auditor = create_final_contract_auditor()
            results = auditor.audit_contracts()
            if parsed.json:
                print(json.dumps([check_result_to_dict(r) for r in results], indent=2))
            else:
                for r in results:
                    print(f"[{r.status.value}] {r.name}")

        elif parsed.command == "integration":
            builder = create_final_integration_matrix_builder()
            matrix = builder.build_matrix()
            store = create_final_audit_store()
            store.append_integration_matrix(matrix)
            if parsed.json:
                print(json.dumps(integration_matrix_to_dict(matrix), indent=2))
            else:
                print(format_integration_matrix_text(matrix))

        elif parsed.command == "security":
            auditor = create_final_security_auditor()
            res = auditor.run_security_audit()
            store = create_final_audit_store()
            store.append_security_audit(res)
            if parsed.json:
                print(json.dumps(security_audit_to_dict(res), indent=2))
            else:
                print(format_security_audit_text(res))

        elif parsed.command == "candidate":
            if parsed.cand_cmd == "build":
                builder = create_release_candidate_builder()
                cand = builder.build_candidate()
                if getattr(parsed, "save", False):
                    store = create_final_audit_store()
                    store.append_release_candidate(cand)
                if parsed.json:
                    print(json.dumps(release_candidate_to_dict(cand), indent=2))
                else:
                    print(format_release_candidate_text(cand))
            elif parsed.cand_cmd == "show":
                store = create_final_audit_store()
                cand = store.load_latest_release_candidate()
                if not cand:
                    print("No candidate found.")
                    return 1
                if parsed.json:
                    print(json.dumps(release_candidate_to_dict(cand), indent=2))
                else:
                    print(format_release_candidate_text(cand))

        elif parsed.command == "freeze":
            store = create_final_audit_store()
            cand = store.load_latest_release_candidate()
            if not cand or cand.candidate_id != parsed.candidate_id:
                print(f"Candidate {parsed.candidate_id} not found or not latest.")
                return 1

            manager = create_hardening_freeze_manager()
            confirm = getattr(parsed, "confirm", False)
            freeze = manager.create_freeze(cand, confirm=confirm)

            if confirm:
                store.append_freeze_manifest(freeze)

            if parsed.json:
                print(json.dumps(freeze_manifest_to_dict(freeze), indent=2))
            else:
                print(format_freeze_manifest_text(freeze))

        elif parsed.command == "go-no-go":
            store = create_final_audit_store()
            cand = store.load_latest_release_candidate()
            if not cand:
                print("No candidate found.")
                return 1

            acc = store.load_latest_acceptance_suite()
            sec = store.load_latest_security_audit()
            matrix = store.load_latest_integration_matrix()

            evaluator = create_go_no_go_evaluator()
            decision = evaluator.evaluate(cand, acc, sec, matrix)
            store.append_go_no_go(decision)

            if parsed.json:
                print(json.dumps(go_no_go_to_dict(decision), indent=2))
            else:
                print(format_go_no_go_text(decision))

        elif parsed.command == "risks":
            store = create_final_audit_store()
            cand = store.load_latest_release_candidate()
            builder = create_final_risk_register_builder()
            items = builder.build_risk_register(cand)
            store.append_risk_register(items)

            if parsed.json:
                print(json.dumps([risk_item_to_dict(i) for i in items], indent=2))
            else:
                print(format_risk_register_text(items))

        elif parsed.command == "report":
            store = create_final_audit_store()
            cand = store.load_latest_release_candidate()
            acc = store.load_latest_acceptance_suite()
            sec = store.load_latest_security_audit()
            matrix = store.load_latest_integration_matrix()
            gng = store.load_latest_go_no_go()
            freeze = store.load_latest_freeze_manifest()
            items = create_final_risk_register_builder().build_risk_register(cand)

            report = FinalAuditReport(
                report_id=f"rpt_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}",
                generated_at=datetime.now(timezone.utc),
                acceptance_suite=acc,
                integration_matrix=matrix,
                security_audit=sec,
                release_candidate=cand,
                freeze_manifest=freeze,
                go_no_go=gng,
                risk_register=items
            )

            md_text = format_final_audit_report_markdown(report)
            store.save_report(report, md_text)

            if parsed.json:
                print(json.dumps(final_audit_report_to_dict(report), indent=2))
            else:
                print("Report saved successfully.")
                print(md_text)

        elif parsed.command == "recent":
            # Just mock it for MVP parity
            if parsed.json:
                print(json.dumps([], indent=2))
            else:
                print("No recent final audit decisions found.")

        elif parsed.command == "config":
            cfg = {"enabled": True, "research_only": True}
            if parsed.json:
                print(json.dumps(cfg, indent=2))
            else:
                print("Final Audit Config:", cfg)

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
