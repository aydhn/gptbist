import os

path = "bist_signal_bot/strategy_registry/evidence.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "from bist_signal_bot.app.model_registry_app" not in content:
        imports = "from bist_signal_bot.app.model_registry_app import create_local_model_registry, create_model_governance_engine\n"
        content = imports + content

        # We can add a method to EvidenceCollector
        hook = """
    def collect_model_evidence(self, model_id: str) -> dict[str, Any]:
        evidence = {}
        try:
            reg = create_local_model_registry(self.settings)
            gov = create_model_governance_engine(self.settings)

            model = reg.get_model(model_id)
            if model:
                evidence["model_status"] = model.status.value
                assessment = gov.assess_model(model_id)
                evidence["model_governance_status"] = assessment.status.value
                evidence["model_blocking_reasons"] = assessment.blocking_reasons
        except Exception as e:
            self.logger.warning(f"Failed to collect model evidence: {e}")
        return evidence
"""
        # find class StrategyEvidenceCollector:
        idx = content.find("class StrategyEvidenceCollector:")
        if idx != -1:
            content = content.replace("class StrategyEvidenceCollector:", "class StrategyEvidenceCollector:" + hook)

    with open(path, "w") as f:
        f.write(content)
else:
    print(f"Skipping {path} as it does not exist")
