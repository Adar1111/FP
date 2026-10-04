"""Test ingestion using real files and a temporary SQLite database."""

import hashlib
import json
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

# Direct execution puts tests/integration on sys.path instead of the project root.
if __name__ == "__main__" and not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.processing.ingest_measurement import ingest_measurement
from src.observability.logging_config import configure_logging
from src.storage import database


class IngestMeasurementTests(unittest.TestCase):
    def setUp(self) -> None:  # Prepare temporary ingestion test environment
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.log_path = self.root / "logs" / "ingestion.jsonl"
        self.raw = self.root / "data" / "raw"
        self.database = self.root / "data" / "local" / "measurements.db"
        self.source = self.root / "original.bin"
        self.source.write_bytes(b"\x00measurement\xff")
        patches = [
            patch("src.observability.logging_config._LOGGER_NAME", f"ofdr.ingestion.test.{uuid4()}"),
            patch("src.storage.files._RAW_DIRECTORY", self.raw),
            patch("src.processing.ingest_measurement.find_measurement_by_hash", side_effect=lambda value: database.find_measurement_by_hash(value, self.database)),
            patch("src.processing.ingest_measurement.insert_measurement", side_effect=lambda record: database.insert_measurement(record, self.database)),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.logger = configure_logging(self.log_path)
        self.addCleanup(self.close_logger)

    def close_logger(self) -> None:
        """Close log files before temporary-directory cleanup on Windows."""
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            handler.close()

    def read_events(self) -> list[dict]:
        """Read the real JSON events produced by this test's ingestion calls."""
        return [json.loads(line) for line in self.log_path.read_text(encoding="utf-8").splitlines()]

    def test_success_saves_file_and_metadata(self) -> None:  # Verify file and metadata storage
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
        events = self.read_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "measurement_ingested")
        self.assertEqual(events[0]["measurement_id"], result["measurement_id"])
        self.assertTrue(events[0]["run_id"])
        self.assertGreaterEqual(events[0]["elapsed_seconds"], 0)

    def test_duplicate_does_not_copy_or_insert(self) -> None:  # Verify duplicates prevent repeated storage
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
        events = self.read_events()
        self.assertEqual([event["event"] for event in events], ["measurement_ingested", "measurement_duplicate"])
        self.assertNotEqual(events[0]["run_id"], events[1]["run_id"])

    def test_insertion_failure_keeps_saved_path_and_id(self) -> None:  # Verify insertion failure retains metadata
        with patch("src.processing.ingest_measurement.insert_measurement", side_effect=sqlite3.OperationalError("database is locked")):
            result = ingest_measurement(self.source)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["stage"], "insert")
        self.assertIn("database is locked", result["error"])
        self.assertEqual(Path(result["stored_path"]).parent.name, result["measurement_id"])
        self.assertEqual(Path(result["stored_path"]).read_bytes(), self.source.read_bytes())
        self.assertEqual(database.list_measurements(self.database), [])
        event = self.read_events()[0]
        self.assertEqual(event["event"], "ingestion_partial_failure")
        self.assertEqual(event["stage"], "insert")
        self.assertEqual(event["stored_path"], result["stored_path"])

    def test_copy_failure_does_not_insert(self) -> None:  # Verify copy failure prevents insertion
        with patch("src.processing.ingest_measurement.save_original_file", side_effect=OSError("disk full")):
            with patch("src.processing.ingest_measurement.insert_measurement") as insert:
                result = ingest_measurement(self.source)
        insert.assert_not_called()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["stage"], "copy")
        self.assertTrue(result["measurement_id"])
        self.assertEqual(result["error"], "disk full")
        event = self.read_events()[0]
        self.assertEqual(event["event"], "ingestion_failed")
        self.assertEqual(event["stage"], "copy")
        self.assertEqual(event["error"], "disk full")

    def test_invalid_source_fails_before_database_or_copy(self) -> None:  # Verify invalid sources prevent ingestion
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
