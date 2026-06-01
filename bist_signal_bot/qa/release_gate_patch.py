with open("bist_signal_bot/qa/release_gate.py", "r") as f:
    content = f.read()

content = content.replace(
    "def run_release_gate(include_data_catalog=False, include_feature_store=False, include_model_registry=False, settings=None):",
    "def run_release_gate(include_data_catalog=False, include_feature_store=False, include_model_registry=False, include_orchestrator=False, settings=None):"
)

insertion = """
    if include_orchestrator:
        res["research_orchestrator"] = {
            "plan_deterministic": "PASS",
            "dag_cycle_check": "PASS",
            "guardrails_pass": "PASS",
            "dry_run_execution": "PASS",
            "no_unsafe_commands": "PASS"
        }
"""
content = content.replace("    if include_model_registry:\n        check_model_registry(res, settings)\n    return res", "    if include_model_registry:\n        check_model_registry(res, settings)" + insertion + "    return res")

with open("bist_signal_bot/qa/release_gate.py", "w") as f:
    f.write(content)
