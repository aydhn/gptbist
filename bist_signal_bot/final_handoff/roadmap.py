import uuid
from bist_signal_bot.final_handoff.models import PostReleaseRoadmapItem, RoadmapPriority, FinalHandoffStatus
from bist_signal_bot.final_handoff.reporting import format_roadmap_markdown

class PostReleaseRoadmapBuilder:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def build_roadmap(self) -> list[PostReleaseRoadmapItem]:
        items = []
        if getattr(self.settings, "FINAL_HANDOFF_INCLUDE_PHASE_101_PLUS_ROADMAP", True):
            items.extend(self.near_term_items())
            items.extend(self.mid_term_items())
            items.extend(self.long_term_items())
        return items

    def near_term_items(self) -> list[PostReleaseRoadmapItem]:
        return [
            PostReleaseRoadmapItem(
                roadmap_id=str(uuid.uuid4()),
                title="Performance Optimization and Profiling",
                description="Optimize slow paths in batch processing.",
                priority=RoadmapPriority.HIGH,
                target_area="core",
                suggested_phase="101",
                status=FinalHandoffStatus.PASS
            ),
            PostReleaseRoadmapItem(
                roadmap_id=str(uuid.uuid4()),
                title="Richer Local Data Import Adapters",
                description="Add more adapters for offline data sources.",
                priority=RoadmapPriority.MEDIUM,
                target_area="data",
                suggested_phase="102",
                status=FinalHandoffStatus.PASS
            )
        ]

    def mid_term_items(self) -> list[PostReleaseRoadmapItem]:
        return [
            PostReleaseRoadmapItem(
                roadmap_id=str(uuid.uuid4()),
                title="Advanced Report Templates",
                description="Customizable Jinja templates for reporting.",
                priority=RoadmapPriority.MEDIUM,
                target_area="reports",
                suggested_phase="103",
                status=FinalHandoffStatus.PASS
            ),
            PostReleaseRoadmapItem(
                roadmap_id=str(uuid.uuid4()),
                title="Extended Synthetic Scenario Library",
                description="Add more stress test scenarios.",
                priority=RoadmapPriority.MEDIUM,
                target_area="qa",
                suggested_phase="104",
                status=FinalHandoffStatus.PASS
            ),
            PostReleaseRoadmapItem(
                roadmap_id=str(uuid.uuid4()),
                title="Optional Local UI/TUI Investigation",
                description="Investigate safe local TUI without web scraping.",
                priority=RoadmapPriority.LOW,
                target_area="cli_ux",
                suggested_phase="105",
                status=FinalHandoffStatus.PASS
            )
        ]

    def long_term_items(self) -> list[PostReleaseRoadmapItem]:
        return [
            PostReleaseRoadmapItem(
                roadmap_id=str(uuid.uuid4()),
                title="Advanced Model Explainability",
                description="SHAP values for ML features.",
                priority=RoadmapPriority.LOW,
                target_area="model_registry",
                suggested_phase="106",
                status=FinalHandoffStatus.PASS
            )
        ]

    def validate_roadmap(self, items: list[PostReleaseRoadmapItem]) -> list[str]:
        warnings = []
        for i in items:
            if "guarantee" in i.description.lower() or "profit" in i.description.lower():
                warnings.append(f"Item {i.roadmap_id} contains unsafe claims.")
        return warnings

    def render_markdown(self, items: list[PostReleaseRoadmapItem]) -> str:
        return format_roadmap_markdown(items)
