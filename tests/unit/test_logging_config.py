"""Test JSON logs with temporary files."""

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from src.observability.logging_config import configure_logging, log_event


class LoggingConfigTests(unittest.TestCase):
    def setUp(self) -> None:  # Prepare temporary log for tests
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "logs" / "ingestion.jsonl"
        self.logger = configure_logging(self.path)
        self.addCleanup(self.close_logger)

    def close_logger(self) -> None:  # Close and remove log handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            handler.close()

    def test_json_fields_utf8_and_newlines(self) -> None:  # Verify JSON fields and encoding
        log_event("ingestion_failed", "ERROR", "copy", "measurement-1", error="échec\nsecond line", stored_path="saved.bin")
        lines = self.path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        event = json.loads(lines[0])
        self.assertEqual(event["event"], "ingestion_failed")
        self.assertEqual(event["level"], "ERROR")
        self.assertEqual(event["stage"], "copy")
        self.assertEqual(event["measurement_id"], "measurement-1")
        self.assertEqual(event["error"], "échec\nsecond line")
        self.assertEqual(datetime.fromisoformat(event["timestamp"]).tzinfo, timezone.utc)

    def test_append_and_repeated_configuration(self) -> None:  # Verify appending and handler reuse
        log_event("first", "INFO", "complete")
        previous = self.path.read_bytes()
        for _ in range(3):
            self.assertIs(configure_logging(self.path), self.logger)
        log_event("second", "WARNING", "duplicate_lookup")
        self.assertTrue(self.path.read_bytes().startswith(previous))
        self.assertEqual(len(self.logger.handlers), 1)
        events = [json.loads(line) for line in self.path.read_text().splitlines()]
        self.assertEqual([event["event"] for event in events], ["first", "second"])

    def test_switching_paths_closes_previous_handler(self) -> None:  # Verify switching logs closes handler
        log_event("first", "INFO", "complete")
        previous = self.logger.handlers[0]
        other = self.path.parent / "other.jsonl"
        configure_logging(other)
        log_event("second", "INFO", "complete")
        self.assertIsNone(previous.stream)
        self.assertEqual(len(self.path.read_text().splitlines()), 1)
        self.assertEqual(json.loads(other.read_text())["event"], "second")

    def test_write_errors_raise_instead_of_being_swallowed(self) -> None:  # Verify log write errors propagate
        handler = self.logger.handlers[0]
        with patch.object(handler.stream, "write", side_effect=OSError("disk full")):
            with self.assertRaisesRegex(OSError, "disk full"):
                log_event("first", "INFO", "complete")

    def test_configuration_errors_raise(self) -> None:  # Verify logging configuration errors propagate
        with patch("pathlib.Path.mkdir", side_effect=PermissionError("permission denied")):
            with self.assertRaises(PermissionError):
                configure_logging(self.path.parent / "other.jsonl")

    def test_import_does_not_configure_logging_or_create_files(self) -> None:  # Verify imports leave logging unconfigured
        code = """
import logging
from unittest.mock import patch

with patch('pathlib.Path.mkdir') as mkdir:
    with patch('logging.FileHandler.__init__') as open_log:
        import src.observability.logging_config
        import src.processing.ingest_measurement
        mkdir.assert_not_called()
        open_log.assert_not_called()
        assert not logging.getLogger('ofdr.ingestion').handlers
"""
        result = subprocess.run([sys.executable, "-c", code], cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
