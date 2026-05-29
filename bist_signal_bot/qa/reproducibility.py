from bist_signal_bot.qa.models import ReproducibilityPack, QAReport
import uuid
from datetime import datetime
from pathlib import Path

class ReproducibilityPackBuilder:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def build_pack(self, report: QAReport | None = None, output_dir: Path | None = None) -> ReproducibilityPack:
        return ReproducibilityPack(
            pack_id=str(uuid.uuid4()),
            created_at=datetime.utcnow()
        )

    def write_run_manifest(self, output_dir: Path, metadata: dict) -> Path:
        return output_dir / "run_manifest.json"

    def write_config_snapshot(self, output_dir: Path) -> Path:
         return output_dir / "config_snapshot.json"

    def write_environment_summary(self, output_dir: Path) -> Path:
         return output_dir / "env_summary.json"

    def write_fixture_manifest(self, output_dir: Path, manifest=None) -> Path:
         return output_dir / "fixture_manifest.json"

    def build_checksum_manifest(self, paths: list[Path]) -> dict[str, str]:
        return {}
