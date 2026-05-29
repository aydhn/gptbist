import uuid
from typing import Any
from bist_signal_bot.bootstrap.models import OnboardingGuide, RunProfileName

class OnboardingGuideBuilder:
    def __init__(self, settings=None):
        self.settings = settings

    def build_guide(self, profile_name: RunProfileName = RunProfileName.STANDARD) -> OnboardingGuide:
        return OnboardingGuide(
            guide_id=str(uuid.uuid4()),
            profile_name=profile_name,
            title="Local MVP Onboarding",
            sections=[{"title": "Welcome", "content": "Welcome to BIST Signal Bot"}],
            recommended_recipes=["QUICKSTART"]
        )

    def quickstart_sections(self, profile) -> list[dict[str, Any]]:
        return []

    def safety_sections(self, profile) -> list[dict[str, Any]]:
        return []

    def workflow_sections(self, profile) -> list[dict[str, Any]]:
        return []

    def troubleshooting_sections(self, profile) -> list[dict[str, Any]]:
        return []

    def render_markdown(self, guide: OnboardingGuide) -> str:
        return f"# {guide.title}\n\n" + "\n\n".join(s["content"] for s in guide.sections)
