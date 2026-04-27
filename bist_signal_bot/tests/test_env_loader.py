from bist_signal_bot.config.env_loader import env_file_status, load_env_file


def test_load_env_file_not_found(tmp_path):
    assert load_env_file(tmp_path / ".env.nonexistent") is False

def test_load_env_file_success(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("TEST_VAR=123")
    assert load_env_file(env_file) is True

def test_env_file_status_not_found(tmp_path):
    status = env_file_status(tmp_path / ".env.nonexistent")
    assert status["exists"] is False
    assert status["loaded_possible"] is False
