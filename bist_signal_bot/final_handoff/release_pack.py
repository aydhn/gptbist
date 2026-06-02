import uuid
import hashlib
from typing import List, Optional, Dict
from pathlib import Path
from bist_signal_bot.final_handoff.models import FinalReleasePack, ReleasePackStage
from bist_signal_bot.config.settings import Settings

class FinalReleasePackBuilder:
    def __init__(self, settings: Optional[Settings] = None, base_dir: Optional[Path] = None):
        self.settings = settings or Settings()
        self.base_dir = base_dir or Path.cwd()

    def build_release_pack(self, stage: ReleasePackStage = ReleasePackStage.BUILT, save: bool = False) -> FinalReleasePack:
        pack = FinalReleasePack(
            pack_id=str(uuid.uuid4()),
            stage=stage,
            included_docs=self.collect_docs() if self.settings.FINAL_HANDOFF_INCLUDE_DOCS else [],
            included_examples=self.collect_examples() if self.settings.FINAL_HANDOFF_INCLUDE_EXAMPLES else [],
            included_reports=self.collect_reports() if self.settings.FINAL_HANDOFF_INCLUDE_REPORTS else [],
            included_manifests=self.collect_manifests() if self.settings.FINAL_HANDOFF_INCLUDE_MANIFESTS else []
        )
        if self.settings.FINAL_HANDOFF_INCLUDE_CHECKSUMS:
            paths = [self.base_dir / p for p in pack.included_docs + pack.included_examples + pack.included_reports + pack.included_manifests]
            pack.checksum_manifest = self.checksum_manifest([str(p) for p in paths if p.exists() and p.is_file()])

        return pack

    def collect_docs(self) -> List[str]:
        # Return a list of critical doc paths
        docs_dir = self.base_dir / "bist_signal_bot" / "docs"
        if not docs_dir.exists():
            return []
        return [str(p.relative_to(self.base_dir)) for p in docs_dir.glob("*.md")]

    def collect_examples(self) -> List[str]:
        examples_dir = self.base_dir / "bist_signal_bot" / "examples"
        if not examples_dir.exists():
            return []
        return [str(p.relative_to(self.base_dir)) for p in examples_dir.glob("*.md")]

    def collect_reports(self) -> List[str]:
         reports_dir = self.base_dir / "data" / "reports"
         if not reports_dir.exists():
             return []
         return [str(p.relative_to(self.base_dir)) for p in reports_dir.rglob("*.md")]

    def collect_manifests(self) -> List[str]:
         manifests_dir = self.base_dir / "data" / "final_handoff" / "manifests"
         if not manifests_dir.exists():
             return []
         return [str(p.relative_to(self.base_dir)) for p in manifests_dir.rglob("*.json*")]

    def checksum_manifest(self, paths: List[str]) -> Dict[str, str]:
        checksums = {}
        for path_str in paths:
            path = Path(path_str)
            if path.exists() and path.is_file():
                hasher = hashlib.sha256()
                with open(path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
                # Keep paths relative for portability
                try:
                    rel_path = str(path.relative_to(self.base_dir))
                except ValueError:
                    rel_path = str(path)
                checksums[rel_path] = hasher.hexdigest()
        return checksums

    def validate_release_pack(self, pack: FinalReleasePack) -> List[str]:
        errors = []
        if not pack.included_docs and self.settings.FINAL_HANDOFF_INCLUDE_DOCS:
            errors.append("No docs included but FINAL_HANDOFF_INCLUDE_DOCS is true.")
        return errors

def add_report_templates_artifacts(pack):
    return pack
