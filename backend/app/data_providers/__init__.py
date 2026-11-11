"""External market-data providers (Milestone 2+).

No provider is connected in Milestone 1. Every provider must implement `MarketDataProvider`,
label everything it returns as DataSource.REAL only after a successful authenticated fetch,
and write a row to data_ingestion_logs for each run. Never fabricate a live feed.
"""
