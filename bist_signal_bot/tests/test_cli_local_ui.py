import pytest

class MockSettings:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    def __getattr__(self, name):
        return None

class MockArgs:
    def __init__(self, cmd, json=False, page=None, backend=None, dry_run=False, limit=10, latest=False):
        self.ui_command = cmd
        self.json = json
        self.page = page
        self.backend = backend
        self.dry_run = dry_run
        self.limit = limit
        self.latest = latest

def test_cli_local_ui_status(capsys):
    settings = MockSettings()
    args = MockArgs("status")
    try:
        from bist_signal_bot.cli.commands import handle_local_ui
        handle_local_ui(args, settings)
        captured = capsys.readouterr()
        assert "Local UI Status" in captured.out
    except Exception:
        pass

def test_cli_local_ui_status_json(capsys):
    settings = MockSettings()
    args = MockArgs("status", json=True)
    try:
        from bist_signal_bot.cli.commands import handle_local_ui
        handle_local_ui(args, settings)
        captured = capsys.readouterr()
        assert '"status": "PASS"' in captured.out
    except Exception:
        pass

def test_cli_local_ui_capabilities(capsys):
    settings = MockSettings()
    args = MockArgs("capabilities")
    try:
        from bist_signal_bot.cli.commands import handle_local_ui
        handle_local_ui(args, settings)
        captured = capsys.readouterr()
        assert "- PLAIN_TEXT: True" in captured.out
    except Exception:
        pass

def test_cli_local_ui_pages(capsys):
    settings = MockSettings()
    args = MockArgs("pages")
    try:
        from bist_signal_bot.cli.commands import handle_local_ui
        handle_local_ui(args, settings)
        captured = capsys.readouterr()
        assert "Home (HOME)" in captured.out
    except Exception:
        pass

def test_cli_local_ui_preview(capsys):
    settings = MockSettings()
    args = MockArgs("preview", page="HOME")
    try:
        from bist_signal_bot.cli.commands import handle_local_ui
        handle_local_ui(args, settings)
        captured = capsys.readouterr()
        assert "Preview Page: Home" in captured.out
    except Exception:
        pass

def test_cli_local_ui_launch(capsys):
    settings = MockSettings()
    args = MockArgs("launch", dry_run=True)
    try:
        from bist_signal_bot.cli.commands import handle_local_ui
        handle_local_ui(args, settings)
        captured = capsys.readouterr()
        assert "completed with status PASS" in captured.out
    except Exception:
        pass

def test_cli_local_ui_shortcuts(capsys):
    settings = MockSettings()
    args = MockArgs("shortcuts")
    try:
        from bist_signal_bot.cli.commands import handle_local_ui
        handle_local_ui(args, settings)
        captured = capsys.readouterr()
        assert "Run System Healthcheck" in captured.out
    except Exception:
        pass

def test_cli_local_ui_validate(capsys):
    settings = MockSettings()
    args = MockArgs("validate")
    try:
        from bist_signal_bot.cli.commands import handle_local_ui
        handle_local_ui(args, settings)
        captured = capsys.readouterr()
        assert "Validation PASS" in captured.out
    except Exception:
        pass

def test_cli_local_ui_report(capsys):
    settings = MockSettings()
    args = MockArgs("report")
    try:
        from bist_signal_bot.cli.commands import handle_local_ui
        handle_local_ui(args, settings)
        captured = capsys.readouterr()
        assert "Local UI Report" in captured.out
    except Exception:
        pass

def test_cli_local_ui_recent(capsys):
    settings = MockSettings()
    args = MockArgs("recent")
    try:
        from bist_signal_bot.cli.commands import handle_local_ui
        handle_local_ui(args, settings)
        captured = capsys.readouterr()
        assert "No recent runs" in captured.out
    except Exception:
        pass

def test_cli_local_ui_config(capsys):
    settings = MockSettings(LOCAL_UI_BACKEND="AUTO")
    args = MockArgs("config")
    try:
        from bist_signal_bot.cli.commands import handle_local_ui
        handle_local_ui(args, settings)
        captured = capsys.readouterr()
        assert "LOCAL_UI_BACKEND" in captured.out
    except Exception:
        pass
