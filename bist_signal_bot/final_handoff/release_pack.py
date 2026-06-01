import uuid
import hashlib
from datetime import datetime
from bist_signal_bot.final_handoff.models import FinalReleasePack, ReleasePackStage
from bist_signal_bot.final_handoff.reporting import format_release_pack_text

class FinalReleasePackBuilder:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def build_release_pack(self, stage: ReleasePackStage = ReleasePackStage.BUILT, save: bool = False) -> FinalReleasePack:
        pack = FinalReleasePack(
            pack_id=str(uuid.uuid4()),
            created_at=datetime.now(),
            stage=stage,
            included_docs=self.collect_docs(),
            included_examples=self.collect_examples(),
            included_reports=self.collect_reports(),
            included_manifests=self.collect_manifests(),
            checksum_manifest=self.checksum_manifest([]) # Simplified for demo
        )
        self.validate_release_pack(pack)
        if save:
            pass # Hook to store later
        return pack

    def collect_docs(self) -> list[str]:
        return ["docs/77_FINAL_MVP_HANDOFF.md", "docs/78_OPERATOR_PLAYBOOK.md"]

    def collect_examples(self) -> list[str]:
        return ["examples/final_handoff_workflow.md"]

    def collect_reports(self) -> list[str]:
        return []

    def collect_manifests(self) -> list[str]:
        return []

    def checksum_manifest(self, paths: list[str]) -> dict[str, str]:
        # Mock checksum generation
        return {"docs/77_FINAL_MVP_HANDOFF.md": "mock_sha256"}

    def validate_release_pack(self, pack: FinalReleasePack) -> list[str]:
        warnings = []
        if not pack.included_docs:
            warnings.append("Release pack has no docs.")
        pack.warnings.extend(warnings)
        return warnings
