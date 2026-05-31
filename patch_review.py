import os

path = "bist_signal_bot/review_workflow/case_builder.py"
if os.path.exists(path):
    with open(path, "r") as f:
        content = f.read()

    if "from bist_signal_bot.app.model_registry_app" not in content:
        imports = "from bist_signal_bot.app.model_registry_app import create_local_model_registry, create_model_governance_engine\nfrom bist_signal_bot.model_registry.models import ModelGovernanceStatus\n"
        content = imports + content

        hook = """
    def add_model_registry_evidence(self, case, model_id: str):
        try:
            reg = create_local_model_registry(self.settings)
            gov = create_model_governance_engine(self.settings)

            model = reg.get_model(model_id)
            if model:
                assessment = gov.assess_model(model_id)
                case.evidence["model_registry"] = {
                    "model_id": model_id,
                    "status": model.status.value,
                    "governance_status": assessment.status.value,
                    "blocking_reasons": assessment.blocking_reasons
                }

                # Assign playbooks based on assessment
                if assessment.status == ModelGovernanceStatus.FAIL:
                    case.recommended_playbooks.append("MODEL_GOVERNANCE_FAIL")
                elif assessment.status == ModelGovernanceStatus.BLOCKED:
                    case.recommended_playbooks.append("MODEL_GOVERNANCE_BLOCKED")

                if assessment.model_card_status != ModelGovernanceStatus.PASS:
                    case.recommended_playbooks.append("MODEL_CARD_MISSING")

        except Exception as e:
            self.logger.warning(f"Failed to add model registry evidence to case: {e}")
"""
        idx = content.find("class ReviewCaseBuilder:")
        if idx != -1:
            content = content.replace("class ReviewCaseBuilder:", "class ReviewCaseBuilder:" + hook)

    with open(path, "w") as f:
        f.write(content)
else:
    print(f"Skipping {path} as it does not exist")
