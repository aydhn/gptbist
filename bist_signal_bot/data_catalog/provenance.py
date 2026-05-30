import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from bist_signal_bot.data_catalog.models import DatasetRecord, SourceProvenance
from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.security.path_guard import PathGuard


class SourceProvenanceTracker:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or get_settings()
        self.base_dir = base_dir
        self.path_guard = PathGuard(settings=self.settings, base_dir=self.base_dir)

    def create_provenance(
        self,
        dataset: DatasetRecord,
        source_name: str,
        source_type: str,
        source_path: str | None = None,
        source_ref: str | None = None,
    ) -> SourceProvenance:

        redacted_source_path = None
        checksum_val = None

        if source_path:
            p = Path(source_path)
            redacted_source_path = str(self.path_guard.redact_path(p))
            if p.exists() and p.is_file():
                checksum_val = self.checksum_path(p)

        return SourceProvenance(
            provenance_id=f"prov_{uuid.uuid4().hex[:12]}",
            dataset_id=dataset.dataset_id,
            source_name=source_name,
            source_type=source_type,
            source_path=redacted_source_path,
            source_ref=source_ref,
            imported_at=datetime.now(timezone.utc),
            imported_by="system", # typically generic unless we add auth context
            checksum=checksum_val,
            trust_level=self.trust_level(source_name, source_type)
        )

    def checksum_path(self, path: Path) -> str | None:
        if not path.exists() or not path.is_file():
            return None

        hash_md5 = hashlib.md5()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return None

    def trust_level(self, source_name: str, source_type: str) -> str:
        # Define basic trust levels. In a real system this might look at a registry.
        name = source_name.lower()
        if "yfinance" in name or "official" in name or "kap" in name:
            return "HIGH"
        if "scraping" in name or "unverified" in name:
            return "LOW"
        return "MEDIUM"

    def provenance_for_dataset(self, dataset_id: str) -> list[SourceProvenance]:
        # Typically requires store lookup. Here we just return empty as interface
        return []

    def validate_provenance(self, provenance: SourceProvenance) -> list[str]:
        errors = []
        if not provenance.source_name:
            errors.append("Source name is required.")
        return errors
