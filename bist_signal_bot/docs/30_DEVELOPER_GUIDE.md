# Developer Guide

## Architecture

The BIST Signal Bot is built as an offline-first research application. It strictly prevents real market executions.

### Modules

* `core`: Shared models and settings
* `scanner`: Batch operations over a symbol universe
* `risk`: Applies sizing rules and rejects trades based on volatility/regime
* `scenarios`: Sandboxed test cases and golden regression
* `release`: MVP Readiness and safe launch checking

## Adding a Feature

1. Consider how it impacts `settings.py` (all new settings must have safe defaults).
2. Consider how it interacts with the `release/` module. For example, if it involves external API calls, you must add it to the `ForbiddenActionGuard` in `security`.
3. Add a scenario test case under `scenarios/registry.py`.
