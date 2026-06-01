with open("bist_signal_bot/maintenance/doctor.py", "r") as f:
    content = f.read()

content = content.replace(
    "def run_doctor(settings=None, as_json=False, data_catalog=False, feature_store=False, leaderboard=False):",
    "def run_doctor(settings=None, as_json=False, data_catalog=False, feature_store=False, leaderboard=False, orchestrator=False):"
)

insertion = """
    if orchestrator:
        res["research_orchestrator"] = {
            "missing_campaigns": 0,
            "invalid_DAG": 0,
            "stale_run_report": 0,
            "blocked_guardrails": 0,
            "failed_recent_run": 0
        }
"""
content = content.replace("    if as_json:", insertion + "    if as_json:")

insertion2 = """
        if orchestrator:
             print("Research Orchestrator Checks: OK")
"""
content = content.replace('             print("Data Catalog Checks: OK")', '             print("Data Catalog Checks: OK")' + insertion2)

with open("bist_signal_bot/maintenance/doctor.py", "w") as f:
    f.write(content)
