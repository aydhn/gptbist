# Running on Windows

This guide explains how to properly set up and run the BIST Signal Bot on Windows using the automated scripts.

## Quick Start

1. Ensure you have **Python 3.10+** installed and added to your `PATH`.
2. Double-click `start_windows.bat` from the root directory of the repository.

## What the Script Does

The `start_windows.bat` script safely manages the environment by automating the following:

- Validates Python installation and repository root.
- Creates and validates the Python virtual environment (`.venv`).
- Installs and updates required dependencies (`requirements.txt`) securely.
- Ensures a valid `.env` configuration file exists.
- Runs an automated `windows_healthcheck.py` to verify modules, database paths, and secrets.
- Launches the offline `bootstrap demo` upon success, logging outputs cleanly.

## Logging and Troubleshooting

If the startup sequence fails, you can find detailed information in the `logs` folder:
- `logs/healthcheck.log` - Errors encountered during validation checks.
- `logs/runtime.log` - Execution log of the bot.

All sensitive data, virtual environments, and logs are automatically excluded via `.gitignore`.
