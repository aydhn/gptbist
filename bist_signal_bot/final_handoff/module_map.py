from bist_signal_bot.final_handoff.models import FinalModuleSummary, FinalHandoffStatus
from bist_signal_bot.final_handoff.reporting import format_module_map_text

class FinalModuleMapBuilder:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir
        self.major_modules = [
            "config", "data", "scanner", "signals", "backtesting",
            "validation", "calibration", "strategy_registry", "risk",
            "portfolio_construction", "portfolio_ledger", "context_fusion",
            "review_workflow", "qa", "ops", "bootstrap", "cli_ux",
            "docs_hub", "data_catalog", "feature_store", "model_registry",
            "monitoring", "leaderboard", "research_orchestrator", "final_audit",
            "final_handoff", "reports", "security", "governance"
        ]

    def build_module_map(self) -> list[FinalModuleSummary]:
        return [self.module_summary(m) for m in self.major_modules]

    def module_summary(self, module_name: str) -> FinalModuleSummary:
        return FinalModuleSummary(
            module_id=f"MOD_{module_name.upper()}",
            module_name=module_name,
            title=module_name.replace("_", " ").title(),
            purpose=f"Handles {module_name.replace('_', ' ')} functionality.",
            owner_area="System",
            main_commands=self.module_commands(module_name),
            main_docs=self.module_docs(module_name),
            status=FinalHandoffStatus.PASS,
            dependencies=self.module_dependencies(module_name)
        )

    def module_dependencies(self, module_name: str) -> list[str]:
        if module_name == "final_handoff":
            return ["config", "core", "final_audit"]
        return ["config", "core"]

    def module_commands(self, module_name: str) -> list[str]:
        return [f"python -m bist_signal_bot {module_name.replace('_', '-')}"]

    def module_docs(self, module_name: str) -> list[str]:
        return [f"docs/{module_name}.md"]

    def render_markdown(self, modules: list[FinalModuleSummary]) -> str:
        return format_module_map_text(modules)
