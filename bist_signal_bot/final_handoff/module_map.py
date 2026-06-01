import uuid
from typing import List, Optional
from bist_signal_bot.final_handoff.models import FinalModuleSummary, FinalHandoffStatus
from bist_signal_bot.config.settings import Settings

class FinalModuleMapBuilder:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.modules = {
            "config": FinalModuleSummary(
                module_id=str(uuid.uuid4()),
                module_name="config",
                title="Configuration Management",
                purpose="Manages settings, feature flags, and environment variables offline.",
                owner_area="core",
                main_commands=["config-registry"],
                status=FinalHandoffStatus.PASS
            ),
             "scanner": FinalModuleSummary(
                module_id=str(uuid.uuid4()),
                module_name="scanner",
                title="Signal Scanner",
                purpose="Batches strategy evaluations across symbol universes to generate research signals.",
                owner_area="research",
                main_commands=["scan"],
                status=FinalHandoffStatus.PASS
            ),
             "final_handoff": FinalModuleSummary(
                module_id=str(uuid.uuid4()),
                module_name="final_handoff",
                title="Final MVP Handoff",
                purpose="Builds final release pack, operator playbook, and developer roadmap.",
                owner_area="governance",
                main_commands=["final-handoff"],
                status=FinalHandoffStatus.PASS
            )
        }

    def build_module_map(self) -> List[FinalModuleSummary]:
        return list(self.modules.values())

    def module_summary(self, module_name: str) -> FinalModuleSummary:
        if module_name in self.modules:
            return self.modules[module_name]
        return FinalModuleSummary(
            module_id=str(uuid.uuid4()),
            module_name=module_name,
            title=module_name.title(),
            purpose="Unknown module.",
            owner_area="unknown",
            status=FinalHandoffStatus.UNKNOWN
        )

    def module_dependencies(self, module_name: str) -> List[str]:
        if module_name == "final_handoff":
             return ["final_audit", "docs_hub", "bootstrap", "cli_ux", "config"]
        return []

    def module_commands(self, module_name: str) -> List[str]:
        summary = self.module_summary(module_name)
        return summary.main_commands

    def module_docs(self, module_name: str) -> List[str]:
        summary = self.module_summary(module_name)
        return summary.main_docs

    def render_markdown(self, modules: List[FinalModuleSummary]) -> str:
        lines = ["# Final Module Map\n"]
        for module in modules:
            lines.append(f"## {module.title} ({module.module_name})")
            lines.append(f"- **Purpose**: {module.purpose}")
            lines.append(f"- **Owner**: {module.owner_area}")
            lines.append(f"- **Status**: {module.status.value}")
            lines.append(f"- **Commands**: {', '.join(module.main_commands)}")
            lines.append("")
        return "\n".join(lines)
