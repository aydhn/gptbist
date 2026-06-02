# Local Data Import Adapters (Phase 102)

## Overview
The Local Data Import subsystem allows researchers to ingest CSV, JSON, JSONL, Parquet, and SQLite data sets safely and consistently without web scraping, API connections, or live interactions.

## Key Features
- **Format Inference:** Auto-detects formats securely.
- **Schema Mapping:** Automatically maps non-standard column names (e.g., "Kapanış") to standard names ("close").
- **Dry-Run by Default:** No destructive actions or file persistence without explicit `--confirm`.
- **Large File Support:** Out-of-the-box chunking support (enabled via `DATA_IMPORT_CHUNKING_ENABLED`).
- **Research Only:** Import success and validation results strictly output metadata. No investment advice or trading instruction is implied or returned.

## Data Catalog & Feature Store Integration
Normalized data can be registered directly into the Data Catalog. Output Parquet files serve as clean downstream sources for the Feature Store and offline research notebooks.

## QA & Ops
Import jobs log statuses and provenance checksums that can be polled by Ops readiness gates and Healthchecks.
