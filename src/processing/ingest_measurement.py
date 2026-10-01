"""Coordinate saving an original file and its metadata."""

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from src.io.ingestion import calculate_file_hash, inspect_file
from src.observability.logging_config import log_event
from src.storage.database import find_measurement_by_hash, insert_measurement
from src.storage.files import save_original_file


def ingest_measurement(source_path: str | Path) -> dict[str, str | int]:  # Save measurement and handle duplicates
    """Save a new measurement and return its metadata with status 'ingested'.

    Return status 'duplicate' with the existing metadata for a known hash.
    Copy or insertion errors return status 'failed', the stage, error, and
    measurement ID. Include stored_path when copying succeeded.
    Inspection, hashing, and duplicate lookup errors raise exceptions.
    Logging errors raise after success, or accompany an ingestion failure.
    """
    run_id = str(uuid4())
    started = perf_counter()
    stage = "inspect"
    measurement_id = None
    saved_path = None
    record = {}
    try:
        file_info = inspect_file(source_path)
        stage = "hash"
        file_hash = calculate_file_hash(source_path)
        stage = "duplicate_lookup"
        existing = find_measurement_by_hash(file_hash)
        if existing is None:
            measurement_id = str(uuid4())
            stage = "copy"
            saved_path = save_original_file(source_path, measurement_id)
            stage = "insert"
            record = {
                "measurement_id": measurement_id,
                "original_name": file_info["original_name"],
                "stored_path": str(saved_path),
                "file_size": file_info["size"],
                "file_hash": file_hash,
                "ingested_at": datetime.now(timezone.utc).isoformat(),
                "status": "ingested",
            }
            insert_measurement(record)
    except Exception as exc:
        logging_error = None
        try:
            event = "ingestion_partial_failure" if saved_path is not None else "ingestion_failed"
            log_event(event, "ERROR", stage, measurement_id, error=str(exc), error_type=type(exc).__name__, stored_path=str(saved_path) if saved_path is not None else None, run_id=run_id, elapsed_seconds=perf_counter() - started)
        except Exception as log_error:
            # Keep the ingestion error when recording it also fails.
            logging_error = f"{type(log_error).__name__}: {log_error}"
            exc.add_note(f"Logging also failed: {logging_error}")

        if (stage == "copy" and isinstance(exc, OSError)) or (stage == "insert" and isinstance(exc, (sqlite3.Error, OSError))):
            result = {**record, "status": "failed", "stage": stage, "measurement_id": measurement_id, "error": str(exc)}
            if logging_error is not None:
                result["logging_error"] = logging_error
            return result
        if measurement_id is not None:
            exc.add_note(f"Measurement ID: {measurement_id}; saved path: {saved_path}")
        raise

    # Record success only after the database commit has completed.
    try:
        if existing is not None:
            log_event("measurement_duplicate", "WARNING", "duplicate_lookup", existing["measurement_id"], stored_path=existing["stored_path"], run_id=run_id, elapsed_seconds=perf_counter() - started)
            return {**existing, "status": "duplicate"}
        log_event("measurement_ingested", "INFO", "complete", measurement_id, stored_path=str(saved_path), run_id=run_id, elapsed_seconds=perf_counter() - started)
    except Exception as exc:
        context = existing if existing is not None else record
        exc.add_note(f"Logging failed after ingestion result: {context['measurement_id']}; saved path: {context['stored_path']}")
        raise

    return record
