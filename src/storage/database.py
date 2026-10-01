"""Store and read measurement metadata in SQLite."""

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path


DEFAULT_DATABASE_PATH = Path(__file__).resolve().parents[2] / "data" / "local" / "measurements.db"


def initialize_database(database_path: str | Path = DEFAULT_DATABASE_PATH) -> None:  # Create database and measurement table
    """Create the database and table if needed. Keep existing records."""
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(path)) as connection:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS measurements (
                    measurement_id TEXT PRIMARY KEY NOT NULL,
                    original_name TEXT NOT NULL,
                    stored_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_hash TEXT NOT NULL UNIQUE,
                    ingested_at TEXT NOT NULL,
                    status TEXT NOT NULL
                )
            """)


def _connect(database_path: str | Path) -> sqlite3.Connection:  # Open database with named rows
    """Open the database and read rows by field name."""
    initialize_database(database_path)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def insert_measurement(record: dict[str, str | int], database_path: str | Path = DEFAULT_DATABASE_PATH) -> None:  # Store measurement metadata
    """Insert metadata. Duplicate IDs or hashes raise sqlite3.IntegrityError.

    Supply all seven fields, with ingested_at as an ISO 8601 string.
    Invalid timestamps raise ValueError. Existing records stay unchanged.
    """
    values = dict(record)
    values["ingested_at"] = datetime.fromisoformat(values["ingested_at"]).isoformat()

    # "with closing" closes the connection when this block ends, even after an error.
    with closing(_connect(database_path)) as connection:
        # Commit on success and roll back on failure.
        with connection:
            connection.execute("""
                INSERT INTO measurements (measurement_id, original_name, stored_path, file_size, file_hash, ingested_at, status)
                VALUES (:measurement_id, :original_name, :stored_path, :file_size, :file_hash, :ingested_at, :status)
            """, values)


def get_measurement(measurement_id: str, database_path: str | Path = DEFAULT_DATABASE_PATH) -> dict[str, str | int] | None:  # Find measurement by ID
    """Return the measurement dictionary, or None if it is missing."""
    with closing(_connect(database_path)) as connection:
        row = connection.execute("SELECT * FROM measurements WHERE measurement_id = ?", (measurement_id,)).fetchone()
        return dict(row) if row is not None else None


def find_measurement_by_hash(file_hash: str, database_path: str | Path = DEFAULT_DATABASE_PATH) -> dict[str, str | int] | None:  # Find measurement by file hash
    """Return the matching measurement dictionary, or None."""
    with closing(_connect(database_path)) as connection:
        row = connection.execute("SELECT * FROM measurements WHERE file_hash = ?", (file_hash,)).fetchone()
        return dict(row) if row is not None else None


def list_measurements(database_path: str | Path = DEFAULT_DATABASE_PATH) -> list[dict[str, str | int]]:  # List measurements ordered by ID
    """Return all measurements as dictionaries, ordered by measurement ID."""
    with closing(_connect(database_path)) as connection:
        rows = connection.execute("SELECT * FROM measurements ORDER BY measurement_id").fetchall()
        return [dict(row) for row in rows]
