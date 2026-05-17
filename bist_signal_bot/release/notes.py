from datetime import datetime
from pathlib import Path
from typing import Any

from bist_signal_bot.release.models import ReleaseNotes, ReleaseStage, ReleaseReadinessReport

class ReleaseNotesBuilder:

    def build_notes(self, version: str, stage: ReleaseStage, readiness: ReleaseReadinessReport | None = None) -> ReleaseNotes:
        notes = ReleaseNotes(
            version=version,
            stage=stage,
            title=f"BIST Signal Bot {version} ({stage.value})",
            summary="This release focuses on providing a stable, research-only MVP environment.",
            highlights=[
                "Local-first execution without cloud requirements.",
                "Safe research profiles for backtesting and scanning.",
                "Zero real market execution capabilities by design."
            ],
            added=["Release Readiness Module", "Safe Launch Rehearsal"],
            changed=["Disabled all real broker integrations"],
            fixed=["Hardened secrets management"],
            known_issues=["Optional ML components require separate setup"],
            safety_notes=["No real orders will be placed. Paper simulation is for research only."],
            upgrade_notes=["Backup your local 'data/' directory before proceeding."]
        )
        return notes

    def render_markdown(self, notes: ReleaseNotes) -> str:
        md = []
        md.append(f"# {notes.title}")
        md.append(f"\n*{notes.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}*")
        md.append(f"\n## Summary\n{notes.summary}")

        if notes.highlights:
            md.append("\n## Highlights")
            for h in notes.highlights:
                md.append(f"- {h}")

        if notes.added:
            md.append("\n## Added")
            for a in notes.added:
                md.append(f"- {a}")

        if notes.safety_notes:
            md.append("\n## Safety Notes")
            for s in notes.safety_notes:
                md.append(f"- ⚠️ {s}")

        md.append(f"\n---\n**Disclaimer**: {notes.disclaimer}")
        return "\n".join(md)

    def render_text(self, notes: ReleaseNotes) -> str:
        # A simpler version of markdown
        return self.render_markdown(notes).replace("#", "").replace("**", "")

    def save_notes(self, notes: ReleaseNotes, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / "release_notes.md"
        file_path.write_text(self.render_markdown(notes), encoding="utf-8")
        return file_path
