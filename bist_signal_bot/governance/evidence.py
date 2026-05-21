import hashlib
import json
import logging
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.core.exceptions import EvidencePackError
from bist_signal_bot.governance.models import EvidencePackManifest, EvidencePackRequest

logger = logging.getLogger(__name__)

class EvidencePackBuilder:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or get_settings()
        self.base_dir = base_dir

    def build_pack(self, request: EvidencePackRequest) -> EvidencePackManifest:
        start_time = datetime.utcnow()
        safe_files, excluded_files = self.collect_files(request)

        pack_id = f"epk_{uuid.uuid4().hex[:8]}"
        archive_path = None

        if not request.dry_run:
            if not request.output_dir:
                from bist_signal_bot.storage.paths import get_governance_dir
                out_dir = get_governance_dir(self.settings) / "evidence" / datetime.utcnow().strftime("%Y%m%d") / pack_id
            else:
                out_dir = Path(request.output_dir)
            out_dir.mkdir(parents=True, exist_ok=True)

            try:
                archive_path = self.create_archive(safe_files, out_dir, pack_id)
            except Exception as e:
                logger.error(f"Failed to create archive: {e}")
                raise EvidencePackError(f"Failed to create archive: {e}")

        checksum = None
        if archive_path and archive_path.exists():
            with open(archive_path, "rb") as f:
                checksum = hashlib.sha256(f.read()).hexdigest()

        manifest = EvidencePackManifest(
            pack_id=pack_id,
            pack_name=request.pack_name,
            created_at=start_time,
            files=[{"path": str(f.name), "size": f.stat().st_size if f.exists() else 0} for f in safe_files],
            excluded_files=excluded_files,
            checksum_sha256=checksum,
            archive_path=str(archive_path) if archive_path else None,
            warnings=["Dry run mode enabled. No archive generated."] if request.dry_run else [],
        )

        return manifest

    def collect_files(self, request: EvidencePackRequest) -> tuple[list[Path], list[dict[str, Any]]]:
        safe_files = []
        excluded_files = []

        # Example mock collection. In reality this would traverse specific directories
        # ensuring no .env, .tokens, or other secrets are included

        from bist_signal_bot.storage.paths import get_data_dir
        data_dir = get_data_dir(self.settings)

        # This is a safe path check mock
        if data_dir.exists():
            for p in data_dir.glob("**/*"):
                if not p.is_file():
                    continue

                # Exclude rules
                if p.name.startswith(".env") or "token" in p.name.lower() or "secret" in p.name.lower():
                    excluded_files.append({"path": str(p), "reason": "Secret exclusion"})
                    continue

                if request.include_audit_log and "audit" in p.name.lower():
                    safe_files.append(p)
                elif request.include_research_ledger and "ledger" in p.name.lower():
                    safe_files.append(p)
                elif request.include_policy and "policy" in p.name.lower():
                    safe_files.append(p)

        return safe_files, excluded_files

    def write_manifest(self, manifest: EvidencePackManifest, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / "evidence_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))
        return manifest_path

    def create_archive(self, files: list[Path], output_dir: Path, pack_id: str) -> Path:
        archive_path = output_dir / f"{pack_id}.zip"

        # Ensure no absolute paths in zip
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files:
                if file_path.exists():
                    zipf.write(file_path, arcname=file_path.name)

        return archive_path
