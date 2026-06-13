# rik

Standardized multi-source market-data pipeline, organized as a uv workspace
monorepo. It pulls daily bars from several data sources, normalizes everything
to one strict record schema, validates the merged batch, and persists it.

```
data sources ──▶ rikcore ──▶ [standard records] ──▶ rikfeed ──▶ storage
 (yfinance,       (fetch +      (rikschema           (persist +
  FinanceDataReader)  normalize)   contract)           schedule)
```

## Packages

| Package     | Role      | Depends on            |
|-------------|-----------|-----------------------|
| `rikschema` | Contract  | pydantic only         |
| `rikcore`   | Producer  | rikschema             |
| `rikfeed`   | Consumer  | rikschema, rikcore    |

`rikschema` is a pure contract package — standard record models, shared enums,
and `Protocol` interfaces. It imports nothing from rikcore or rikfeed, so the
dependency arrow only ever points inward toward the contract.

---

## Table of contents

- [Install](#install)
- [60-second example](#60-second-example)
- [Core concepts](#core-concepts)
- [rikschema API](#rikschema-api)
- [rikcore API](#rikcore-api)
- [rikfeed API](#rikfeed-api)
- [Writing a new source adapter](#writing-a-new-source-adapter)
- [Repository layout](#repository-layout)
- [Versioning](#versioning)
- [License](#license)

---

## Install

### Local development (uv workspace)

```bash
uv sync                 # installs all three packages editable + dev tools
uv run pytest           # runs the whole suite
```

Without uv:

```bash
python scripts/dev_setup.py   # editable installs in dependency order
```

### Single package from GitHub (e.g. Colab)

Workspace resolution only applies to local clones. To install one package from
GitHub use a per-package tag + subdirectory, and install `rikschema` alongside
whatever depends on it:

```bash
pip install "git+https://github.com/syuririk/rik.git@main#subdirectory=packages/rikschema"
pip install "git+https://github.com/syuririk/rik.git@main#subdirectory=packages/rikcore"
pip install "git+https://github.com/syuririk/rik.git@main#subdirectory=packages/rikfeed"
```

Source adapters pull their data libraries lazily, so install those too when you
intend to fetch live data:

```bash
pip install yfinance finance-datareader pandas
```

---

## 60-second example

```python
from datetime import date, timedelta

from rikschema import InstrumentMeta, AssetClass, Currency, SourceId
from rikcore import (
    SymbolResolver, SourceRegistry, YFinanceSource, FDRSource, Orchestrator,
)
from rikfeed import SQLiteStore
from rikfeed.storage import StoreEmitter

# 1. Describe the instruments and their per-source tickers.
universe = [
    InstrumentMeta(
        symbol="KRX:005930", name="Samsung Electronics",
        asset_class=AssetClass.EQUITY, currency=Currency.KRW,
        aliases={SourceId.FDR: "005930", SourceId.YFINANCE: "005930.KS"},
    ),
    InstrumentMeta(
        symbol="INDEX:SPX", name="S&P 500",
        asset_class=AssetClass.EQUITY_INDEX, currency=Currency.NONE,
        aliases={SourceId.YFINANCE: "^GSPC"},
    ),
]

# 2. Wire resolver + sources.
resolver = SymbolResolver(universe)
registry = SourceRegistry()
registry.register(YFinanceSource(resolver))
registry.register(FDRSource(resolver))

# 3. Run the pipeline, writing straight into a SQLite store.
store = SQLiteStore("rikfeed.db")
orch = Orchestrator(registry, StoreEmitter(store))

end = date.today()
result = orch.run(resolver.known_symbols(), end - timedelta(days=10), end)

print(result.report.summary())      # e.g. "[OK] 18 records, 0 duplicate(s), ..."
print("rows written:", result.output)
print("rows in store:", store.count())
```

---

## Core concepts

- **Canonical symbol, many source aliases.** Every instrument has one canonical
  id (`KRX:005930`, `INDEX:SPX`, `ETF:TLT`). Each source maps it to its own
  native ticker. The resolver translates both directions, which is how records
  from different sources merge cleanly.
- **Records are immutable and strict.** Every `StandardRecord` is frozen,
  forbids extra fields, and forces a timezone-aware KST timestamp at
  construction — a naive datetime is rejected.
- **Native values, explicit transforms.** Prices stay in their source currency.
  Any FX/scale conversion is an opt-in pipeline step, never automatic.
- **fetch / to_standard split.** A source adapter separates I/O (`fetch`, may
  hit the network) from the pure transform (`to_standard`, no I/O), so
  normalization is unit-testable with fixtures.
- **Per-source routing.** The orchestrator only asks a source for symbols it can
  actually serve, so an index symbol never reaches a KR-equities-only source.

---

## rikschema API

```python
import rikschema
rikschema.__version__   # "0.1.0"
```

### Records

All records subclass `StandardRecord`, which contributes four shared fields and
the KST/strictness invariants:

| Field        | Type         | Notes                                          |
|--------------|--------------|------------------------------------------------|
| `symbol`     | `str`        | canonical id; stripped, must be non-empty      |
| `timestamp`  | `datetime`   | must be tz-aware; auto-converted to KST        |
| `source`     | `SourceId`   | provenance                                     |
| `asset_class`| `AssetClass` | coarse classification                          |

Construction rules enforced by the model:

```python
from datetime import datetime, timezone
from rikschema import OHLCVRecord, SourceId, AssetClass, Currency

rec = OHLCVRecord(
    symbol="KRX:005930",
    timestamp=datetime(2026, 6, 4, 12, 0, tzinfo=timezone.utc),  # -> KST
    source=SourceId.FDR,
    asset_class=AssetClass.EQUITY,
    open=349000, high=366000, low=348000, close=351500,
    volume=34_771_037, currency=Currency.KRW,
)

rec.timestamp           # 2026-06-04 21:00:00+09:00 (converted from UTC)
rec.model_dump()        # dict; rec.model_dump(mode="json") for JSON-safe

# These all raise:
# OHLCVRecord(..., timestamp=datetime(2026,6,4,12,0))      # naive -> ValueError
# OHLCVRecord(..., high=90, low=95)                        # high<low -> ValueError
# OHLCVRecord(..., extra_field=1)                          # extra -> ValueError
# rec.close = 999                                          # frozen -> Error
```

**`OHLCVRecord`** — one price/volume bar.

| Field      | Type        | Default          |
|------------|-------------|------------------|
| `open`     | `float >=0` | required         |
| `high`     | `float >=0` | required         |
| `low`      | `float >=0` | required         |
| `close`    | `float >=0` | required         |
| `volume`   | `float >=0` | `0.0`            |
| `currency` | `Currency`  | `Currency.NONE`  |
| `adjusted` | `bool`      | `False`          |

Cross-field validation: `low <= open <= high`, `low <= close <= high`,
`high >= low`.

**`FundamentalRecord`** — one fundamental metric observation (long format).

| Field         | Type          | Default         |
|---------------|---------------|-----------------|
| `metric`      | `str`         | required        |
| `value`       | `float`       | required        |
| `period_type` | `PeriodType`  | required        |
| `period_end`  | `date`        | required        |
| `currency`    | `Currency`    | `Currency.NONE` |
| `unit`        | `str or None` | `None`          |

```python
from datetime import date, datetime, timezone
from rikschema import FundamentalRecord, PeriodType, SourceId, AssetClass, Currency

FundamentalRecord(
    symbol="KRX:005930", timestamp=datetime.now(timezone.utc),
    source=SourceId.DART, asset_class=AssetClass.EQUITY,
    metric="revenue", value=2.79e14,
    period_type=PeriodType.ANNUAL, period_end=date(2025, 12, 31),
    currency=Currency.KRW,
)
```

**`MacroRecord`** — one macro indicator observation.

| Field                 | Type          | Default |
|-----------------------|---------------|---------|
| `indicator`           | `str`         | required|
| `value`               | `float`       | required|
| `frequency`           | `Frequency`   | required|
| `unit`                | `str or None` | `None`  |
| `seasonally_adjusted` | `bool`        | `False` |

### Enums

```python
from rikschema import AssetClass, Currency, SourceId
from rikschema import PeriodType, Frequency   # record-specific
```

- `AssetClass`: `EQUITY`, `EQUITY_INDEX`, `ETF`, `BOND`, `COMMODITY`, `FX`,
  `CRYPTO`, `MACRO`, `OTHER`
- `Currency`: `KRW`, `USD`, `EUR`, `JPY`, `GBP`, `CNY`, `HKD`, `NONE`
  (`NONE` for unit-less series like indices/ratios)
- `SourceId`: `YFINANCE`, `FDR`, `DART`, `OECD`, `MANUAL`
- `PeriodType`: `ANNUAL`, `QUARTERLY`, `TTM`, `POINT`
- `Frequency`: `DAILY`, `WEEKLY`, `MONTHLY`, `QUARTERLY`, `ANNUAL`

All are `StrEnum`, so `SourceId.FDR == "fdr"` and `SourceId("fdr")` both work.

### InstrumentMeta

Reference data (not a time-series record). Carries the cross-source aliases the
resolver uses.

| Field         | Type                   | Default          |
|---------------|------------------------|------------------|
| `symbol`      | `str`                  | required         |
| `name`        | `str`                  | required         |
| `asset_class` | `AssetClass`           | required         |
| `currency`    | `Currency`             | `Currency.NONE`  |
| `aliases`     | `dict[SourceId, str]`  | `{}`             |
| `country`     | `str or None`          | `None`           |
| `exchange`    | `str or None`          | `None`           |

```python
meta = InstrumentMeta(
    symbol="KRX:005930", name="Samsung Electronics",
    asset_class=AssetClass.EQUITY, currency=Currency.KRW,
    aliases={SourceId.FDR: "005930", SourceId.YFINANCE: "005930.KS"},
    country="KR", exchange="KRX",
)
meta.alias_for(SourceId.FDR)        # "005930"
meta.alias_for(SourceId.OECD)       # None
```

### Interfaces

`Protocol` classes (structural typing) — implement by shape, no subclassing
required.

```python
from rikschema import Source, Emitter

# Source:  source_id: SourceId; fetch(symbols, start, end); to_standard(raw)
# Emitter: emit(records) -> Any
isinstance(my_source, Source)       # True if it has the right shape
```

### Errors

```python
from rikschema import (
    RikError,                # base
    SchemaError,
    SourceError,             # has .source_id
    FetchError,              # SourceError subclass (network/API/rate-limit)
    NormalizationError,      # has .field
    SymbolResolutionError,   # NormalizationError subclass
    ValidationFailure,
)
```

---

## rikcore API

```python
import rikcore
rikcore.__version__   # "0.1.0"
```

### SymbolResolver

Bidirectional canonical/native map, built from `InstrumentMeta`.

```python
from rikcore import SymbolResolver

resolver = SymbolResolver(universe)          # iterable of InstrumentMeta
resolver.register(more_meta)                 # add one later

resolver.to_native("KRX:005930", SourceId.FDR)        # "005930"
resolver.to_canonical("005930.KS", SourceId.YFINANCE) # "KRX:005930"
resolver.meta("KRX:005930")                  # the InstrumentMeta
resolver.known_symbols()                     # ["KRX:005930", "INDEX:SPX", ...]
resolver.filter_supported(syms, SourceId.FDR)   # subset FDR can serve
```

Unknown symbol or missing alias raises `SymbolResolutionError`.

### Source adapters

All adapters take a `resolver` and satisfy the `Source` protocol. They
lazy-import their data library, so importing the adapter never requires the
library to be installed.

```python
from rikcore import YFinanceSource, FDRSource, ManualSource

yf  = YFinanceSource(resolver)   # SourceId.YFINANCE; needs `yfinance`
fdr = FDRSource(resolver)        # SourceId.FDR;      needs `finance-datareader`
```

- **`YFinanceSource`** — global equities, indices, ETFs. Asset class / currency
  inferred from the canonical prefix (`INDEX:` -> index/NONE, `ETF:` -> etf,
  `KRX:` -> KRW, else USD). Handles yfinance's MultiIndex columns automatically.
- **`FDRSource`** — KR equities, indices, ETFs via FinanceDataReader (no
  credentials). `INDEX:` -> unit-less, otherwise KRW.

**`ManualSource`** — network-free, for tests/fixtures/overrides. Takes in-memory
rows (`ManualRow` dicts):

```python
from datetime import date
from rikcore import ManualSource

rows = [{
    "symbol": "KRX:005930", "day": date(2026, 6, 4),
    "open": 349000.0, "high": 366000.0, "low": 348000.0, "close": 351500.0,
    "volume": 34_771_037.0, "currency": Currency.KRW,
    "asset_class": AssetClass.EQUITY,
}]
src = ManualSource(resolver, rows)

raw = src.fetch(["KRX:005930"], date(2026, 6, 1), date(2026, 6, 30))
records = src.to_standard(raw)    # list[OHLCVRecord]
```

### SourceRegistry

```python
from rikcore import SourceRegistry

registry = SourceRegistry()
registry.register(YFinanceSource(resolver))
registry.register(FDRSource(resolver))

registry.get(SourceId.FDR)        # the adapter
registry.all()                    # [adapter, ...]
SourceId.FDR in registry          # True
```

### Orchestrator

Runs fetch -> normalize -> validate -> emit and merges across sources. Each
source is only asked for symbols it can serve.

```python
from rikcore import Orchestrator

orch = Orchestrator(registry, emitter=None, strict=False)
# emitter defaults to RecordsEmitter()
# strict=True -> raise ValidationFailure if the batch doesn't validate

result = orch.run(
    symbols=resolver.known_symbols(),
    start=date(2026, 6, 1),
    end=date(2026, 6, 13),
    sources=None,                 # None = all registered; or [SourceId.FDR]
)

result.records      # list[StandardRecord] merged from all sources
result.report       # ValidationReport
result.output       # whatever the emitter returned
```

### Emitters

All satisfy the `Emitter` protocol (`emit(records) -> Any`).

```python
from rikcore import RecordsEmitter, DictEmitter, DataFrameEmitter

RecordsEmitter().emit(records)    # the records unchanged
DictEmitter().emit(records)       # list[dict] (JSON-ready)
DataFrameEmitter().emit(records)  # pandas DataFrame, sorted by symbol+timestamp
```

Pass one to the orchestrator: `Orchestrator(registry, DataFrameEmitter())`.

### Validation

```python
from rikcore import validate_batch

report = validate_batch(records)
report.ok           # bool — True if no duplicates / issues
report.total        # record count
report.duplicates   # list[(symbol, timestamp_iso)]
report.summary()    # "[OK] 18 records, 0 duplicate(s), 0 issue(s)"
```

Per-record invariants are already enforced by the models; `validate_batch`
checks cross-record properties (duplicate `(symbol, timestamp, source)` keys).

### Normalization helpers

```python
from rikcore.normalize import (
    SymbolResolver, FieldMapper,
    to_kst_midnight, is_weekday, daterange, convert_ohlcv_currency,
)

to_kst_midnight(date(2026, 6, 4))         # KST-aware datetime at 00:00
is_weekday(date(2026, 6, 6))              # False (Saturday)
list(daterange(date(2026,6,1), date(2026,6,5)))   # 5 inclusive dates

# Explicit, opt-in currency conversion (returns a NEW frozen record):
usd_rec = convert_ohlcv_currency(krw_rec, rate=1/1350, target=Currency.USD)

# FieldMapper renames source columns to standard fields:
m = FieldMapper({"Open": "open", "Close": "close"})
m.apply({"Open": 100, "Close": 105})      # {"open": 100, "close": 105}
m.missing({"Open": 100})                  # ["Close"]
```

### Config

`defaults.yaml` is the canonical config; override by passing a path.

```python
from rikcore.config import load_config

cfg = load_config()               # packaged defaults
cfg = load_config("my.yaml")      # your overrides
# cfg["pipeline"]["strict"], cfg["sources"]["fdr"]["enabled"], ...
```

---

## rikfeed API

```python
import rikfeed
rikfeed.__version__   # "0.1.0"
```

### SQLiteStore

WAL-mode SQLite persistence for OHLCV records. Upserts on
`(symbol, timestamp, source)`, so re-running a feed never duplicates.

```python
from rikfeed import SQLiteStore

store = SQLiteStore("rikfeed.db")
n = store.write(records)          # int rows written (non-OHLCV ignored)
store.count()                     # total rows in the ohlcv table
store.close()

# context manager form:
with SQLiteStore("rikfeed.db") as store:
    store.write(records)
```

Read it back with plain SQL / pandas:

```python
import sqlite3, pandas as pd
con = sqlite3.connect("rikfeed.db")
df = pd.read_sql_query("SELECT * FROM ohlcv ORDER BY symbol, timestamp", con)
con.close()

# wide close-price panel for cross-sectional analysis:
panel = df.pivot_table(index="timestamp", columns="symbol", values="close")
```

### StoreEmitter

Adapts a store to the `Emitter` protocol so the orchestrator writes straight
into it.

```python
from rikfeed.storage import StoreEmitter

orch = Orchestrator(registry, StoreEmitter(store))
result = orch.run(symbols, start, end)
result.output                     # rows written (StoreEmitter.emit returns int)
```

### Scheduler

Computes the next KRX-close-plus-margin run slot, skipping weekends.

```python
from datetime import datetime
from zoneinfo import ZoneInfo
from rikfeed import next_run_after
from rikfeed.schedule import KRX_CLOSE   # time(15, 30)

now = datetime.now(ZoneInfo("Asia/Seoul"))
next_run_after(now)                                   # default 30-min margin
next_run_after(now, margin_minutes=15)                # custom margin
```

Colab can't host a long-lived scheduler; use this to decide whether a run is
due, or wire it into cron / a GitHub Action.

---

## Writing a new source adapter

Implement two methods. Inheriting `SourceAdapter` is optional but gives you the
`resolver` and lets the orchestrator route symbols to you.

```python
from datetime import date
from typing import Any
from rikschema import OHLCVRecord, SourceId, AssetClass, Currency, StandardRecord
from rikcore.normalize import to_kst_midnight
from rikcore.sources.base import SourceAdapter

class MySource(SourceAdapter):
    source_id = SourceId.OECD          # pick/extend the SourceId enum

    def fetch(self, symbols: list[str], start: date, end: date) -> Any:
        rows = []
        for canonical in symbols:
            native = self.resolver.to_native(canonical, self.source_id)
            # ... call your API with `native` ...
            rows.append({"symbol": canonical, "raw": ...})
        return rows

    def to_standard(self, raw: Any) -> list[StandardRecord]:
        out = []
        for item in raw:
            out.append(OHLCVRecord(
                symbol=item["symbol"],
                timestamp=to_kst_midnight(item["raw"]["day"]),
                source=self.source_id,
                asset_class=AssetClass.EQUITY,
                open=..., high=..., low=..., close=...,
                currency=Currency.KRW,
            ))
        return out

registry.register(MySource(resolver))
```

Keep `fetch` for I/O and `to_standard` pure (no network) so the transform is
testable with recorded fixtures.

---

## Repository layout

```
rik/
├── pyproject.toml          # uv workspace root
├── packages/
│   ├── rikschema/          # contract (pydantic only)
│   │   └── src/rikschema/{records,enums,interfaces}/
│   ├── rikcore/            # producer
│   │   └── src/rikcore/{sources,normalize,validate,pipeline,emit,config,utils}/
│   └── rikfeed/            # consumer
│       └── src/rikfeed/{storage,schedule}/
├── examples/rik_feed.ipynb # end-to-end Colab notebook
├── scripts/dev_setup.py    # pip-based editable install fallback
└── .github/workflows/ci.yml
```

---

## Versioning

`rikschema` follows SemVer strictly: adding a record field is **minor**,
removing a field or changing a type is **major**. rikcore/rikfeed may move
faster. When installing single packages from GitHub, pin a per-package tag
(`@rikschema-v0.1.0`) for reproducibility.

## License

MIT — see [LICENSE](LICENSE).