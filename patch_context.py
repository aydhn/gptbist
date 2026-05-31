import os

path = "bist_signal_bot/context_fusion/collectors.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "def collect_model_context" not in content:
        hook = """
    def collect_model_context(self, model_id: str) -> dict[str, Any]:
        context = {"source": "MODEL_REGISTRY"}
        try:
            from bist_signal_bot.app.model_registry_app import create_model_governance_engine
            gov = create_model_governance_engine(self.settings)
            assessment = gov.assess_model(model_id)
            context["model_governance_status"] = assessment.status.value
            context["validation_status"] = assessment.validation_status.value if assessment.validation_status else "UNKNOWN"
            context["calibration_status"] = assessment.calibration_status.value if assessment.calibration_status else "UNKNOWN"
        except Exception as e:
            self.logger.warning(f"Failed to collect model context: {e}")
        return context
"""
        # find class ContextCollector:
        idx = content.find("class ContextCollector:")
        if idx != -1:
            content = content.replace("class ContextCollector:", "class ContextCollector:" + hook)

    with open(path, "w") as f:
        f.write(content)
else:
    print(f"Skipping {path} as it does not exist")
