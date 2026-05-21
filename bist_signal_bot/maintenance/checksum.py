import hashlib
from pathlib import Path
from bist_signal_bot.core.exceptions import ChecksumError
from bist_signal_bot.maintenance.models import BackupFileEntry

class ChecksumManager:
    @staticmethod
    def sha256_file(path: Path) -> str:
        if not path.is_file():
            raise ChecksumError(f"Cannot calculate checksum. Not a file: {path}")

        sha256_hash = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                # Read and update hash string value in blocks of 4K
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            raise ChecksumError(f"Failed to calculate checksum for {path}: {e}")

    @staticmethod
    def sha256_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def verify_file(path: Path, expected_sha256: str) -> bool:
        try:
            actual_sha256 = ChecksumManager.sha256_file(path)
            return actual_sha256 == expected_sha256
        except ChecksumError:
            return False

    @staticmethod
    def checksum_manifest_entries(entries: list[BackupFileEntry], base_dir: Path) -> list[BackupFileEntry]:
        updated_entries = []
        for entry in entries:
            if not entry.included:
                updated_entries.append(entry)
                continue

            full_path = base_dir / entry.relative_path
            try:
                entry.checksum_sha256 = ChecksumManager.sha256_file(full_path)
            except ChecksumError as e:
                entry.included = False
                entry.excluded_reason = f"Checksum failed: {e}"
            updated_entries.append(entry)

        return updated_entries
