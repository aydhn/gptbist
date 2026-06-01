import uuid
from typing import List, Optional
from bist_signal_bot.final_handoff.models import PostReleaseRoadmapItem, RoadmapPriority, FinalHandoffStatus
from bist_signal_bot.config.settings import Settings

class PostReleaseRoadmapBuilder:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()

    def build_roadmap(self) -> List[PostReleaseRoadmapItem]:
        items = self.near_term_items() + self.mid_term_items() + self.long_term_items()
        return items

    def near_term_items(self) -> List[PostReleaseRoadmapItem]:
        if not self.settings.FINAL_HANDOFF_INCLUDE_PHASE_101_PLUS_ROADMAP:
            return []
        return [
            PostReleaseRoadmapItem(
                roadmap_id=str(uuid.uuid4()),
                title="Performance Optimization & Profiling",
                description="Profile and optimize critical paths in the scanner and backtesting engines.",
                priority=RoadmapPriority.HIGH,
                target_area="core",
                suggested_phase="101",
                status=FinalHandoffStatus.PASS
            ),
             PostReleaseRoadmapItem(
                roadmap_id=str(uuid.uuid4()),
                title="Richer Local Data Import Adapters",
                description="Add support for more offline data formats and direct DB integrations (read-only).",
                priority=RoadmapPriority.MEDIUM,
                target_area="data",
                suggested_phase="102",
                status=FinalHandoffStatus.PASS
            )
        ]

    def mid_term_items(self) -> List[PostReleaseRoadmapItem]:
        if not self.settings.FINAL_HANDOFF_INCLUDE_PHASE_101_PLUS_ROADMAP:
            return []
        return [
             PostReleaseRoadmapItem(
                roadmap_id=str(uuid.uuid4()),
                title="Advanced Report Templates",
                description="Allow custom jinja/markdown templates for reports.",
                priority=RoadmapPriority.LOW,
                target_area="reports",
                suggested_phase="103",
                status=FinalHandoffStatus.PASS
            ),
             PostReleaseRoadmapItem(
                roadmap_id=str(uuid.uuid4()),
                title="Optional Local UI/TUI Investigation",
                description="Investigate safe, offline local UI or Text UI options without breaking core CLI.",
                priority=RoadmapPriority.MEDIUM,
                target_area="ux",
                suggested_phase="105",
                status=FinalHandoffStatus.PASS
            )
        ]

    def long_term_items(self) -> List[PostReleaseRoadmapItem]:
        if not self.settings.FINAL_HANDOFF_INCLUDE_PHASE_101_PLUS_ROADMAP:
            return []
        return [
            PostReleaseRoadmapItem(
                roadmap_id=str(uuid.uuid4()),
                title="Plugin Architecture",
                description="Decouple modules into isolated plugins with defined interfaces.",
                priority=RoadmapPriority.MEDIUM,
                target_area="architecture",
                suggested_phase="109",
                status=FinalHandoffStatus.PASS
            ),
            PostReleaseRoadmapItem(
                roadmap_id=str(uuid.uuid4()),
                title="Strict Release Branch Policy",
                description="Implement semantic release and branching governance.",
                priority=RoadmapPriority.HIGH,
                target_area="governance",
                suggested_phase="110",
                status=FinalHandoffStatus.PASS
            )
        ]

    def validate_roadmap(self, items: List[PostReleaseRoadmapItem]) -> List[str]:
        errors = []
        for item in items:
            if item.priority == RoadmapPriority.UNKNOWN:
                errors.append(f"Roadmap item '{item.title}' has unknown priority.")
        return errors

    def render_markdown(self, items: List[PostReleaseRoadmapItem]) -> str:
        lines = ["# Post-Release Roadmap\n"]
        for item in items:
            lines.append(f"## Phase {item.suggested_phase}: {item.title}")
            lines.append(f"- **Priority**: {item.priority.value}")
            lines.append(f"- **Target Area**: {item.target_area}")
            lines.append(f"- **Description**: {item.description}")
            if item.risks:
                lines.append(f"- **Risks**: {', '.join(item.risks)}")
            lines.append("")
        return "\n".join(lines)
