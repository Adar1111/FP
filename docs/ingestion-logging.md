# Ingestion event logs

Ingestion appends UTF-8 JSON lines to `results/logs/ingestion.jsonl` under the
project root. Logging starts on the first event, not during module import.
To choose another file, call `configure_logging(log_path)` from
`src.observability.logging_config` before ingestion. Repeated calls with the
same path reuse the handler. Selecting another path closes the previous handler.

Each event includes a UTC ISO 8601 timestamp, event name, level, stage,
measurement ID (null before assignment), run ID, and elapsed seconds.
Errors include their type and message. Saved paths appear when available.
Logs contain metadata and error details, not file contents or entire records.

| Event | Level | Meaning |
| --- | --- | --- |
| `measurement_ingested` | INFO | The database record was saved successfully. |
| `measurement_duplicate` | WARNING | The hash already exists; no copy or insert occurred. |
| `ingestion_failed` | ERROR | A stage failed before a copy completed. |
| `ingestion_partial_failure` | ERROR | Copying completed but a later step failed. |

Stages are `inspect`, `hash`, `duplicate_lookup`, `copy`, `insert`, and `complete`.
The public `ingest_measurement(source_path)` interface and ordinary results stay
the same. Inspection, hashing, and lookup exceptions still propagate.

Logging failures are never discarded. If ingestion already raised an error,
that same error is raised with a note about the logging failure. If ingestion
returns a failure result, it includes `logging_error` alongside the original
error, measurement ID, and saved path when available. A logging failure after
a successful commit raises the logging error with the saved ID and path in a
note; it does not undo the saved measurement.

Verification uses temporary files and databases to check JSON formatting,
append behavior, handler reuse, import behavior, stage events, and combined
ingestion and logging failures.
