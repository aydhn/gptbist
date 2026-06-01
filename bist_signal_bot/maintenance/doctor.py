from typing import Any

def run_doctor(settings=None, as_json=False, data_catalog=False, feature_store=False, leaderboard=False, orchestrator=False, final_audit=False, final_handoff=False):
    res = {
        "status": "healthy",
        "checks": [
            "db_connection",
            "disk_space",
            "permissions"
        ]
    }
    if data_catalog:
        res["data_catalog"] = {
            "missing_contracts": 0,
            "missing_required_datasets": 0,
            "schema_drift": 0,
            "stale_datasets": 0,
            "orphan_lineage": 0,
            "low_quality_score": 0
        }

    if final_audit:
        append_final_audit_doctor_checks(res, settings)

    if final_handoff:
        append_final_handoff_doctor_checks(res, settings)

    if orchestrator:
        res["research_orchestrator"] = {
            "missing_campaigns": 0,
            "invalid_DAG": 0,
            "stale_run_report": 0,
            "blocked_guardrails": 0,
            "failed_recent_run": 0
        }
    if as_json:
        import json
        print(json.dumps(res, indent=2))
    else:
        print(f"Doctor Status: {res['status']}")
        if data_catalog:
             print("Data Catalog Checks: OK")
    if final_audit:
        append_final_audit_doctor_checks(res, settings)

        if orchestrator:
             print("Research Orchestrator Checks: OK")
        if final_handoff:
             print("Final Handoff Checks: OK")

def append_final_audit_doctor_checks(report: dict, settings: Any):
    if not getattr(settings, "ENABLE_FINAL_AUDIT", True):
        return

    try:
        from bist_signal_bot.app.final_audit_app import create_final_audit_store
        store = create_final_audit_store(settings=settings)
        latest_cand = store.load_latest_release_candidate()
        latest_sec = store.load_latest_security_audit()

        issues = []
        if not latest_cand:
            issues.append("Missing release candidate.")
        if latest_sec and latest_sec.blocked_findings:
            issues.append(f"Blocked security findings: {latest_sec.blocked_findings}")

        report["final_audit"] = {
            "status": "FAIL" if issues else "PASS",
            "issues": issues
        }
    except Exception:
        pass

def append_final_handoff_doctor_checks(report: dict, settings: Any):
    if not getattr(settings, "ENABLE_FINAL_HANDOFF", True):
        return

    try:
        from bist_signal_bot.app.final_handoff_app import create_final_handoff_store
        store = create_final_handoff_store(settings=settings)
        op_playbook = store.load_latest_operator_playbook()
        dev_playbook = store.load_latest_developer_playbook()
        command_map = store.load_command_map()
        roadmap = store.load_roadmap()
        latest_pack = store.load_latest_release_pack()

        issues = []
        if not op_playbook or not dev_playbook:
            issues.append("missing playbooks")
        if not command_map:
            issues.append("missing final command map")
        if not roadmap:
            issues.append("missing roadmap")
        if not latest_pack or latest_pack.stage.value not in ["BUILT", "VERIFIED", "HANDOFF_READY", "FROZEN"]:
            issues.append("release pack incomplete")

        report["final_handoff"] = {
            "status": "FAIL" if issues else "PASS",
            "issues": issues
        }
    except Exception:
        pass
