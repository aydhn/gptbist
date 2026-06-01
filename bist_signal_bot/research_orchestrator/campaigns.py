import uuid
from datetime import datetime, timezone
from bist_signal_bot.research_orchestrator.models import ResearchCampaign, ResearchCampaignType, ResearchTask, ResearchTaskType

class ResearchCampaignRegistry:
    def __init__(self):
        self._campaigns = self.default_campaigns()

    def default_campaigns(self) -> list[ResearchCampaign]:
        campaigns = []

        c_quick = ResearchCampaign(
            campaign_id=str(uuid.uuid4()),
            campaign_type=ResearchCampaignType.QUICK_RESEARCH_SCAN,
            name="Quick Research Scan",
            description="Runs a basic data catalog gate, feature compute, and scanner.",
            created_at=datetime.now(timezone.utc),
            default_profile="STANDARD",
            default_symbols=["ASELS", "THYAO", "TUPRS"],
            default_tasks=[
                ResearchTask(task_id="t1", task_type=ResearchTaskType.DATA_CATALOG_GATE, name="Data Catalog Gate"),
                ResearchTask(task_id="t2", task_type=ResearchTaskType.FEATURE_COMPUTE, name="Feature Compute", depends_on=["t1"]),
                ResearchTask(task_id="t3", task_type=ResearchTaskType.SCANNER_RUN, name="Scanner Run", depends_on=["t2"]),
                ResearchTask(task_id="t4", task_type=ResearchTaskType.REPORT_BUILD, name="Report Build", depends_on=["t3"])
            ]
        )
        campaigns.append(c_quick)

        c_full = ResearchCampaign(
            campaign_id=str(uuid.uuid4()),
            campaign_type=ResearchCampaignType.FULL_RESEARCH_PIPELINE,
            name="Full Research Pipeline",
            description="End-to-end research campaign.",
            created_at=datetime.now(timezone.utc),
            default_profile="ADVANCED",
            default_symbols=["ASELS", "THYAO", "TUPRS", "GARAN", "KCHOL"]
        )
        campaigns.append(c_full)

        c_model = ResearchCampaign(
            campaign_id=str(uuid.uuid4()),
            campaign_type=ResearchCampaignType.MODEL_GOVERNANCE_CAMPAIGN,
            name="Model Governance Campaign",
            description="Validates and calibrates models.",
            created_at=datetime.now(timezone.utc),
            default_profile="ML_DEV"
        )
        campaigns.append(c_model)

        return campaigns

    def get_campaign(self, campaign_type_or_name: str) -> ResearchCampaign | None:
        for c in self._campaigns:
            if c.campaign_type.value == campaign_type_or_name or c.name == campaign_type_or_name:
                return c
        return None

    def validate_campaign(self, campaign: ResearchCampaign) -> list[str]:
        errors = []
        if not campaign.name:
            errors.append("Campaign name is required.")
        return errors

    def campaigns_for_profile(self, profile_name: str) -> list[ResearchCampaign]:
        return [c for c in self._campaigns if c.default_profile == profile_name]

    def render_campaign_markdown(self, campaign: ResearchCampaign) -> str:
        lines = [
            f"# Campaign: {campaign.name}",
            f"**Type:** {campaign.campaign_type.value}",
            f"**Description:** {campaign.description}",
            f"**Profile:** {campaign.default_profile}",
            "",
            "## Default Symbols",
            ", ".join(campaign.default_symbols) if campaign.default_symbols else "None",
            "",
            "## Disclaimer",
            f"*{campaign.disclaimer}*"
        ]
        return "\n".join(lines)
