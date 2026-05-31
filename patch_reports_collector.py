import os
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
        content = content.replace("class ReportDataCollector:", "class ReportDataCollector:" + hook)

    with open(path, "w") as f:
        f.write(content)

path2 = "bist_signal_bot/tests/test_model_registry_integrations.py"
with open(path2, "r") as f:
    content2 = f.read()
content2 = content2.replace("from bist_signal_bot.reports.collector import ReportCollector", "from bist_signal_bot.reports.collector import ReportDataCollector")
content2 = content2.replace("collector = ReportCollector(settings)", "collector = ReportDataCollector(settings)")

with open(path2, "w") as f:
    f.write(content2)
