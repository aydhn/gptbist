import pytest
from pathlib import Path
from bist_signal_bot.packaging.installers import InstallerGenerator

def test_generate_windows_install_script(tmp_path):
    gen = InstallerGenerator()
    out_file = tmp_path / "install.ps1"
    gen.generate_windows_install_script(out_file)
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "Python version check" in content
    assert ".\\.venv\\Scripts" in content
    assert "requirements.txt" in content
    assert "token" not in content.lower()

def test_generate_unix_install_script(tmp_path):
    gen = InstallerGenerator()
    out_file = tmp_path / "install.sh"
    gen.generate_unix_install_script(out_file)
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "python3 -c" in content
    assert ".venv/bin/activate" in content
    assert "requirements.txt" in content
    assert "token" not in content.lower()

def test_generate_all_scripts(tmp_path):
    gen = InstallerGenerator()
    scripts = gen.generate_all_scripts(tmp_path)
    assert "install.ps1" in scripts
    assert "install.sh" in scripts
    assert "run_healthcheck.sh" in scripts
    assert "runtime_once.sh" in scripts
    assert len(scripts) == 8
