import os

# QA Release Gate
path = "bist_signal_bot/qa/release_gate.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "from bist_signal_bot.app.model_registry_app" not in content:
        imports = "from bist_signal_bot.app.model_registry_app import create_local_model_registry, create_model_governance_engine\nfrom bist_signal_bot.model_registry.models import ModelGovernanceStatus\n"
        content = imports + content

        hook = """
    def check_model_registry(self, report: dict[str, Any]) -> None:
        if not getattr(self.settings, "QA_INCLUDE_MODEL_REGISTRY", True):
            return

        try:
            reg = create_local_model_registry(self.settings)
            gov = create_model_governance_engine(self.settings)

            models = reg.list_models()
            report["model_registry"] = {"total_models": len(models), "issues": []}

            for m in models:
                assessment = gov.assess_model(m.model_id)
                if getattr(self.settings, "QA_MODEL_REGISTRY_FAIL_ON_BLOCKED_GOVERNANCE", True) and assessment.status == ModelGovernanceStatus.BLOCKED:
                    report["model_registry"]["issues"].append(f"Model {m.model_id} is BLOCKED in governance")
                    self.fail_gate(f"Model Registry: Model {m.model_id} is BLOCKED")

                if getattr(self.settings, "QA_MODEL_REGISTRY_FAIL_ON_MISSING_CARD", False) and assessment.model_card_status != ModelGovernanceStatus.PASS:
                    report["model_registry"]["issues"].append(f"Model {m.model_id} is missing model card")
                    self.fail_gate(f"Model Registry: Model {m.model_id} is missing model card")

        except Exception as e:
            self.logger.warning(f"Failed to check model registry in QA: {e}")
            report["model_registry"] = {"error": str(e)}
"""
        idx = content.find("class QAReleaseGate:")
        if idx != -1:
            content = content.replace("class QAReleaseGate:", "class QAReleaseGate:" + hook)

        # Hook into evaluate method
        eval_idx = content.find("def evaluate(")
        if eval_idx != -1:
            check_hook = "\n        self.check_model_registry(report)\n"
            eval_body_idx = content.find("return report", eval_idx)
            if eval_body_idx != -1:
                content = content[:eval_body_idx] + check_hook + content[eval_body_idx:]

    with open(path, "w") as f:
        f.write(content)

# Ops Store Checks
path = "bist_signal_bot/ops/store_checks.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "check_model_registry_dirs" not in content:
        hook = """
    def check_model_registry_dirs(self) -> dict[str, Any]:
        if not getattr(self.settings, "ENABLE_MODEL_REGISTRY", False):
            return {"status": "SKIPPED"}

        try:
            from bist_signal_bot.storage.paths import get_model_registry_dir
            base = get_model_registry_dir(self.settings)
            dirs = ["models", "experiments", "artifacts", "cards", "validation", "calibration", "promotion", "drift", "lineage", "governance", "reports"]
            missing = [d for d in dirs if not (base / d).exists()]
            return {
                "status": "PASS" if not missing else "WARN",
                "missing_dirs": missing
            }
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
"""
        idx = content.find("class OpsStoreChecker:")
        if idx != -1:
            content = content.replace("class OpsStoreChecker:", "class OpsStoreChecker:" + hook)

    with open(path, "w") as f:
        f.write(content)

# Reports
path = "bist_signal_bot/reports/collector.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "collect_model_registry_report" not in content:
        hook = """
    def collect_model_registry_report(self) -> dict[str, Any]:
        if not getattr(self.settings, "REPORT_INCLUDE_MODEL_REGISTRY", True):
            return {"status": "SKIPPED"}

        try:
            from bist_signal_bot.app.model_registry_app import create_local_model_registry
            reg = create_local_model_registry(self.settings)
            models = reg.list_models()

            return {
                "total_models": len(models),
                "active_research": len([m for m in models if m.status.value == "ACTIVE_RESEARCH"]),
                "candidate": len([m for m in models if m.status.value == "CANDIDATE"]),
                "blocked": len([m for m in models if m.status.value == "BLOCKED_LEAKAGE"]),
            }
        except Exception as e:
            return {"error": str(e)}
"""
        idx = content.find("class ReportCollector:")
        if idx != -1:
            content = content.replace("class ReportCollector:", "class ReportCollector:" + hook)

    with open(path, "w") as f:
        f.write(content)
