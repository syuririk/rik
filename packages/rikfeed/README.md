# rikfeed

Consumer side of the rik ecosystem. Persists standard records and schedules
collection runs.

- **storage/** — `SQLiteStore` (WAL mode) + `StoreEmitter` (a rikschema Emitter,
  so the orchestrator can write straight to the feed).
- **schedule/** — `next_run_after`, computing the post-KRX-close run slot.
