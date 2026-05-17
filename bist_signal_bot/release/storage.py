import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.storage.paths import get_release_dir
from bist_signal_bot.release.models import (
    ReleaseReadinessReport, SafeLaunchRehearsalResult, ReleaseCandidateManifest, ReleaseNotes
)
from bist_signal_bot.release.reporting import (
    readiness_report_to_dict, release_checks_to_dataframe, format_readiness_markdown,
    rehearsal_result_to_dict, candidate_manifest_to_dict, release_notes_to_dict
)

class ReleaseStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or get_settings()
        self.base_dir = base_dir or get_release_dir(self.settings)

    def get_release_dir(self) -> Path:
        return self.base_dir

    def create_release_run_dir(self, run_id: str) -> Path:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        d = self.base_dir / date_str / run_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save_readiness_report(self, report: ReleaseReadinessReport, output_dir: Path | None = None) -> dict[str, Path]:
        out_dir = output_dir or self.create_release_run_dir(report.readiness_id)
        paths = {}

        # JSON
        j_path = out_dir / "readiness_report.json"
        with open(j_path, "w", encoding="utf-8") as f:
            json.dump(readiness_report_to_dict(report), f, indent=2, default=str)
        paths["json"] = j_path

        # Markdown
        m_path = out_dir / "readiness_report.md"
        with open(m_path, "w", encoding="utf-8") as f:
             f.write(format_readiness_markdown(report))
        paths["markdown"] = m_path

        # CSV
        df = release_checks_to_dataframe(report.checks)
        c_path = out_dir / "checks.csv"
        df.to_csv(c_path, index=False)
        paths["csv"] = c_path

        return paths

    def save_rehearsal_result(self, result: SafeLaunchRehearsalResult, output_dir: Path | None = None) -> dict[str, Path]:
        out_dir = output_dir or self.create_release_run_dir(result.rehearsal_id)
        paths = {}
        j_path = out_dir / "safe_launch_rehearsal.json"
        with open(j_path, "w", encoding="utf-8") as f:
             json.dump(rehearsal_result_to_dict(result), f, indent=2, default=str)
        paths["json"] = j_path
        return paths

    def save_candidate_manifest(self, manifest: ReleaseCandidateManifest, output_dir: Path | None = None) -> Path:
        out_dir = output_dir or self.create_release_run_dir(manifest.candidate_id)
        j_path = out_dir / "candidate_manifest.json"
        with open(j_path, "w", encoding="utf-8") as f:
             json.dump(candidate_manifest_to_dict(manifest), f, indent=2, default=str)
        return j_path

    def save_release_notes(self, notes: ReleaseNotes, output_dir: Path | None = None) -> Path:
        out_dir = output_dir or self.create_release_run_dir("notes_" + datetime.utcnow().strftime("%H%M%S"))
        from bist_signal_bot.release.notes import ReleaseNotesBuilder
        return ReleaseNotesBuilder().save_notes(notes, out_dir)

    def list_recent_release_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        runs = []
        if not self.base_dir.exists():
            return runs

        for date_dir in sorted(self.base_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue
            for run_dir in sorted(date_dir.iterdir(), reverse=True):
                if not run_dir.is_dir():
                    continue

                manifest_file = run_dir / "candidate_manifest.json"
                readiness_file = run_dir / "readiness_report.json"

                run_info = {"run_id": run_dir.name, "date": date_dir.name}
                if readiness_file.exists():
                    try:
                        with open(readiness_file, "r") as f:
                             data = json.load(f)
                             run_info["readiness_status"] = data.get("status")
                             run_info["version"] = data.get("version")
                    except:
                        pass

                if manifest_file.exists():
                     run_info["has_manifest"] = True

                runs.append(run_info)
                if len(runs) >= limit:
                    return runs
        return runs
