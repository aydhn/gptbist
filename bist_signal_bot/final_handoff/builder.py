import uuid
from typing import List, Optional, Dict, Any
from bist_signal_bot.final_handoff.models import (
    FinalHandoffManifest, FinalModuleSummary, FinalCommandMapEntry,
    FinalHandoffStatus
)
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.final_handoff.module_map import FinalModuleMapBuilder
from bist_signal_bot.final_handoff.command_map import FinalCommandMapBuilder
from bist_signal_bot.final_handoff.roadmap import PostReleaseRoadmapBuilder
from bist_signal_bot.final_handoff.maintenance import MaintenanceCadenceBuilder

class FinalHandoffBuilder:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.module_builder = FinalModuleMapBuilder(self.settings)
        self.command_builder = FinalCommandMapBuilder(self.settings)
        self.roadmap_builder = PostReleaseRoadmapBuilder(self.settings)
        self.maintenance_builder = MaintenanceCadenceBuilder(self.settings)

    def build_handoff(self) -> FinalHandoffManifest:
        manifest = FinalHandoffManifest(
            handoff_id=str(uuid.uuid4()),
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
        return "Local-first, research-only, multi-layer BIST signal bot MVP. Orchestrates data, signals, risk, and portfolio analysis completely offline without live broker integrations."

    def collect_module_summaries(self) -> List[FinalModuleSummary]:
        return self.module_builder.build_module_map()

    def collect_command_entries(self) -> List[FinalCommandMapEntry]:
        return self.command_builder.build_command_map()

    def collect_latest_release_status(self) -> Dict[str, Any]:
        # In a real integration, this fetches from final_audit storage
        return {
            "release_candidate_id": "RC-MOCK",
            "go_no_go_decision": "GO"
        }

    def known_limitations(self) -> List[str]:
        return [
            "No real-time intraday tick data processing.",
            "No broker API integrations.",
            "No live portfolio sync.",
            "Offline local-first design means no web dashboard.",
            "Feature store runs batch only, not streaming."
        ]

    def residual_risks(self) -> List[str]:
        return [
            "Users may mistakenly interpret outputs as financial advice despite disclaimers.",
            "Local data files may grow large, requiring manual cleanup via ops tools.",
            "Model degradation if offline retraining schedule is ignored."
        ]

    def next_steps(self) -> List[str]:
        return [
            "Operator must run `bootstrap validate` and `healthcheck --final-handoff`.",
            "Operator should review the Operator Playbook for daily routines.",
            "Review post-release roadmap for Phase 101+ optimizations."
        ]

    def final_status(self, manifest: FinalHandoffManifest) -> FinalHandoffStatus:
        if manifest.go_no_go_decision == "GO":
             return FinalHandoffStatus.PASS
        elif manifest.go_no_go_decision == "GO_WITH_WARNINGS":
             return FinalHandoffStatus.WATCH
        elif manifest.go_no_go_decision == "NO_GO":
             return FinalHandoffStatus.FAIL

        return FinalHandoffStatus.UNKNOWN
