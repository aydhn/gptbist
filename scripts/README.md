# Installer and Execution Scripts

These generated scripts help you quickly set up and run the BIST Signal Bot.

## Available Scripts

*   `install.ps1` / `install.sh`: Creates a virtual environment and installs dependencies.
*   `run_healthcheck.ps1` / `run_healthcheck.sh`: Runs the system healthcheck.
*   `run_quality.ps1` / `run_quality.sh`: Runs the automated quality smoke tests.
*   `runtime_once.ps1` / `runtime_once.sh`: Executes a single pass of the runtime orchestrator.

## Security Warnings
*   **Never commit your `.env` file.**
*   Be careful when entering sensitive information (like Telegram tokens) into your configuration.
*   These scripts are designed for local research and testing. They do **not** configure or connect to real broker APIs. No real orders are sent.
