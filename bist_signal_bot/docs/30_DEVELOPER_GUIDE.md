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

### Data Provider V2

The new Data Provider V2 architecture introduces a robust, modular approach to data fetching:
- Implement new providers by extending `BaseMarketDataProviderV2`.
- `ProviderRequest` and `ProviderResponse` are standardized for all data fetches.
- Integration tests must use `MockMarketDataProvider` or local files; real network calls are prohibited during testing.
- When creating a new provider, ensure it registers its health via `ProviderHealthTracker` and logs its operations using the `AuditEventBuilder`.
