# Config Registry (Phase 68)

## Overview
The Config Registry centralizes settings, feature flags, runtime profiles, and safe toggles across the application. It provides validation, snapshotting, diffing, and drift detection to ensure a stable and compliant operational environment.

## Key Features
- **Schema Validation**: Ensures all configuration entries meet defined types, limits, and safety standards.
- **Safety Levels**: Configs are categorized into SAFE, CAUTION, SENSITIVE, DANGEROUS, and FORBIDDEN levels to prevent unsafe operations.
- **Feature Flags**: Manage toggles for various modules with dependencies and conflicts checks.
- **Runtime Profiles**: Apply standardized modes like `RESEARCH_ONLY` or `TELEGRAM_DRY_RUN` to enforce operational bounds.
- **Secret Hygiene**: Sensitive values are redacted in outputs and snapshots to prevent leakage.
- **Snapshots & Diffs**: Capture current configuration states and compare them against baselines to track changes.
- **Drift Detection**: Identify unintended or unsafe deviations from expected configurations.
- **Config Gates**: Validate configurations before executing runtime tasks or deployments to block forbidden states.

## Important Constraints
- **Research Only**: The config registry does not generate investment advice.
- **No Real Orders**: Configurations cannot enable real market execution or broker APIs.
- **No Scraping/Paid APIs**: HTML scraping and paid external services are blocked by schema validation.

## Usage
The CLI provides commands to manage and view the config registry:

- List configurations: `python -m bist_signal_bot config-registry list`
- Show a configuration: `python -m bist_signal_bot config-registry show [KEY]`
- Validate configurations: `python -m bist_signal_bot config-registry validate`
- View feature flags: `python -m bist_signal_bot config-registry flags`
- Preview a profile: `python -m bist_signal_bot config-registry profile-preview RESEARCH_ONLY`
- Apply a profile: `python -m bist_signal_bot config-registry profile-apply RESEARCH_ONLY --confirm`
- Create a snapshot: `python -m bist_signal_bot config-registry snapshot`
- Detect drift: `python -m bist_signal_bot config-registry drift`
