<<<<<<< HEAD
# rik

Standardized multi-source market-data pipeline, organized as a uv workspace
monorepo.

```
data sources ──▶ rikcore ──▶ [standard records] ──▶ rikfeed ──▶ storage
  (yfinance,      (fetch +      (rikschema           (persist +
   pykrx, ...)     normalize)    contract)            schedule)
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

## Design

- **One canonical symbol, many source aliases.** `rikcore.SymbolResolver`
  maps e.g. `005930.KS` (yfinance) and `005930` (pykrx) to one canonical
  `KRX:005930`, which is how records from different sources merge.
- **Records are immutable and strict.** Every `StandardRecord` is frozen,
  forbids extra fields, and forces tz-aware KST timestamps at construction.
- **Native values, explicit transforms.** Prices stay in their source
  currency; any FX/scale conversion is an opt-in pipeline step.
- **fetch / to_standard split.** Source adapters separate I/O (`fetch`) from
  the pure transform (`to_standard`), so normalization is unit-testable with
  fixtures and no network.

## Quick start (local dev)

```bash
uv sync                 # installs all three packages editable + dev tools
uv run pytest           # runs the whole suite
```

Without uv:

```bash
python scripts/dev_setup.py
```

## Single-package install (e.g. Colab)

Workspace resolution only applies locally. To install one package from GitHub,
use a per-package tag + subdirectory, and install rikschema alongside it:

```bash
pip install "git+https://github.com/syuririk/rik.git@rikschema-v0.1.0#subdirectory=packages/rikschema"
pip install "git+https://github.com/syuririk/rik.git@rikcore-v0.1.0#subdirectory=packages/rikcore"
```

## Versioning

`rikschema` follows SemVer strictly: adding a record field is **minor**,
removing a field or changing a type is **major**. rikcore/rikfeed are free to
move faster.

## Repository layout

```
rik/
├── pyproject.toml          # uv workspace root
├── packages/
│   ├── rikschema/          # contract (pydantic only)
│   ├── rikcore/            # producer
│   └── rikfeed/            # consumer
├── scripts/dev_setup.py    # pip-based editable install fallback
└── .github/workflows/ci.yml
```

## License

MIT — see [LICENSE](LICENSE).
=======
# rik
>>>>>>> 6a747916a2abbcd97e37162a146ee8e444f15d6a
