"""Tests for measurement metadata storage."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.storage.database import find_measurement_by_hash, get_measurement, initialize_database, insert_measurement, list_measurements


class MeasurementDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:  # Prepare database path and metadata
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = Path(temporary.name) / "local" / "measurements.db"
        self.record = {
            "measurement_id": "measurement-1",
            "original_name": "original.bin",
            "stored_path": "data/raw/measurement-1/original.bin",
            "file_size": 12,
            "file_hash": "abc123",
            "ingested_at": "2026-10-01T12:30:00+00:00",
            "status": "ingested",
        }

    def test_initialization_creates_database_and_preserves_records(self) -> None:  # Verify database creation preserves records
        initialize_database(self.database)
        self.assertTrue(self.database.is_file())
        insert_measurement(self.record, self.database)
        initialize_database(self.database)
        self.assertEqual(get_measurement("measurement-1", self.database), self.record)

    def test_find_and_list_return_dictionaries(self) -> None:  # Verify queries return metadata dictionaries
        insert_measurement(self.record, self.database)
        self.assertEqual(find_measurement_by_hash("abc123", self.database), self.record)
        self.assertEqual(list_measurements(self.database), [self.record])

    def test_missing_records_and_empty_database(self) -> None:  # Verify missing records return nothing
        self.assertIsNone(get_measurement("missing", self.database))
        self.assertIsNone(find_measurement_by_hash("missing", self.database))
        self.assertEqual(list_measurements(self.database), [])

    def test_duplicate_id_and_hash_do_not_change_records(self) -> None:  # Verify duplicates preserve stored records
        insert_measurement(self.record, self.database)
        duplicates = [dict(self.record, file_hash="different"), dict(self.record, measurement_id="different")]
        for record in duplicates:
            with self.assertRaises(sqlite3.IntegrityError):
                insert_measurement(record, self.database)
        self.assertEqual(list_measurements(self.database), [self.record])
        insert_measurement(dict(self.record, measurement_id="measurement-2", file_hash="new"), self.database)
        self.assertEqual(len(list_measurements(self.database)), 2)

    def test_queries_treat_sql_as_text(self) -> None:  # Verify queries treat SQL literally
        record = dict(self.record, measurement_id="' OR 1=1 --", file_hash="'; DROP TABLE measurements; --")
        insert_measurement(record, self.database)
        self.assertEqual(get_measurement(record["measurement_id"], self.database), record)
        self.assertEqual(find_measurement_by_hash(record["file_hash"], self.database), record)
        self.assertIsNone(get_measurement("' OR 1=1 -- other", self.database))

    def test_timestamp_is_normalized_without_changing_input(self) -> None:  # Verify timestamps normalize without mutation
        record = dict(self.record, ingested_at="2026-10-01 12:30:00+00:00")
        insert_measurement(record, self.database)
        self.assertEqual(get_measurement("measurement-1", self.database)["ingested_at"], self.record["ingested_at"])
        self.assertEqual(record["ingested_at"], "2026-10-01 12:30:00+00:00")

    def test_invalid_timestamp_is_rejected(self) -> None:  # Verify invalid timestamps are rejected
        with self.assertRaises(ValueError):
            insert_measurement(dict(self.record, ingested_at="invalid"), self.database)
        self.assertEqual(list_measurements(self.database), [])


if __name__ == "__main__":
    unittest.main()
