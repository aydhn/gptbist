from pathlib import Path
from datetime import datetime
import pandas as pd
import hashlib
import uuid
import shutil
from bist_signal_bot.qa.models import QAFixtureManifest, QAFixtureKind
from bist_signal_bot.core.exceptions import QAFixtureError
from bist_signal_bot.config.settings import get_settings

class QAFixtureManager:
    def __init__(self, settings=None, base_dir: Path | None = None):
        self.settings = settings or get_settings()
        self.base_dir = base_dir

    def fixture_root(self) -> Path:
        root = Path(self.settings.QA_FIXTURE_ROOT)
        if not root.is_absolute() and self.base_dir:
            return self.base_dir / root
        return root

    def create_fixture_manifest(self) -> QAFixtureManifest:
        root = self.fixture_root()
        if not root.exists():
            raise QAFixtureError(f"Fixture root {root} does not exist.")

        fixtures = {}
        symbols = self.settings.QA_SYNTHETIC_SYMBOLS.split(",")
        date_range = {"start": self.settings.QA_SYNTHETIC_START_DATE}

        return QAFixtureManifest(
            manifest_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            fixture_root=str(root),
            fixtures=fixtures,
            symbols=symbols,
            date_range=date_range
        )

    def validate_fixture_manifest(self, manifest: QAFixtureManifest) -> list[str]:
        warnings = []
        if not Path(manifest.fixture_root).exists():
            warnings.append(f"Fixture root {manifest.fixture_root} missing.")
        return warnings

    def copy_fixtures_to_temp(self, tmp_root: Path) -> QAFixtureManifest:
        src = self.fixture_root()
        if src.exists():
            shutil.copytree(src, tmp_root, dirs_exist_ok=True)
        manifest = self.create_fixture_manifest()
        manifest.fixture_root = str(tmp_root)
        return manifest

    def fixture_path(self, kind: QAFixtureKind, name: str | None = None) -> Path:
        root = self.fixture_root()
        fname = name or f"synthetic_{kind.value.lower()}.csv"
        return root / fname

    def load_fixture_dataframe(self, kind: QAFixtureKind, name: str | None = None) -> pd.DataFrame:
        path = self.fixture_path(kind, name)
        if not path.exists():
            raise QAFixtureError(f"Fixture {path} not found.")
        return pd.read_csv(path)

    def checksum_fixture(self, path: Path) -> str:
        if not path.exists():
            return ""
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
