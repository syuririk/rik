# rikschema

The data & behavior contract for the rik ecosystem. Pure package: depends only
on pydantic.

- **records/** — `StandardRecord` base + `OHLCVRecord`, `FundamentalRecord`,
  `MacroRecord`, `InstrumentMeta`.
- **enums/** — `AssetClass`, `Currency`, `SourceId`.
- **interfaces/** — `Source` and `Emitter` Protocols.
- **errors.py** — shared exception hierarchy.

rikcore implements these interfaces; rikfeed consumes records. Neither is
imported here.
