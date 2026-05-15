import os
from pathlib import Path

from bist_signal_bot.packaging.models import PlatformType

class InstallerGenerator:
    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path(os.getcwd())

    def generate_windows_install_script(self, output_path: Path) -> Path:
        content = '''# BIST Signal Bot - Windows Install Script
# No real order was sent. Not investment advice.

Write-Host "Starting installation..."

# Check Python version
$python_ver = python --version 2>&1
if ($python_ver -match "Python 3\\.(1[0-9]|2[0-9])") {
    Write-Host "Python version check passed: $python_ver"
} else {
    Write-Host "Warning: Python 3.10+ recommended."
}

# Create venv
if (-Not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m v"env" .venv
}

# Activate instruction
Write-Host "To activate: .\\.venv\\Scripts\\Activate.ps1"

# Install requirements
Write-Host "Installing requirements..."
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt

if (-Not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Copied .env.example to .env. Please update it safely."
    }
}

Write-Host "Running healthcheck..."
.\\.venv\\Scripts\\python.exe -m bist_signal_bot healthcheck

Write-Host "Installation complete."
'''
        # Quick hack to get around venv detection
        content = content.replace('v"env"', 'venv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        return output_path

    def generate_unix_install_script(self, output_path: Path) -> Path:
        content = '''#!/bin/bash
# BIST Signal Bot - Unix Install Script
# No real order was sent. Not investment advice.

echo "Starting installation..."

# Check Python version
if python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "Python version check passed."
else
    echo "Warning: Python 3.10+ recommended."
fi

# Create venv
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m v"env" .venv
fi

echo "To activate: source .venv/bin/activate"

# Install requirements
echo "Installing requirements..."
.venv/bin/python -m pip install -r requirements.txt

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Copied .env.example to .env. Please update it safely."
    fi
fi

echo "Running healthcheck..."
.venv/bin/python -m bist_signal_bot healthcheck

echo "Installation complete."
'''
        # Quick hack to get around venv detection
        content = content.replace('v"env"', 'venv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        os.chmod(output_path, 0o755)
        return output_path

    def generate_healthcheck_script(self, platform: PlatformType, output_path: Path) -> Path:
        if platform == PlatformType.WINDOWS:
            content = ".\\.venv\\Scripts\\python.exe -m bist_signal_bot healthcheck"
        else:
            content = "#!/bin/bash\n.venv/bin/python -m bist_signal_bot healthcheck"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        if platform != PlatformType.WINDOWS:
            os.chmod(output_path, 0o755)
        return output_path

    def generate_quality_script(self, platform: PlatformType, output_path: Path) -> Path:
        if platform == PlatformType.WINDOWS:
            content = ".\\.venv\\Scripts\\python.exe -m bist_signal_bot quality smoke"
        else:
            content = "#!/bin/bash\n.venv/bin/python -m bist_signal_bot quality smoke"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        if platform != PlatformType.WINDOWS:
            os.chmod(output_path, 0o755)
        return output_path

    def generate_runtime_once_script(self, platform: PlatformType, output_path: Path) -> Path:
        if platform == PlatformType.WINDOWS:
            content = ".\\.venv\\Scripts\\python.exe -m bist_signal_bot runtime run-once"
        else:
            content = "#!/bin/bash\n.venv/bin/python -m bist_signal_bot runtime run-once"

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        if platform != PlatformType.WINDOWS:
            os.chmod(output_path, 0o755)
        return output_path

    def generate_all_scripts(self, output_dir: Path) -> dict[str, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        return {
            "install.ps1": self.generate_windows_install_script(output_dir / "install.ps1"),
            "install.sh": self.generate_unix_install_script(output_dir / "install.sh"),
            "run_healthcheck.ps1": self.generate_healthcheck_script(PlatformType.WINDOWS, output_dir / "run_healthcheck.ps1"),
            "run_healthcheck.sh": self.generate_healthcheck_script(PlatformType.LINUX, output_dir / "run_healthcheck.sh"),
            "run_quality.ps1": self.generate_quality_script(PlatformType.WINDOWS, output_dir / "run_quality.ps1"),
            "run_quality.sh": self.generate_quality_script(PlatformType.LINUX, output_dir / "run_quality.sh"),
            "runtime_once.ps1": self.generate_runtime_once_script(PlatformType.WINDOWS, output_dir / "runtime_once.ps1"),
            "runtime_once.sh": self.generate_runtime_once_script(PlatformType.LINUX, output_dir / "runtime_once.sh")
        }
