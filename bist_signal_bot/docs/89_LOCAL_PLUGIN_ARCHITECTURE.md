# Phase 109 - Local Plugin Architecture

## Mimari
The plugin architecture uses a safe, metadata-first approach to discovering and loading plugins without arbitrary code execution. It uses a PluginManifest as the source of truth, validates capabilities and contracts, and ensures dangerous operations are blocked by default.

## Plugin Kinds
- STRATEGY
- SIGNAL
- INDICATOR
- FEATURE
- REPORT_SECTION
- vb.

## Safe Discovery & Loader
The discovery engine only reads `plugin.json` manifests.
The loader defaults to `SAFE_METADATA_ONLY` or `DRY_RUN` to prevent unwanted side-effects.

## Governance
Plugins are assessed for dangerous capabilities (e.g. EXTERNAL_NETWORK, BROKER_ACCESS) and unsafe language (e.g. "guarantee", "risk-free") to ensure compliance with the "research-only" mandate.
