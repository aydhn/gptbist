import pytest
from pathlib import Path
from bist_signal_bot.performance.cache import CacheInspector
from bist_signal_bot.performance.models import CachePolicy
from bist_signal_bot.config.settings import Settings

class MockInspector(CacheInspector):
    def _get_target_dirs(self) -> list[Path]:
        return [self.base_dir / "cache"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hack path guard
        self.path_guard.ensure_safe_path = lambda p: True

def test_cache_inspector_scan(tmp_path):
    settings = Settings()
    settings.PERFORMANCE_PROTECT_MODEL_ARTIFACTS = True
    inspector = MockInspector(settings, tmp_path)

    d = tmp_path / "cache"
    d.mkdir()
    (d / "test.tmp").write_text("hello")
    (d / "model.pkl").write_text("protected")

    rep = inspector.scan_cache_dirs()
    assert rep.entry_count == 2
    assert rep.safe_delete_count == 1

def test_cache_inspector_cleanup_dry_run(tmp_path):
    inspector = MockInspector(base_dir=tmp_path)
    d = tmp_path / "cache"
    d.mkdir(exist_ok=True)
    f = d / "test.tmp"
    f.write_text("hello")

    rep = inspector.cleanup(CachePolicy.CLEAN_TEMP_ONLY, 30, dry_run=True, confirm=False)
    assert f.exists()
    assert rep.safe_delete_count == 1

def test_cache_inspector_cleanup_exec(tmp_path):
    inspector = MockInspector(base_dir=tmp_path)
    d = tmp_path / "cache"
    d.mkdir(exist_ok=True)
    f = d / "test.tmp"
    f.write_text("hello")

    rep = inspector.cleanup(CachePolicy.CLEAN_TEMP_ONLY, 30, dry_run=False, confirm=True)
    assert not f.exists()
    assert rep.safe_delete_count == 1
    assert len(rep.deleted_files) == 1

def test_cache_cleanup_requires_confirm(tmp_path):
    inspector = MockInspector(base_dir=tmp_path)
    with pytest.raises(ValueError):
        inspector.cleanup(CachePolicy.CLEAN_TEMP_ONLY, 30, dry_run=False, confirm=False)
