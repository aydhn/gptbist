import json
import csv
from pathlib import Path
from datetime import datetime
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.packaging.models import (
    ReleaseManifest, EnvironmentDoctorReport, DependencyCheckResult, ReleaseBundleResult
)
from bist_signal_bot.storage.paths import get_packaging_dir
from bist_signal_bot.core.exceptions import PackagingStorageError

class PackagingStore:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def get_packaging_dir(self) -> Path:
        return get_packaging_dir(self.settings)

    def create_release_dir(self, release_id: str) -> Path:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        release_dir = self.get_packaging_dir() / date_str / release_id
        release_dir.mkdir(parents=True, exist_ok=True)
        return release_dir

    def save_manifest(self, manifest: ReleaseManifest, output_dir: Path) -> Path:
        from bist_signal_bot.packaging.reporting import release_manifest_to_dict

        manifest_path = output_dir / "release_manifest.json"
        data = release_manifest_to_dict(manifest)

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        return manifest_path

    def save_environment_report(self, report: EnvironmentDoctorReport, output_dir: Path) -> Path:
        from bist_signal_bot.packaging.reporting import environment_doctor_report_to_dict

        report_path = output_dir / "environment_doctor.json"
        data = environment_doctor_report_to_dict(report)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

        return report_path

    def save_dependency_report(self, results: list[DependencyCheckResult], output_dir: Path) -> Path:
        report_path = output_dir / "dependency_report.csv"

        with open(report_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Package", "Required", "Installed", "Status", "Optional", "Message"])
            for r in results:
                writer.writerow([
                    r.package_name,
                    r.required_version or "",
                    r.installed_version or "",
                    r.status.name,
                    r.optional,
                    r.message
                ])

        return report_path

    def save_release_result(self, result: ReleaseBundleResult, output_dir: Path | None = None) -> dict[str, Path]:
        from bist_signal_bot.packaging.reporting import release_bundle_result_to_dict, format_release_report_markdown

        out_dir = output_dir or self.create_release_dir(result.release_id)
        out_dir.mkdir(parents=True, exist_ok=True)

        paths = {}

        # Save manifest
        paths["manifest"] = self.save_manifest(result.manifest, out_dir)

        # Save report JSON
        report_path = out_dir / "release_report.json"
        data = release_bundle_result_to_dict(result)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        paths["report_json"] = report_path

        # Save report MD
        md_path = out_dir / "release_report.md"
        md_content = format_release_report_markdown(result)
        md_path.write_text(md_content, encoding="utf-8")
        paths["report_md"] = md_path

        return paths

    def list_recent_releases(self, limit: int = 20) -> list[dict[str, Any]]:
        pkg_dir = self.get_packaging_dir()
        if not pkg_dir.exists():
            return []

        releases = []
        for date_dir in sorted(pkg_dir.iterdir(), reverse=True):
            if not date_dir.is_dir():
                continue

            for rel_dir in sorted(date_dir.iterdir(), reverse=True):
                if not rel_dir.is_dir():
                    continue

                manifest_file = rel_dir / "release_manifest.json"
                if manifest_file.exists():
                    try:
                        with open(manifest_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            releases.append({
                                "release_id": data.get("release_id"),
                                "version": data.get("version"),
                                "created_at": data.get("created_at"),
                                "path": str(rel_dir)
                            })
                    except Exception:
                        pass

                if len(releases) >= limit:
                    return releases

        return releases
