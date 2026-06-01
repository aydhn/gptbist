from datetime import datetime, timezone
import uuid
from typing import Any
from pathlib import Path
import hashlib

from bist_signal_bot.final_audit.models import (
    HardeningFreezeManifest,
    ReleaseCandidateManifest
)
from bist_signal_bot.config.settings import Settings

class HardeningFreezeManager:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir or Path.cwd()

    def create_freeze(self, candidate: ReleaseCandidateManifest, confirm: bool = False) -> HardeningFreezeManifest:
        frozen = confirm
        paths = self.frozen_paths()
        checksums = self.checksum_manifest(paths)

        manifest = HardeningFreezeManifest(
            freeze_id=f"frz_{uuid.uuid4().hex[:8]}",
            candidate_id=candidate.candidate_id,
            created_at=datetime.now(timezone.utc),
            frozen=frozen,
            frozen_paths=paths,
            config_snapshot_ref="snapshot/config_v1.json" if frozen else None,
            docs_snapshot_ref="snapshot/docs_v1.tar.gz" if frozen else None,
            test_summary_ref="snapshot/test_summary_v1.json" if frozen else None,
            checksum_manifest=checksums,
            blocked_changes=["destructive file writes", "broker API calls"]
        )
        return manifest

    def frozen_paths(self) -> list[str]:
        return [
            "bist_signal_bot/config/settings.py",
            "bist_signal_bot/core",
            "bist_signal_bot/cli_ux",
            "bist_signal_bot/final_audit"
        ]

    def config_snapshot(self) -> str | None:
        return "snapshot/config_latest.json"

    def docs_snapshot(self) -> str | None:
        return "snapshot/docs_latest.tar.gz"

    def test_summary_snapshot(self) -> str | None:
        return "snapshot/tests_latest.json"

    def checksum_manifest(self, paths: list[str]) -> dict[str, str]:
        checksums = {}
        for p in paths:
            path_obj = self.base_dir / p
            if path_obj.exists() and path_obj.is_file():
                content = path_obj.read_bytes()
                checksums[p] = hashlib.sha256(content).hexdigest()
        return checksums

    def validate_freeze(self, freeze: HardeningFreezeManifest) -> list[str]:
        errors = []
        if freeze.frozen and not freeze.checksum_manifest:
            errors.append("Checksum manifest is empty for frozen state.")
        return errors
