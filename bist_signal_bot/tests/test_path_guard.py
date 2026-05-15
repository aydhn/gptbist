import pytest
from pathlib import Path
from bist_signal_bot.security.path_guard import PathGuard
from bist_signal_bot.core.exceptions import PathSecurityError

def test_path_guard_catches_traversal(tmp_path):
    guard = PathGuard([tmp_path])

    with pytest.raises(PathSecurityError):
        guard.assert_no_path_traversal(Path("../outside.txt"))

def test_path_guard_safe_join_blocks_escape(tmp_path):
    guard = PathGuard([tmp_path])

    with pytest.raises(PathSecurityError):
        guard.safe_join(tmp_path, "..", "etc", "passwd")

    # Safe join should work
    safe_path = guard.safe_join(tmp_path, "models", "my_model.pkl")
    assert tmp_path in safe_path.parents

def test_path_guard_model_path_allowed_dir(tmp_path):
    allowed_dir = tmp_path / "allowed_models"
    allowed_dir.mkdir()
    guard = PathGuard([allowed_dir])

    outside_path = tmp_path / "outside_model.pkl"
    with pytest.raises(PathSecurityError):
        guard.validate_model_path(outside_path)

    inside_path = allowed_dir / "safe_model.pkl"
    guard.validate_model_path(inside_path)  # Should pass
