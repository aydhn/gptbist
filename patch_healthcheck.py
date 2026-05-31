import os

path = "bist_signal_bot/app/healthcheck.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "def check_model_registry" not in content:
        hook = """
    def check_model_registry(self) -> dict[str, Any]:
        res = {"enabled": getattr(self.settings, "ENABLE_MODEL_REGISTRY", False)}
        if not res["enabled"]:
            return res

        try:
            from bist_signal_bot.app.model_registry_app import create_local_model_registry, create_model_governance_engine
            reg = create_local_model_registry(self.settings)
            gov = create_model_governance_engine(self.settings)

            models = reg.list_models()
            res["registry_readable"] = True
            res["total_models"] = len(models)

            blocked = 0
            for m in models:
                assessment = gov.assess_model(m.model_id)
                if assessment.status.value in ["BLOCKED", "FAIL"]:
                    blocked += 1
            res["blocked_models"] = blocked
        except Exception as e:
            res["registry_readable"] = False
            res["error"] = str(e)

        return res
"""
        idx = content.find("class HealthcheckManager:")
        if idx != -1:
            content = content.replace("class HealthcheckManager:", "class HealthcheckManager:" + hook)

        # Hook into run_healthcheck
        eval_idx = content.find("def run_healthcheck(")
        if eval_idx != -1:
            # We assume it has a report dict and returns it
            check_hook = "\n        report['model_registry'] = self.check_model_registry()\n"
            eval_body_idx = content.find("return report", eval_idx)
            if eval_body_idx != -1:
                content = content[:eval_body_idx] + check_hook + content[eval_body_idx:]

    with open(path, "w") as f:
        f.write(content)
