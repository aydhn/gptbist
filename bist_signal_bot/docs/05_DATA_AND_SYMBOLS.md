# Data and Symbols

## Data Provider V2

The `bist_signal_bot` utilizes a local-first approach to market data, managed by the Data Provider V2 architecture.
This system is designed to provide high-quality data through local storage, caching, and fallback mechanisms while strictly forbidding HTML scraping and web scraping.

### Features
- **Local Import**: Load market data directly from local CSV or Parquet files.
- **Incremental Updates**: Update existing local data efficiently by only fetching missing data (gaps) from external sources.
- **Provider Fallback**: A robust fallback router (`FallbackProviderRouter`) automatically switches to secondary providers (e.g., from `Local File Provider` to `YFinance Provider`) if a provider fails or returns incomplete data.
- **Data Lineage**: Detailed metadata (`DataLineageSource`) is kept for all imported and fetched data, ensuring tracebility (e.g., source, time fetched, checksum).
- **Health Tracking**: Provider success rates, latencies, and failures are continuously monitored and logged (`ProviderHealthTracker`).
- **Freshness Reports**: Identify stale data before running research pipelines.

### Usage
Run `python -m bist_signal_bot data --help` to explore the CLI commands for importing, updating, checking freshness, comparing sources, and viewing data lineage.
