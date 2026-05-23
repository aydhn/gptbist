from bist_signal_bot.deployment.platforms import PlatformCommandBuilder

def test_platform_command_builder():
    builder = PlatformCommandBuilder()

    # Test windows
    win_examples = builder.windows_task_scheduler_examples()
    assert len(win_examples) > 0
    assert "dry-run" in win_examples[0]["action"]
    assert "broker" not in win_examples[0]["action"].lower()

    # Test linux
    linux_examples = builder.linux_cron_examples()
    assert len(linux_examples) > 0
    assert "dry-run" in linux_examples[0]["action"]

    # Platform detection
    plat = builder.detect_platform()
    assert plat in ["windows", "linux", "macos"]

    # Safe shell command
    cmd = builder.safe_shell_command(["python", "-m", "bist_signal_bot"])
    assert cmd == "python -m bist_signal_bot"
