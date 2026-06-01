import uuid
from datetime import datetime
from typing import Any

from bist_signal_bot.final_handoff.models import (
    FinalHandoffManifest,
    FinalHandoffStatus,
    FinalModuleSummary,
    FinalCommandMapEntry,
    PostReleaseRoadmapItem,
    MaintenanceTask
)
from bist_signal_bot.final_handoff.module_map import FinalModuleMapBuilder
from bist_signal_bot.final_handoff.command_map import FinalCommandMapBuilder
from bist_signal_bot.final_handoff.roadmap import PostReleaseRoadmapBuilder
from bist_signal_bot.final_handoff.maintenance import MaintenanceCadenceBuilder
from bist_signal_bot.final_handoff.operator_playbook import OperatorPlaybookBuilder
from bist_signal_bot.final_handoff.developer_playbook import DeveloperPlaybookBuilder

class FinalHandoffBuilder:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir
        self.module_builder = FinalModuleMapBuilder(settings, base_dir)
        self.command_builder = FinalCommandMapBuilder(settings, base_dir)
        self.roadmap_builder = PostReleaseRoadmapBuilder(settings, base_dir)
        self.maintenance_builder = MaintenanceCadenceBuilder(settings, base_dir)
        self.operator_builder = OperatorPlaybookBuilder(settings, base_dir)
        self.developer_builder = DeveloperPlaybookBuilder(settings, base_dir)

    def build_handoff(self) -> FinalHandoffManifest:
        manifest = FinalHandoffManifest(
            handoff_id=str(uuid.uuid4()),
            created_at=datetime.now(),
            project_name="BIST Signal Bot",
            project_summary=self.project_summary(),
            final_status=FinalHandoffStatus.UNKNOWN,
            module_summaries=self.collect_module_summaries(),
            command_entries=self.collect_command_entries(),
            roadmap_items=self.roadmap_builder.build_roadmap(),
            maintenance_tasks=self.maintenance_builder.build_tasks(),
            known_limitations=self.known_limitations(),
            residual_risks=self.residual_risks(),
            next_steps=self.next_steps()
        )

        status_info = self.collect_latest_release_status()
        manifest.release_candidate_id = status_info.get("release_candidate_id")
        manifest.go_no_go_decision = status_info.get("go_no_go_decision")

        manifest.final_status = self.final_status(manifest)
        return manifest

    def project_summary(self) -> str:
        return "BIST Signal Bot is a local-first, research-only algorithmic signal generator MVP. It does not execute real trades."

    def collect_module_summaries(self) -> list[FinalModuleSummary]:
        return self.module_builder.build_module_map()

    def collect_command_entries(self) -> list[FinalCommandMapEntry]:
        return self.command_builder.build_command_map()

    def collect_latest_release_status(self) -> dict[str, Any]:
        # In a real implementation, this would read from Final Audit
        return {
            "release_candidate_id": "RC_MOCK_123",
            "go_no_go_decision": "GO_WITH_WARNINGS"
        }

    def known_limitations(self) -> list[str]:
        return [
            "No real-time market data streaming.",
            "No live broker execution.",
            "Test coverage is focused on deterministic offline paths."
        ]

    def residual_risks(self) -> list[str]:
        return [
            "User might ignore disclaimers and attempt manual trading.",
            "Data staleness if daily ingest fails silently."
        ]

    def next_steps(self) -> list[str]:
        return [
            "Review Operator Playbook.",
            "Run offline demo.",
            "Execute QUICK_RESEARCH_SCAN."
        ]

    def final_status(self, manifest: FinalHandoffManifest) -> FinalHandoffStatus:
        if manifest.go_no_go_decision and "NO_GO" in manifest.go_no_go_decision:
            return FinalHandoffStatus.FAIL
        return FinalHandoffStatus.PASS
