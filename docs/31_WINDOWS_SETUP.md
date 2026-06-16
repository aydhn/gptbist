# 31. Running on Windows

This guide explains how to set up and run the BIST Signal Bot on Windows using the
automated `start_windows.bat` script.

## Quick Start

1. Install **Python 3.11+** and make sure it is on your `PATH`.
2. Double-click `start_windows.bat` from the repository root (or run it from a terminal).

## What `start_windows.bat` Does

The script bootstraps a fully isolated environment and runs an offline smoke test:

1. Validates the Python installation and that you are in the repository root (`pyproject.toml` present).
2. Creates and validates the virtual environment (`.venv`).
3. Upgrades `pip`, `setuptools`, `wheel`.
4. Installs runtime dependencies from `requirements.txt` **and** ML dependencies from
   `requirements-ml.txt` (the ML extras are required for the autonomous learning loop).
5. Creates a `.env` from `.env.example` if one does not exist.
6. Ensures `.venv/`, `logs/`, and `.env` are present in `.gitignore`.
7. Runs `scripts/windows_healthcheck.py` and writes the result to `logs/healthcheck.log`.
8. On success, runs the offline demo (`python -m bist_signal_bot bootstrap demo`) and logs to
   `logs/runtime.log`.

> **Safety:** The bot is **research / paper-only**. No real broker connection is made and no real
> orders are ever routed (see [00_DISCLAIMER.md](00_DISCLAIMER.md) and [20_SECURITY.md](20_SECURITY.md)).

## Verifying the Install Manually

```bat
.venv\Scripts\python.exe -m bist_signal_bot version
.venv\Scripts\python.exe -m bist_signal_bot healthcheck
.venv\Scripts\python.exe -m bist_signal_bot bootstrap demo
```

A healthy install prints real values (not `mock_value`) and a non-error exit code.

## Logging and Troubleshooting

If the startup sequence fails, inspect the `logs` folder:

- `logs/healthcheck.log` — validation / dependency / import check results.
- `logs/runtime.log` — execution log of the bot and the offline demo.

Common issues:

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: typer` | Dependencies not installed | Re-run `start_windows.bat`, or `pip install -r requirements.txt` |
| Healthcheck prints `mock_value` | Stale config layer | Pull latest; `config/settings.py` now reads `.env` for real |
| `invalid choice: 'bootstrap'` | Stale launcher | Pull latest; the demo command is now wired into the real CLI |

All sensitive data, virtual environments, and logs are excluded via `.gitignore`.
