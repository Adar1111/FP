"""Test ingestion using real files and a temporary SQLite database."""

import hashlib
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from src.processing.ingest_measurement import ingest_measurement
from src.storage import database


class IngestMeasurementTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.raw = self.root / "data" / "raw"
        self.database = self.root / "data" / "local" / "measurements.db"
        self.source = self.root / "original.bin"
        self.source.write_bytes(b"\x00measurement\xff")
        patches = [
            patch("src.storage.files._RAW_DIRECTORY", self.raw),
            patch("src.processing.ingest_measurement.find_measurement_by_hash", side_effect=lambda value: database.find_measurement_by_hash(value, self.database)),
            patch("src.processing.ingest_measurement.insert_measurement", side_effect=lambda record: database.insert_measurement(record, self.database)),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_success_saves_file_and_metadata(self) -> None:
        before = self.source.stat()
        result = ingest_measurement(self.source)
        self.assertEqual(result["status"], "ingested")
        self.assertEqual(result["original_name"], self.source.name)
        self.assertEqual(result["file_size"], before.st_size)
        self.assertEqual(result["file_hash"], hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertEqual(Path(result["stored_path"]), self.raw / result["measurement_id"] / self.source.name)
        self.assertEqual(Path(result["stored_path"]).read_bytes(), b"\x00measurement\xff")
        self.assertEqual(self.source.read_bytes(), b"\x00measurement\xff")
        self.assertEqual(self.source.stat().st_mtime_ns, before.st_mtime_ns)
        self.assertEqual(datetime.fromisoformat(result["ingested_at"]).tzinfo, timezone.utc)
        self.assertEqual(database.get_measurement(result["measurement_id"], self.database), result)

    def test_duplicate_does_not_copy_or_insert(self) -> None:
        original = ingest_measurement(self.source)
        renamed = self.root / "renamed.bin"
        renamed.write_bytes(self.source.read_bytes())
        with patch("src.processing.ingest_measurement.save_original_file") as copy:
            with patch("src.processing.ingest_measurement.insert_measurement") as insert:
                result = ingest_measurement(renamed)
        copy.assert_not_called()
        insert.assert_not_called()
        self.assertEqual(result["status"], "duplicate")
        self.assertEqual(result["measurement_id"], original["measurement_id"])
        self.assertEqual(database.list_measurements(self.database), [original])

    def test_insertion_failure_keeps_saved_path_and_id(self) -> None:
        with patch("src.processing.ingest_measurement.insert_measurement", side_effect=sqlite3.OperationalError("database is locked")):
            result = ingest_measurement(self.source)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["stage"], "insert")
        self.assertIn("database is locked", result["error"])
        self.assertEqual(Path(result["stored_path"]).parent.name, result["measurement_id"])
        self.assertEqual(Path(result["stored_path"]).read_bytes(), self.source.read_bytes())
        self.assertEqual(database.list_measurements(self.database), [])

    def test_copy_failure_does_not_insert(self) -> None:
        with patch("src.processing.ingest_measurement.save_original_file", side_effect=OSError("disk full")):
            with patch("src.processing.ingest_measurement.insert_measurement") as insert:
                result = ingest_measurement(self.source)
        insert.assert_not_called()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["stage"], "copy")
        self.assertTrue(result["measurement_id"])
        self.assertEqual(result["error"], "disk full")

    def test_invalid_source_fails_before_database_or_copy(self) -> None:
        for source, error in [(self.root / "missing", FileNotFoundError), (self.root, IsADirectoryError)]:
            with self.subTest(source=source):
                with self.assertRaises(error):
                    ingest_measurement(source)
        empty = self.root / "empty.bin"
        empty.touch()
        with self.assertRaises(ValueError):
            ingest_measurement(empty)
        self.assertFalse(self.database.exists())
        self.assertFalse(self.raw.exists())


if __name__ == "__main__":
    unittest.main()
