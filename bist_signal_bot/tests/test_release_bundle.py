import pytest
from pathlib import Path
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.packaging.release import ReleaseBundleBuilder
from bist_signal_bot.packaging.models import PackagingFormat, ReleaseBundleStatus

def test_build_release_bundle_manifest_only(tmp_path):
    settings = Settings(
        PACKAGING_PROJECT_NAME="test-bot",
        PACKAGING_EXCLUDE_DATA_DIR=True,
        PACKAGING_INCLUDE_INSTALLERS=False
    )

    builder = ReleaseBundleBuilder(settings=settings)
    builder.base_dir = tmp_path # Override for test
    (tmp_path / "README.md").touch()

    res = builder.build_release_bundle(
        format=PackagingFormat.MANIFEST_ONLY,
        run_quality=False,
        run_security=False,
        output_dir=tmp_path / "out"
    )

    assert res.status in [ReleaseBundleStatus.SUCCESS, ReleaseBundleStatus.PARTIAL_SUCCESS]
    assert res.format == PackagingFormat.MANIFEST_ONLY
    assert "manifest" in res.output_files

def test_create_zip_bundle(tmp_path):
    settings = Settings(PACKAGING_PROJECT_NAME="test-bot")
    builder = ReleaseBundleBuilder(settings=settings)
    builder.base_dir = tmp_path

    (tmp_path / "README.md").write_text("Hello")
    (tmp_path / ".env").write_text("SECRET=123")

    manifest = builder.manifest_builder.build_manifest(
        include_quality=False, include_security=False, include_environment=False
    )
    manifest.included_files = ["README.md", ".env"]
    manifest.excluded_patterns = [".env"]

    out_dir = tmp_path / "out"
    out_dir.mkdir()

    zip_path = builder.create_zip_bundle(manifest, out_dir)
    assert zip_path.exists()

    import zipfile
    with zipfile.ZipFile(zip_path, 'r') as zf:
        names = zf.namelist()
        assert "README.md" in names
        assert ".env" not in names
