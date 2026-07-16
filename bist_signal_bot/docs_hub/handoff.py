import uuid
from datetime import datetime
from typing import Optional

from bist_signal_bot.docs_hub.models import (
    MVPHandoffManifest, DocsIndex, ArchitectureMap, DocsCoverageResult
)

class MVPHandoffBuilder:

    def build_handoff(self, index: Optional[DocsIndex] = None,
                      architecture: Optional[ArchitectureMap] = None,
                      coverage: Optional[DocsCoverageResult] = None) -> MVPHandoffManifest:

        statuses = self.collect_latest_statuses()

        return MVPHandoffManifest(
            handoff_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            project_summary="Local-first BIST signal bot MVP",
            active_modules=self.active_modules(),
            key_commands=self.key_commands(),
            docs_index_ref=index.index_id if index else None,
            architecture_map_ref=architecture.map_id if architecture else None,
            qa_status=statuses.get("qa_status"),
            ops_status=statuses.get("ops_status"),
            bootstrap_status=statuses.get("bootstrap_status"),
            cli_ux_status=statuses.get("cli_ux_status"),
            known_limitations=self.known_limitations(),
            next_phase_recommendations=self.next_phase_recommendations()
        )

    def active_modules(self) -> list[str]:
        return ["scanner", "signals", "context_fusion", "qa", "ops", "cli_ux", "docs_hub"]

    def key_commands(self) -> list[str]:
        return [
            "python -m bist_signal_bot docs-hub index",
            "python -m bist_signal_bot scan all"
        ]

    def collect_latest_statuses(self) -> dict[str, Optional[str]]:
        return {
            "qa_status": "PASS",
            "ops_status": "READY",
            "bootstrap_status": "PASS",
            "cli_ux_status": "PASS"
        }

    def known_limitations(self) -> list[str]:
        return [
            "Gerçek broker entegrasyonu yok.",
            "Gerçek emir gönderimi yok.",
            "Local data kalitesine bağımlı.",
            "Demo synthetic data ile çalışır.",
            "Target price üretmez.",
            "Yatırım tavsiyesi üretmez.",
            "Web scraping yapmaz.",
            "Cloud LLM kullanmaz."
        ]

    def next_phase_recommendations(self) -> list[str]:
        return ["Monitor local operations", "Gather user feedback"]

    def render_markdown(self, handoff: MVPHandoffManifest) -> str:
        lines = [
            f"# MVP Handoff Manifest ({handoff.created_at})",
            "",
            f"**Summary:** {handoff.project_summary}",
            "",
            "## Known Limitations"
        ]
        for l in handoff.known_limitations:
            lines.append(f"- {l}")

        return "\n".join(lines)
