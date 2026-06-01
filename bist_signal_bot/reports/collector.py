from typing import Any
def run_daily_report(dry_run=False, include_data_catalog=False, include_feature_store=False, include_orchestrator=False):
    res = {"report": "daily"}
    if include_data_catalog:
        res["data_catalog_section"] = "included"
    if include_orchestrator:
        res['orchestrator_section'] = 'included'
    return res

class ReportDataCollector:
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

    def __init__(self, settings=None):
        pass

    def collect(self, config=None):
        return None
