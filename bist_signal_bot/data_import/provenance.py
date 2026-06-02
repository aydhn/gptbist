from typing import Any
from pathlib import Path
import hashlib

from bist_signal_bot.data_import.models import ImportJob
from bist_signal_bot.core.exceptions import ImportProvenanceError

class ImportProvenanceBuilder:
    def __init__(self, settings: Any = None, base_dir: Path | None = None):
        self.settings = settings
        self.base_dir = base_dir

    def build_import_provenance(self, job: ImportJob) -> dict[str, Any]:
        source_chk = self.source_checksum(Path(job.source.path)) if job.source.path else None

        norm_chk = None
        if job.normalized_result and job.normalized_result.output_path:
             norm_chk = self.normalized_checksum(Path(job.normalized_result.output_path))

        return {
            "job_id": job.job_id,
            "dataset_type": job.source.dataset_type,
            "source_path": job.source.path,
            "source_checksum": source_chk,
            "normalized_path": job.normalized_result.output_path if job.normalized_result else None,
            "normalized_checksum": norm_chk,
            "status": job.status,
            "timestamp": job.finished_at.isoformat() if job.finished_at else None,
            "lineage": self.lineage_edges(job)
        }

    def source_checksum(self, path: Path) -> str | None:
        return self._compute_sha256(path)

    def normalized_checksum(self, path: Path | None) -> str | None:
        if not path:
             return None
        return self._compute_sha256(path)

    def lineage_edges(self, job: ImportJob) -> list[dict[str, Any]]:
        edges = []
        if job.normalized_result and job.normalized_result.output_path:
            edges.append({
                "from": f"file:{job.source.path}",
                "to": f"file:{job.normalized_result.output_path}",
                "type": "NORMALIZATION",
                "job_id": job.job_id
            })
        return edges

    def _compute_sha256(self, path: Path) -> str | None:
        if not path.is_file():
            return None
        try:
            sha256_hash = hashlib.sha256()
            with open(path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return None
