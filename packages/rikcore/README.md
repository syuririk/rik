# rikcore

Producer side of the rik ecosystem. Fetches data from multiple sources,
normalizes it to rikschema standard records, validates, and emits.

- **sources/** — adapters (yfinance, FinanceDataReader, manual) satisfying `rikschema.Source`.
- **normalize/** — symbol resolution, calendar alignment, field mapping, transforms.
- **validate/** — cross-record checks (duplicates, gaps).
- **pipeline/** — `Orchestrator`: fetch → normalize → validate → emit.
- **emit/** — `RecordsEmitter`, `DictEmitter`, `DataFrameEmitter`.

Heavy source deps (yfinance, finance-datareader, pandas) are optional extras and imported
lazily, so the core and its tests load without them.
